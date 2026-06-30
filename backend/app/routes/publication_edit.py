"""
Publication Edit Routes — per-entity CRUD endpoints for editing a DOCiD
without re-minting the top-level Cordra handle.

Security model:
- JWT-authenticated only (Flask-JWT-Extended). Caller identity comes from
  the signed token, NOT from any request body field. user_id in the body
  is ignored.
- Only the owner (publication.user_id == JWT identity) can edit.
- Top-level document_docid handle NEVER changes or re-mints.
- NEW files and documents mint their own Cordra child handles.
- All mutations logged to PublicationAuditTrail.

Upload constraints:
- Max 25 MB per file.
- Extension allowlist (no scripts/executables).
- Cordra handle is minted BEFORE the file is persisted, so a Cordra failure
  does not leave an orphan file on disk.
- DELETE removes the on-disk file if it lives under our uploads dir.
"""
import logging
import os
import re
import uuid
from urllib.parse import quote as url_quote, urlparse

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from app import db
from app.models import (
    Publications,
    PublicationCreators,
    PublicationOrganization,
    PublicationFunders,
    PublicationProjects,
    PublicationFiles,
    PublicationDocuments,
    PublicationAuditTrail,
    CreatorsRoles,
    FunderTypes,
)
from app.service_identifiers import IdentifierService

logger = logging.getLogger(__name__)

edit_bp = Blueprint('publication_edit', __name__, url_prefix='/api/v1/publications')

UPLOAD_DIR = 'uploads'
MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB

# Local copy of `app.routes.publications.coerce_real_doi` and its `_REAL_DOI_RE`
# regex, kept here to avoid a cross-blueprint import. Accepts a CrossRef /
# DataCite DOI (`10.xxxx/...`); strips a `https://doi.org/` /
# `http://dx.doi.org/` prefix; rejects DOCiD Handles (`20.500.14351/...`) and
# any other non-DOI string. Returns the bare-DOI form or None.
_REAL_DOI_RE = re.compile(r'^10\.\d+/.+')


def _coerce_real_doi(raw):
    if not raw or not isinstance(raw, str):
        return None
    stripped = raw.strip()
    if not stripped:
        return None
    bare = re.sub(r'^https?://(dx\.)?doi\.org/', '', stripped, flags=re.IGNORECASE)
    if _REAL_DOI_RE.match(bare):
        return bare
    return None

# Extensions we refuse outright (scripts, executables, web content that nginx might serve).
BLOCKED_EXTENSIONS = {
    '.exe', '.bat', '.cmd', '.com', '.sh', '.bash', '.ps1',
    '.php', '.php3', '.php4', '.php5', '.phtml',
    '.html', '.htm', '.shtml', '.xhtml',
    '.js', '.mjs', '.jsp', '.asp', '.aspx',
    '.py', '.rb', '.pl', '.cgi',
}


# ---------- helpers ----------

def _current_user_id():
    """Return the JWT identity as an int, or None."""
    try:
        identity = get_jwt_identity()
        return int(identity) if identity is not None else None
    except (ValueError, TypeError):
        return None


def _authorize(publication_id):
    """Return (publication, user_id, None) on success or (None, None, error_response) on failure."""
    user_id = _current_user_id()
    if user_id is None:
        return None, None, (jsonify({'error': 'Authentication required'}), 401)
    publication = Publications.query.filter_by(id=publication_id).first()
    if not publication:
        return None, user_id, (jsonify({'error': 'Publication not found'}), 404)
    if publication.user_id != user_id:
        return None, user_id, (jsonify({'error': 'Access denied: you do not own this publication'}), 403)
    return publication, user_id, None


def _audit(publication_id, user_id, action, field_name=None, old_value=None, new_value=None):
    """Write an audit trail row."""
    PublicationAuditTrail.log_change(
        publication_id=publication_id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None,
        ip_address=request.environ.get('HTTP_X_REAL_IP', request.remote_addr),
        user_agent=request.headers.get('User-Agent', ''),
    )


def _validate_upload(file_storage):
    """Return None if the upload is acceptable, or an error string."""
    if not file_storage or not file_storage.filename:
        return 'filename is empty'
    ext = os.path.splitext(file_storage.filename)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        return f'file type {ext} is not allowed'
    # Size: seek-based measurement. FileStorage wraps a SpooledTemporaryFile.
    try:
        file_storage.stream.seek(0, os.SEEK_END)
        size = file_storage.stream.tell()
        file_storage.stream.seek(0)
    except Exception:
        return None  # size unknown, let it through (rare)
    if size > MAX_UPLOAD_BYTES:
        return f'file too large ({size} bytes; max {MAX_UPLOAD_BYTES} bytes)'
    if size <= 0:
        return 'file is empty'
    return None


def _save_upload(file_storage):
    """Save an uploaded FileStorage to uploads/. UUID-prefixed to avoid collision.
    Returns (stored_name, public_url, absolute_local_path).
    """
    base_url = (os.environ.get('PUBLIC_BASE_URL') or os.environ.get('APPLICATION_BASE_URL') or '').rstrip('/')
    safe_name = secure_filename(file_storage.filename) or 'upload.bin'
    unique_name = f"{uuid.uuid4().hex[:12]}_{safe_name}"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    target_path = os.path.join(UPLOAD_DIR, unique_name)
    file_storage.save(target_path)
    public_url = f"{base_url}/{UPLOAD_DIR}/{url_quote(unique_name)}"
    return unique_name, public_url, os.path.abspath(target_path)


def _delete_local_file(file_url):
    """Best-effort removal of a locally-stored upload. Silently ignores paths outside uploads/."""
    if not file_url:
        return
    try:
        parsed = urlparse(file_url)
        url_path = parsed.path or file_url
        if '/uploads/' not in url_path:
            return
        relative = url_path.split('/uploads/', 1)[1]
        # guard against path traversal: reject anything with '..' segment
        if '..' in relative.split('/'):
            return
        abs_upload_dir = os.path.abspath(UPLOAD_DIR)
        candidate = os.path.abspath(os.path.join(UPLOAD_DIR, relative))
        if not candidate.startswith(abs_upload_dir + os.sep):
            return
        if os.path.isfile(candidate):
            os.remove(candidate)
            logger.info(f"Deleted local upload: {candidate}")
    except Exception as e:
        logger.warning(f"Failed to delete local file for url={file_url}: {e}")


# ---------- CREATORS ----------

@edit_bp.route('/<int:publication_id>/creators', methods=['POST'])
@jwt_required()
def add_creator(publication_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    family_name = (data.get('family_name') or '').strip()
    if not family_name:
        return jsonify({'error': 'family_name is required'}), 400

    role_id = data.get('role_id')
    if not role_id:
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        if not author_role:
            return jsonify({'error': 'role_id is required; default Author role not configured'}), 400
        role_id = author_role.role_id

    creator = PublicationCreators(
        publication_id=publication_id,
        family_name=family_name[:255],
        given_name=(data.get('given_name') or '')[:255],
        identifier=(data.get('identifier') or '')[:500],
        identifier_type=(data.get('identifier_type') or '')[:50],
        role_id=role_id,
        affiliation=(data.get('affiliation') or None),
    )
    db.session.add(creator)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_CREATOR',
           field_name='publication_creators',
           new_value=f"{creator.given_name} {creator.family_name}")
    db.session.commit()
    return jsonify({'message': 'Creator added', 'id': creator.id}), 201


@edit_bp.route('/<int:publication_id>/creators/<int:creator_id>', methods=['PUT'])
@jwt_required()
def update_creator(publication_id, creator_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    creator = PublicationCreators.query.filter_by(id=creator_id, publication_id=publication_id).first()
    if not creator:
        return jsonify({'error': 'Creator not found for this publication'}), 404

    data = request.get_json(silent=True) or {}
    changes = {}
    for field in ('family_name', 'given_name', 'identifier', 'identifier_type', 'affiliation', 'role_id'):
        if field in data:
            old = getattr(creator, field)
            new = data[field]
            if old != new:
                setattr(creator, field, new)
                changes[field] = (old, new)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_CREATOR',
                   field_name=f'creator.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Creator updated', 'id': creator.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/creators/<int:creator_id>', methods=['DELETE'])
@jwt_required()
def delete_creator(publication_id, creator_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    creator = PublicationCreators.query.filter_by(id=creator_id, publication_id=publication_id).first()
    if not creator:
        return jsonify({'error': 'Creator not found'}), 404

    label = f"{creator.given_name} {creator.family_name}"
    db.session.delete(creator)
    _audit(publication_id, user_id, 'DELETE_CREATOR',
           field_name='publication_creators', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Creator deleted'}), 200


# ---------- ORGANIZATIONS ----------

@edit_bp.route('/<int:publication_id>/organizations', methods=['POST'])
@jwt_required()
def add_organization(publication_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    org_type = (data.get('type') or '').strip()
    if not name or not org_type:
        return jsonify({'error': 'name and type are required'}), 400

    org = PublicationOrganization(
        publication_id=publication_id,
        name=name[:255],
        type=org_type[:255],
        other_name=(data.get('other_name') or None),
        country=(data.get('country') or None),
        identifier_type=(data.get('identifier_type') or None),
        identifier=(data.get('identifier') or None),
        rrid=(data.get('rrid') or None),
    )
    db.session.add(org)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_ORGANIZATION',
           field_name='publication_organizations', new_value=org.name)
    db.session.commit()
    return jsonify({'message': 'Organization added', 'id': org.id}), 201


@edit_bp.route('/<int:publication_id>/organizations/<int:org_id>', methods=['PUT'])
@jwt_required()
def update_organization(publication_id, org_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    org = PublicationOrganization.query.filter_by(id=org_id, publication_id=publication_id).first()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    data = request.get_json(silent=True) or {}
    changes = {}
    for field in ('name', 'type', 'other_name', 'country', 'identifier_type', 'identifier', 'rrid'):
        if field in data:
            old = getattr(org, field)
            new = data[field]
            if old != new:
                setattr(org, field, new)
                changes[field] = (old, new)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_ORGANIZATION',
                   field_name=f'organization.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Organization updated', 'id': org.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/organizations/<int:org_id>', methods=['DELETE'])
@jwt_required()
def delete_organization(publication_id, org_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    org = PublicationOrganization.query.filter_by(id=org_id, publication_id=publication_id).first()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    label = org.name
    db.session.delete(org)
    _audit(publication_id, user_id, 'DELETE_ORGANIZATION',
           field_name='publication_organizations', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Organization deleted'}), 200


# ---------- FUNDERS ----------

@edit_bp.route('/<int:publication_id>/funders', methods=['POST'])
@jwt_required()
def add_funder(publication_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    funder_type = (data.get('type') or '').strip()
    if not name or not funder_type:
        return jsonify({'error': 'name and type are required'}), 400

    funder_type_id = data.get('funder_type_id')
    try:
        funder_type_id = int(funder_type_id) if funder_type_id is not None else 1
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid funder_type_id'}), 400
    if not FunderTypes.query.filter_by(id=funder_type_id).first():
        return jsonify({'error': f'Unknown funder_type_id {funder_type_id}'}), 400

    funder = PublicationFunders(
        publication_id=publication_id,
        name=name[:255],
        type=funder_type[:255],
        funder_type_id=funder_type_id,
        other_name=(data.get('other_name') or None),
        country=(data.get('country') or None),
        identifier_type=(data.get('identifier_type') or None),
        identifier=(data.get('identifier') or None),
    )
    db.session.add(funder)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_FUNDER',
           field_name='publication_funders', new_value=funder.name)
    db.session.commit()
    return jsonify({'message': 'Funder added', 'id': funder.id}), 201


@edit_bp.route('/<int:publication_id>/funders/<int:funder_id>', methods=['PUT'])
@jwt_required()
def update_funder(publication_id, funder_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    funder = PublicationFunders.query.filter_by(id=funder_id, publication_id=publication_id).first()
    if not funder:
        return jsonify({'error': 'Funder not found'}), 404

    data = request.get_json(silent=True) or {}
    # Validate funder_type_id if provided
    if 'funder_type_id' in data:
        try:
            new_ft = int(data['funder_type_id'])
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid funder_type_id'}), 400
        if not FunderTypes.query.filter_by(id=new_ft).first():
            return jsonify({'error': f'Unknown funder_type_id {new_ft}'}), 400
        data['funder_type_id'] = new_ft

    changes = {}
    for field in ('name', 'type', 'funder_type_id', 'other_name', 'country', 'identifier_type', 'identifier'):
        if field in data:
            old = getattr(funder, field)
            new = data[field]
            if old != new:
                setattr(funder, field, new)
                changes[field] = (old, new)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_FUNDER',
                   field_name=f'funder.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Funder updated', 'id': funder.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/funders/<int:funder_id>', methods=['DELETE'])
@jwt_required()
def delete_funder(publication_id, funder_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    funder = PublicationFunders.query.filter_by(id=funder_id, publication_id=publication_id).first()
    if not funder:
        return jsonify({'error': 'Funder not found'}), 404

    label = funder.name
    db.session.delete(funder)
    _audit(publication_id, user_id, 'DELETE_FUNDER',
           field_name='publication_funders', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Funder deleted'}), 200


# ---------- PROJECTS ----------

@edit_bp.route('/<int:publication_id>/projects', methods=['POST'])
@jwt_required()
def add_project(publication_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'title is required'}), 400

    project = PublicationProjects(
        publication_id=publication_id,
        title=title[:255],
        description=(data.get('description') or ''),
        raid_id=(data.get('raid_id') or None),
        identifier=(data.get('identifier') or None),
        identifier_type=(data.get('identifier_type') or None),
    )
    db.session.add(project)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_PROJECT',
           field_name='publication_projects', new_value=project.title)
    db.session.commit()
    return jsonify({'message': 'Project added', 'id': project.id}), 201


@edit_bp.route('/<int:publication_id>/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(publication_id, project_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    project = PublicationProjects.query.filter_by(id=project_id, publication_id=publication_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json(silent=True) or {}
    changes = {}
    for field in ('title', 'description', 'raid_id', 'identifier', 'identifier_type'):
        if field in data:
            old = getattr(project, field)
            new = data[field]
            if old != new:
                setattr(project, field, new)
                changes[field] = (old, new)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_PROJECT',
                   field_name=f'project.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Project updated', 'id': project.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(publication_id, project_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    project = PublicationProjects.query.filter_by(id=project_id, publication_id=publication_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    label = project.title
    db.session.delete(project)
    _audit(publication_id, user_id, 'DELETE_PROJECT',
           field_name='publication_projects', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Project deleted'}), 200


# ---------- FILES (publications_files) ----------

@edit_bp.route('/<int:publication_id>/files', methods=['POST'])
@jwt_required()
def add_file(publication_id):
    """Upload a new file OR add external video URL + mint Cordra child handle."""
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err

    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    publication_type_id_raw = request.form.get('publication_type_id', '1')
    video_url_raw = (request.form.get('video_url') or '').strip()
    uploaded = request.files.get('file')

    # Optional external identifier (e.g. an existing CrossRef DOI the
    # researcher wants to record against this file). Stored as 'DOI' to match
    # the assign-docid flow — the UI labels the dropdown option "CrossRef".
    ext_id_type_raw = (request.form.get('external_identifier_type') or '').strip()
    ext_id_value_raw = (request.form.get('external_identifier_value') or '').strip()
    ext_identifier = None
    ext_identifier_type = None
    if ext_id_type_raw or ext_id_value_raw:
        if not ext_id_type_raw:
            return jsonify({
                'error': "external_identifier_type is required when "
                         "external_identifier_value is supplied."
            }), 400
        if ext_id_type_raw != 'DOI':
            return jsonify({
                'error': "external_identifier_type must be 'DOI' (the only external "
                         "identifier supported here today)."
            }), 400
        if not ext_id_value_raw:
            return jsonify({
                'error': "external_identifier_value is required when "
                         "external_identifier_type='DOI' is supplied."
            }), 400
        coerced = _coerce_real_doi(ext_id_value_raw)
        if coerced is None:
            return jsonify({
                'error': "Invalid DOI: must look like 10.xxxx/..."
            }), 400
        if len(coerced) > 100:
            return jsonify({
                'error': "DOI too long (max 100 characters after URL-prefix stripping)."
            }), 400
        ext_identifier = coerced
        ext_identifier_type = 'DOI'

    if not title:
        return jsonify({'error': 'title is required'}), 400

    try:
        publication_type_id = int(publication_type_id_raw)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid publication_type_id'}), 400

    # Branch: external video URL (no upload), OR file upload
    if video_url_raw:
        if not video_url_raw.startswith(('http://', 'https://')):
            video_url_raw = 'https://' + video_url_raw
        minted = IdentifierService.generate_handle()
        if not minted:
            return jsonify({'error': 'Cordra handle mint failed'}), 502

        pub_file = PublicationFiles(
            publication_id=publication_id,
            title=title[:255],
            description=description,
            publication_type_id=publication_type_id,
            file_name='',
            file_type='video/external',
            file_url=video_url_raw[:255],
            identifier='1',  # identifier-TYPE id (1=APA Handle iD); handle lives in handle_identifier
            generated_identifier=minted[:100],
            handle_identifier=minted[:100],
            external_identifier=ext_identifier,
            external_identifier_type=ext_identifier_type,
        )
        db.session.add(pub_file)
        db.session.flush()
        audit_label = f"{title} (video) ({minted})"
        if ext_identifier:
            audit_label += f" doi={ext_identifier}"
        _audit(publication_id, user_id, 'CREATE_FILE',
               field_name='publications_files', new_value=audit_label)
        db.session.commit()
        return jsonify({
            'message': 'Video link added',
            'id': pub_file.id,
            'handle': minted,
            'file_url': video_url_raw,
        }), 201

    # File upload branch
    validation_error = _validate_upload(uploaded)
    if validation_error:
        return jsonify({'error': validation_error}), 400

    # Mint FIRST — if Cordra is down, don't waste disk.
    minted = IdentifierService.generate_handle()
    if not minted:
        return jsonify({'error': 'Cordra handle mint failed'}), 502

    file_name, file_url, _abs_path = _save_upload(uploaded)

    pub_file = PublicationFiles(
        publication_id=publication_id,
        title=title[:255],
        description=description,
        publication_type_id=publication_type_id,
        file_name=file_name[:255],
        file_type=(uploaded.mimetype or 'application/octet-stream')[:100],
        file_url=file_url[:255],
        identifier='1',  # identifier-TYPE id (1=APA Handle iD); handle lives in handle_identifier
        generated_identifier=minted[:100],
        handle_identifier=minted[:100],
        external_identifier=ext_identifier,
        external_identifier_type=ext_identifier_type,
    )
    db.session.add(pub_file)
    db.session.flush()
    audit_label = f"{title} ({minted})"
    if ext_identifier:
        audit_label += f" doi={ext_identifier}"
    _audit(publication_id, user_id, 'CREATE_FILE',
           field_name='publications_files', new_value=audit_label)
    db.session.commit()
    return jsonify({
        'message': 'File added',
        'id': pub_file.id,
        'handle': minted,
        'file_url': file_url,
    }), 201


@edit_bp.route('/<int:publication_id>/files/<int:file_id>', methods=['PUT'])
@jwt_required()
def update_file(publication_id, file_id):
    """Update metadata on an existing file row.

    Mutable: title, description, publication_type_id, plus the external
    identifier pair (external_identifier_type + external_identifier_value).
    file_url, file_name, file_type, and handle_identifier are immutable —
    attempts to change them are silently ignored to keep Cordra + disk
    state in sync. The external identifier pair has three-state semantics:
    omitted fields = no change · empty string = clear · non-empty = set.
    """
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    pub_file = PublicationFiles.query.filter_by(id=file_id, publication_id=publication_id).first()
    if not pub_file:
        return jsonify({'error': 'File not found'}), 404

    data = request.get_json(silent=True) or {}
    changes = {}
    for field in ('title', 'description', 'publication_type_id'):
        if field not in data:
            continue
        new_value = data[field]
        if field == 'publication_type_id':
            try:
                new_value = int(new_value)
            except (ValueError, TypeError):
                return jsonify({'error': 'Invalid publication_type_id'}), 400
        elif isinstance(new_value, str):
            new_value = new_value[:255] if field == 'title' else new_value
        old_value = getattr(pub_file, field)
        if old_value != new_value:
            setattr(pub_file, field, new_value)
            changes[field] = (old_value, new_value)

    # External identifier (Crossref DOI tagging). Three-state semantics:
    #   - field omitted entirely from body  -> no change (leave column alone)
    #   - field present and empty string    -> clear (set NULL)
    #   - field present and non-empty       -> validate via _coerce_real_doi and write
    # Type and value travel together — sending only one is a 400 to catch UI bugs.
    has_ext_type = 'external_identifier_type' in data
    has_ext_value = 'external_identifier_value' in data
    if has_ext_type or has_ext_value:
        if has_ext_type != has_ext_value:
            return jsonify({
                'error': "external_identifier_type and external_identifier_value must "
                         "be sent together (or both omitted)."
            }), 400
        raw_type = data.get('external_identifier_type')
        raw_value = data.get('external_identifier_value')
        ext_type_str = (raw_type or '').strip() if isinstance(raw_type, str) else ''
        ext_value_str = (raw_value or '').strip() if isinstance(raw_value, str) else ''
        # Both empty -> clear the existing identifier.
        if not ext_type_str and not ext_value_str:
            new_ext_id = None
            new_ext_type = None
        else:
            if ext_type_str != 'DOI':
                return jsonify({
                    'error': "external_identifier_type must be 'DOI' (the only external "
                             "identifier supported here today)."
                }), 400
            if not ext_value_str:
                return jsonify({
                    'error': "external_identifier_value is required when "
                             "external_identifier_type='DOI' is supplied."
                }), 400
            coerced = _coerce_real_doi(ext_value_str)
            if coerced is None:
                return jsonify({'error': 'Invalid DOI: must look like 10.xxxx/...'}), 400
            if len(coerced) > 100:
                return jsonify({
                    'error': 'DOI too long (max 100 characters after URL-prefix stripping).'
                }), 400
            new_ext_id = coerced
            new_ext_type = 'DOI'

        old_ext_id = pub_file.external_identifier
        old_ext_type = pub_file.external_identifier_type
        if old_ext_id != new_ext_id:
            pub_file.external_identifier = new_ext_id
            changes['external_identifier'] = (old_ext_id, new_ext_id)
        if old_ext_type != new_ext_type:
            pub_file.external_identifier_type = new_ext_type
            changes['external_identifier_type'] = (old_ext_type, new_ext_type)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_FILE',
                   field_name=f'file.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'File updated', 'id': pub_file.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(publication_id, file_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    pub_file = PublicationFiles.query.filter_by(id=file_id, publication_id=publication_id).first()
    if not pub_file:
        return jsonify({'error': 'File not found'}), 404

    label = pub_file.title
    saved_url = pub_file.file_url
    db.session.delete(pub_file)
    _audit(publication_id, user_id, 'DELETE_FILE',
           field_name='publications_files', old_value=label)
    db.session.commit()
    _delete_local_file(saved_url)
    return jsonify({'message': 'File deleted'}), 200


# ---------- DOCUMENTS (publication_documents) ----------

@edit_bp.route('/<int:publication_id>/documents', methods=['POST'])
@jwt_required()
def add_document(publication_id):
    """Upload a new document OR add external video URL + mint Cordra child handle."""
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err

    title = (request.form.get('title') or '').strip()
    description = (request.form.get('description') or '').strip()
    publication_type_id_raw = request.form.get('publication_type_id', '1')
    identifier_type_id_raw = request.form.get('identifier_type_id', '1')
    video_url_raw = (request.form.get('video_url') or '').strip()
    uploaded = request.files.get('file')

    if not title:
        return jsonify({'error': 'title is required'}), 400

    try:
        publication_type_id = int(publication_type_id_raw)
        identifier_type_id = int(identifier_type_id_raw)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid publication_type_id or identifier_type_id'}), 400

    # Branch: external video URL (no upload), OR file upload
    if video_url_raw:
        if not video_url_raw.startswith(('http://', 'https://')):
            video_url_raw = 'https://' + video_url_raw
        minted = IdentifierService.generate_handle()
        if not minted:
            return jsonify({'error': 'Cordra handle mint failed'}), 502

        pub_doc = PublicationDocuments(
            publication_id=publication_id,
            title=title[:255],
            description=description,
            publication_type_id=publication_type_id,
            file_url=video_url_raw[:255],
            identifier_type_id=identifier_type_id,
            generated_identifier=minted[:255],
            handle_identifier=minted[:100],
        )
        db.session.add(pub_doc)
        db.session.flush()
        _audit(publication_id, user_id, 'CREATE_DOCUMENT',
               field_name='publication_documents', new_value=f"{title} (video) ({minted})")
        db.session.commit()
        return jsonify({
            'message': 'Video link added as document',
            'id': pub_doc.id,
            'handle': minted,
            'file_url': video_url_raw,
        }), 201

    # File upload branch
    validation_error = _validate_upload(uploaded)
    if validation_error:
        return jsonify({'error': validation_error}), 400

    minted = IdentifierService.generate_handle()
    if not minted:
        return jsonify({'error': 'Cordra handle mint failed'}), 502

    _file_name, file_url, _abs_path = _save_upload(uploaded)

    pub_doc = PublicationDocuments(
        publication_id=publication_id,
        title=title[:255],
        description=description,
        publication_type_id=publication_type_id,
        file_url=file_url[:255],
        identifier_type_id=identifier_type_id,
        generated_identifier=minted[:255],
        handle_identifier=minted[:100],
    )
    db.session.add(pub_doc)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_DOCUMENT',
           field_name='publication_documents', new_value=f"{title} ({minted})")
    db.session.commit()
    return jsonify({
        'message': 'Document added',
        'id': pub_doc.id,
        'handle': minted,
        'file_url': file_url,
    }), 201


@edit_bp.route('/<int:publication_id>/documents/<int:document_id>', methods=['PUT'])
@jwt_required()
def update_document(publication_id, document_id):
    """Update metadata on an existing document row.

    Only title, description, publication_type_id, and identifier_type_id are
    mutable. file_url, generated_identifier, handle_identifier are immutable.
    """
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    pub_doc = PublicationDocuments.query.filter_by(id=document_id, publication_id=publication_id).first()
    if not pub_doc:
        return jsonify({'error': 'Document not found'}), 404

    data = request.get_json(silent=True) or {}
    changes = {}
    for field in ('title', 'description', 'publication_type_id', 'identifier_type_id'):
        if field not in data:
            continue
        new_value = data[field]
        if field in ('publication_type_id', 'identifier_type_id'):
            try:
                new_value = int(new_value)
            except (ValueError, TypeError):
                return jsonify({'error': f'Invalid {field}'}), 400
        elif field == 'title' and isinstance(new_value, str):
            new_value = new_value[:255]
        old_value = getattr(pub_doc, field)
        if old_value != new_value:
            setattr(pub_doc, field, new_value)
            changes[field] = (old_value, new_value)

    if changes:
        for field, (old, new) in changes.items():
            _audit(publication_id, user_id, 'UPDATE_DOCUMENT',
                   field_name=f'document.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Document updated', 'id': pub_doc.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/documents/<int:document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(publication_id, document_id):
    publication, user_id, err = _authorize(publication_id)
    if err:
        return err
    pub_doc = PublicationDocuments.query.filter_by(id=document_id, publication_id=publication_id).first()
    if not pub_doc:
        return jsonify({'error': 'Document not found'}), 404

    label = pub_doc.title
    saved_url = pub_doc.file_url
    db.session.delete(pub_doc)
    _audit(publication_id, user_id, 'DELETE_DOCUMENT',
           field_name='publication_documents', old_value=label)
    db.session.commit()
    _delete_local_file(saved_url)
    return jsonify({'message': 'Document deleted'}), 200
