"""
Publication Edit Routes — per-entity CRUD endpoints for editing a DOCiD
without re-minting the top-level Cordra handle.

Rules:
- Only the owner (publication.user_id == caller user_id) can edit.
- Top-level document_docid handle NEVER changes or re-mints.
- NEW files and documents mint their own Cordra child handles.
- All mutations logged to PublicationAuditTrail.
"""
import logging
import os
from datetime import datetime
from urllib.parse import quote as url_quote

from flask import Blueprint, jsonify, request
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


# ---------- helpers ----------

def _get_user_id_from_request():
    """Extract user_id from JSON body, form, or query string."""
    user_id = None
    if request.is_json:
        user_id = (request.get_json() or {}).get('user_id')
    if user_id is None:
        user_id = request.form.get('user_id') or request.args.get('user_id')
    try:
        return int(user_id) if user_id is not None else None
    except (ValueError, TypeError):
        return None


def _authorize(publication_id):
    """Return (publication, None) on success or (None, error_response) on failure."""
    user_id = _get_user_id_from_request()
    if not user_id:
        return None, (jsonify({'error': 'user_id is required'}), 400)
    publication = Publications.query.filter_by(id=publication_id).first()
    if not publication:
        return None, (jsonify({'error': 'Publication not found'}), 404)
    if publication.user_id != user_id:
        return None, (jsonify({'error': 'Access denied: you do not own this publication'}), 403)
    return publication, None


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


def _save_upload(file_storage, subdir=''):
    """Save an uploaded werkzeug FileStorage to uploads/[subdir]. Return (file_name, file_url)."""
    base_url = (os.environ.get('PUBLIC_BASE_URL') or 'https://docid.africapidalliance.org').rstrip('/')
    safe_name = secure_filename(file_storage.filename) or 'upload.bin'
    target_dir = os.path.join(UPLOAD_DIR, subdir) if subdir else UPLOAD_DIR
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, safe_name)
    file_storage.save(target_path)
    url_path = f"/{target_dir}/{url_quote(safe_name)}"
    return safe_name, f"{base_url}{url_path}"


# ---------- CREATORS ----------

@edit_bp.route('/<int:publication_id>/creators', methods=['POST'])
def add_creator(publication_id):
    """Add a new creator. Body: {user_id, family_name, given_name, identifier, identifier_type, role_id, affiliation}"""
    publication, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json() or {}
    if not data.get('family_name'):
        return jsonify({'error': 'family_name is required'}), 400

    role_id = data.get('role_id')
    if not role_id:
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        role_id = author_role.role_id if author_role else None

    creator = PublicationCreators(
        publication_id=publication_id,
        family_name=(data.get('family_name') or '')[:255],
        given_name=(data.get('given_name') or '')[:255],
        identifier=(data.get('identifier') or '')[:500],
        identifier_type=(data.get('identifier_type') or '')[:50],
        role_id=role_id,
        affiliation=(data.get('affiliation') or None),
    )
    db.session.add(creator)
    db.session.flush()
    _audit(publication_id, data['user_id'], 'CREATE_CREATOR',
           field_name='publication_creators', new_value=f"{creator.given_name} {creator.family_name}")
    db.session.commit()
    return jsonify({'message': 'Creator added', 'id': creator.id}), 201


@edit_bp.route('/<int:publication_id>/creators/<int:creator_id>', methods=['PUT'])
def update_creator(publication_id, creator_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    creator = PublicationCreators.query.filter_by(id=creator_id, publication_id=publication_id).first()
    if not creator:
        return jsonify({'error': 'Creator not found for this publication'}), 404

    data = request.get_json() or {}
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
            _audit(publication_id, data['user_id'], 'UPDATE_CREATOR',
                   field_name=f'creator.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Creator updated', 'id': creator.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/creators/<int:creator_id>', methods=['DELETE'])
def delete_creator(publication_id, creator_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    creator = PublicationCreators.query.filter_by(id=creator_id, publication_id=publication_id).first()
    if not creator:
        return jsonify({'error': 'Creator not found'}), 404

    label = f"{creator.given_name} {creator.family_name}"
    user_id = _get_user_id_from_request()
    db.session.delete(creator)
    _audit(publication_id, user_id, 'DELETE_CREATOR',
           field_name='publication_creators', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Creator deleted'}), 200


# ---------- ORGANIZATIONS ----------

@edit_bp.route('/<int:publication_id>/organizations', methods=['POST'])
def add_organization(publication_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json() or {}
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'name and type are required'}), 400

    org = PublicationOrganization(
        publication_id=publication_id,
        name=(data.get('name') or '')[:255],
        type=(data.get('type') or '')[:255],
        other_name=(data.get('other_name') or None),
        country=(data.get('country') or None),
        identifier_type=(data.get('identifier_type') or None),
        identifier=(data.get('identifier') or None),
        rrid=(data.get('rrid') or None),
    )
    db.session.add(org)
    db.session.flush()
    _audit(publication_id, data['user_id'], 'CREATE_ORGANIZATION',
           field_name='publication_organizations', new_value=org.name)
    db.session.commit()
    return jsonify({'message': 'Organization added', 'id': org.id}), 201


@edit_bp.route('/<int:publication_id>/organizations/<int:org_id>', methods=['PUT'])
def update_organization(publication_id, org_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    org = PublicationOrganization.query.filter_by(id=org_id, publication_id=publication_id).first()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    data = request.get_json() or {}
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
            _audit(publication_id, data['user_id'], 'UPDATE_ORGANIZATION',
                   field_name=f'organization.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Organization updated', 'id': org.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/organizations/<int:org_id>', methods=['DELETE'])
def delete_organization(publication_id, org_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    org = PublicationOrganization.query.filter_by(id=org_id, publication_id=publication_id).first()
    if not org:
        return jsonify({'error': 'Organization not found'}), 404

    label = org.name
    user_id = _get_user_id_from_request()
    db.session.delete(org)
    _audit(publication_id, user_id, 'DELETE_ORGANIZATION',
           field_name='publication_organizations', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Organization deleted'}), 200


# ---------- FUNDERS ----------

@edit_bp.route('/<int:publication_id>/funders', methods=['POST'])
def add_funder(publication_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json() or {}
    if not data.get('name') or not data.get('type'):
        return jsonify({'error': 'name and type are required'}), 400

    funder_type_id = data.get('funder_type_id') or 1  # Default to Grantor
    funder = PublicationFunders(
        publication_id=publication_id,
        name=(data.get('name') or '')[:255],
        type=(data.get('type') or '')[:255],
        funder_type_id=funder_type_id,
        other_name=(data.get('other_name') or None),
        country=(data.get('country') or None),
        identifier_type=(data.get('identifier_type') or None),
        identifier=(data.get('identifier') or None),
    )
    db.session.add(funder)
    db.session.flush()
    _audit(publication_id, data['user_id'], 'CREATE_FUNDER',
           field_name='publication_funders', new_value=funder.name)
    db.session.commit()
    return jsonify({'message': 'Funder added', 'id': funder.id}), 201


@edit_bp.route('/<int:publication_id>/funders/<int:funder_id>', methods=['PUT'])
def update_funder(publication_id, funder_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    funder = PublicationFunders.query.filter_by(id=funder_id, publication_id=publication_id).first()
    if not funder:
        return jsonify({'error': 'Funder not found'}), 404

    data = request.get_json() or {}
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
            _audit(publication_id, data['user_id'], 'UPDATE_FUNDER',
                   field_name=f'funder.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Funder updated', 'id': funder.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/funders/<int:funder_id>', methods=['DELETE'])
def delete_funder(publication_id, funder_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    funder = PublicationFunders.query.filter_by(id=funder_id, publication_id=publication_id).first()
    if not funder:
        return jsonify({'error': 'Funder not found'}), 404

    label = funder.name
    user_id = _get_user_id_from_request()
    db.session.delete(funder)
    _audit(publication_id, user_id, 'DELETE_FUNDER',
           field_name='publication_funders', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Funder deleted'}), 200


# ---------- PROJECTS ----------

@edit_bp.route('/<int:publication_id>/projects', methods=['POST'])
def add_project(publication_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    data = request.get_json() or {}
    if not data.get('title'):
        return jsonify({'error': 'title is required'}), 400

    project = PublicationProjects(
        publication_id=publication_id,
        title=(data.get('title') or '')[:255],
        description=(data.get('description') or ''),
        raid_id=(data.get('raid_id') or None),
        identifier=(data.get('identifier') or None),
        identifier_type=(data.get('identifier_type') or None),
    )
    db.session.add(project)
    db.session.flush()
    _audit(publication_id, data['user_id'], 'CREATE_PROJECT',
           field_name='publication_projects', new_value=project.title)
    db.session.commit()
    return jsonify({'message': 'Project added', 'id': project.id}), 201


@edit_bp.route('/<int:publication_id>/projects/<int:project_id>', methods=['PUT'])
def update_project(publication_id, project_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    project = PublicationProjects.query.filter_by(id=project_id, publication_id=publication_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    data = request.get_json() or {}
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
            _audit(publication_id, data['user_id'], 'UPDATE_PROJECT',
                   field_name=f'project.{field}', old_value=old, new_value=new)
        db.session.commit()
    return jsonify({'message': 'Project updated', 'id': project.id, 'changes': list(changes.keys())}), 200


@edit_bp.route('/<int:publication_id>/projects/<int:project_id>', methods=['DELETE'])
def delete_project(publication_id, project_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    project = PublicationProjects.query.filter_by(id=project_id, publication_id=publication_id).first()
    if not project:
        return jsonify({'error': 'Project not found'}), 404

    label = project.title
    user_id = _get_user_id_from_request()
    db.session.delete(project)
    _audit(publication_id, user_id, 'DELETE_PROJECT',
           field_name='publication_projects', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Project deleted'}), 200


# ---------- FILES (publications_files) ----------

@edit_bp.route('/<int:publication_id>/files', methods=['POST'])
def add_file(publication_id):
    """Upload a new file + mint a new Cordra child handle for it."""
    publication, err = _authorize(publication_id)
    if err:
        return err

    user_id = _get_user_id_from_request()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    publication_type_id = request.form.get('publication_type_id', '1')
    uploaded = request.files.get('file')

    if not title or not uploaded or not uploaded.filename:
        return jsonify({'error': 'title and file are required'}), 400

    try:
        publication_type_id = int(publication_type_id)
    except ValueError:
        return jsonify({'error': 'Invalid publication_type_id'}), 400

    # Save file
    file_name, file_url = _save_upload(uploaded)

    # Mint new Cordra child handle
    minted = IdentifierService.generate_handle()
    if not minted:
        return jsonify({'error': 'Cordra handle mint failed'}), 502

    pub_file = PublicationFiles(
        publication_id=publication_id,
        title=title[:255],
        description=description,
        publication_type_id=publication_type_id,
        file_name=file_name[:255],
        file_type=uploaded.mimetype or 'application/octet-stream',
        file_url=file_url[:255],
        identifier=minted[:100],
        generated_identifier=minted[:100],
        handle_identifier=minted[:100],
    )
    db.session.add(pub_file)
    db.session.flush()
    _audit(publication_id, user_id, 'CREATE_FILE',
           field_name='publications_files', new_value=f"{title} ({minted})")
    db.session.commit()
    return jsonify({
        'message': 'File added',
        'id': pub_file.id,
        'handle': minted,
        'file_url': file_url,
    }), 201


@edit_bp.route('/<int:publication_id>/files/<int:file_id>', methods=['DELETE'])
def delete_file(publication_id, file_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    pub_file = PublicationFiles.query.filter_by(id=file_id, publication_id=publication_id).first()
    if not pub_file:
        return jsonify({'error': 'File not found'}), 404

    label = pub_file.title
    user_id = _get_user_id_from_request()
    db.session.delete(pub_file)
    _audit(publication_id, user_id, 'DELETE_FILE',
           field_name='publications_files', old_value=label)
    db.session.commit()
    return jsonify({'message': 'File deleted'}), 200


# ---------- DOCUMENTS (publication_documents) ----------

@edit_bp.route('/<int:publication_id>/documents', methods=['POST'])
def add_document(publication_id):
    """Upload a new document + mint a new Cordra child handle for it."""
    publication, err = _authorize(publication_id)
    if err:
        return err

    user_id = _get_user_id_from_request()
    title = request.form.get('title', '').strip()
    description = request.form.get('description', '').strip()
    publication_type_id = request.form.get('publication_type_id', '1')
    identifier_type_id = request.form.get('identifier_type_id', '1')
    uploaded = request.files.get('file')

    if not title or not uploaded or not uploaded.filename:
        return jsonify({'error': 'title and file are required'}), 400

    try:
        publication_type_id = int(publication_type_id)
        identifier_type_id = int(identifier_type_id)
    except ValueError:
        return jsonify({'error': 'Invalid publication_type_id or identifier_type_id'}), 400

    file_name, file_url = _save_upload(uploaded)

    minted = IdentifierService.generate_handle()
    if not minted:
        return jsonify({'error': 'Cordra handle mint failed'}), 502

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


@edit_bp.route('/<int:publication_id>/documents/<int:document_id>', methods=['DELETE'])
def delete_document(publication_id, document_id):
    publication, err = _authorize(publication_id)
    if err:
        return err
    pub_doc = PublicationDocuments.query.filter_by(id=document_id, publication_id=publication_id).first()
    if not pub_doc:
        return jsonify({'error': 'Document not found'}), 404

    label = pub_doc.title
    user_id = _get_user_id_from_request()
    db.session.delete(pub_doc)
    _audit(publication_id, user_id, 'DELETE_DOCUMENT',
           field_name='publication_documents', old_value=label)
    db.session.commit()
    return jsonify({'message': 'Document deleted'}), 200
