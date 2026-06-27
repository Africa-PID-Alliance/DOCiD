"""
Generic enrichment routes for Wave 1-4 providers:
  semantic_scholar | core | openaire | opencitations | lens_org | base | worldcat

Mirrors the OpenAlex enrichment pattern from enrichment.py:
  POST /api/v1/publications/<id>/enrich/<source>            fetch + upsert
  POST /api/v1/publications/<id>/enrich/<source>/accept     curator accept
  POST /api/v1/publications/<id>/enrich/<source>/reject     curator reject
  POST /api/v1/publications/<id>/enrich/<source>/undo       undo accepted
  GET  /api/v1/publications/<id>/enrich/<source>/preview    read-only diff
  GET  /api/v1/publications/<id>/enrich/<source>            last stored row

OAI-PMH harvest trigger (admin only):
  POST /api/v1/harvest/<source>                              run harvest (scienceopen|citeseerx)
  GET  /api/v1/harvest/<source>/status                      last harvest state
"""
import logging
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app import db
from app.models import Publications, PublicationEnrichment, PublicationExternalEdge, UserAccount
from app.service_registry import get_service, ProviderNotImplementedError, enrichment_enabled

logger = logging.getLogger(__name__)

enrichment_generic_bp = Blueprint('enrichment_generic', __name__)

# Providers handled by this blueprint (not OpenAlex — that stays in enrichment.py)
_ENRICHMENT_SOURCES = {'semantic_scholar', 'core', 'openaire', 'opencitations', 'lens_org', 'base', 'worldcat'}
_OAI_PMH_SOURCES    = {'scienceopen', 'citeseerx'}


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_admin(user_id):
    user = UserAccount.query.get(user_id)
    return bool(user and (user.role or '').lower() == 'admin')


def _authorise(publication_id):
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, None, False, (jsonify({'message': 'Authentication required'}), 401)
    publication = Publications.query.filter_by(id=publication_id).first()
    if not publication:
        return None, user_id, False, (jsonify({'message': 'Publication not found'}), 404)
    is_admin = _is_admin(user_id)
    if publication.user_id != user_id and not is_admin:
        return publication, user_id, is_admin, (
            jsonify({'message': 'Access denied: not the publication owner'}), 403,
        )
    return publication, user_id, is_admin, None


def _build_provider_client(source_name, service_module):
    """Return (client, mapper) for source_name using current app config."""
    cfg = current_app.config
    try:
        if source_name == 'semantic_scholar':
            return (
                service_module.SemanticScholarClient(
                    api_key=cfg.get('SEMANTIC_SCHOLAR_API_KEY') or None
                ),
                service_module.SemanticScholarEnrichmentMapper(),
            )
        if source_name == 'core':
            api_key = cfg.get('CORE_API_KEY', '')
            if not api_key:
                return None, None
            return (
                service_module.CoreClient(
                    api_key=api_key,
                    base_url=cfg.get('CORE_API_BASE_URL', 'https://api.core.ac.uk/v3'),
                ),
                service_module.CoreEnrichmentMapper(),
            )
        if source_name == 'openaire':
            return (
                service_module.OpenAIREClient(
                    base_url=cfg.get('OPENAIRE_API_BASE_URL', 'https://graph.openaire.eu/api')
                ),
                service_module.OpenAIREEnrichmentMapper(),
            )
        if source_name == 'opencitations':
            return (
                service_module.OpenCitationsClient(
                    access_token=cfg.get('OPENCITATIONS_ACCESS_TOKEN', '')
                ),
                service_module.OpenCitationsMapper(),
            )
        if source_name == 'lens_org':
            return (
                service_module.LensClient(
                    scholar_api_key=cfg.get('LENS_SCHOLAR_API_KEY', ''),
                    patent_api_key=cfg.get('LENS_PATENT_API_KEY', ''),
                    base_url=cfg.get('LENS_API_BASE_URL', 'https://api.lens.org'),
                ),
                service_module.LensEnrichmentMapper(),
            )
        if source_name == 'base':
            api_key = cfg.get('BASE_API_KEY', '')
            if not api_key:
                return None, None
            return (
                service_module.BaseSearchClient(
                    api_key=api_key,
                    base_url=cfg.get('BASE_API_BASE_URL', 'https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi'),
                ),
                service_module.BaseEnrichmentMapper(),
            )
        if source_name == 'worldcat':
            client_id = cfg.get('WORLDCAT_CLIENT_ID', '')
            client_secret = cfg.get('WORLDCAT_CLIENT_SECRET', '')
            if not client_id or not client_secret:
                return None, None
            return (
                service_module.WorldCatClient(
                    client_id=client_id,
                    client_secret=client_secret,
                    search_base_url=cfg.get('WORLDCAT_SEARCH_BASE_URL', 'https://americas.discovery.api.oclc.org/worldcat/search/v2'),
                    metadata_base_url=cfg.get('WORLDCAT_METADATA_BASE_URL', 'https://metadata.api.oclc.org'),
                ),
                service_module.WorldCatEnrichmentMapper(),
            )
    except Exception as exc:
        logger.error("Failed to build client for %s: %s", source_name, exc)
        return None, None
    return None, None


def _fetch_candidate(source_name, service_module, publication, client, mapper,
                     performed_by, allow_title_fallback=False):
    """Dispatch to the provider-specific fetch function."""
    if source_name == 'opencitations':
        fn = getattr(service_module, 'fetch_opencitations_edges')
        return fn(publication, client, mapper, performed_by=performed_by)
    if source_name == 'lens_org':
        fn = getattr(service_module, 'fetch_lens_candidate')
        return fn(publication, client, mapper, performed_by=performed_by)
    fn_name = f'fetch_{source_name}_candidate'
    fn = getattr(service_module, fn_name)
    return fn(publication, client, mapper, performed_by=performed_by,
              allow_title_fallback=allow_title_fallback)


def _apply_enrichment(source_name, service_module, publication, payload):
    fn_name = f'apply_{source_name}_enrichment_to_publication'
    fn = getattr(service_module, fn_name, None)
    if fn:
        fn(publication, payload)


def _snapshot_fields(source_name, service_module, publication) -> dict:
    fn_name = f'snapshot_publication_{source_name}_fields'
    fn = getattr(service_module, fn_name, None)
    return fn(publication) if fn else {}


def _restore_from_snapshot(service_module, publication, snapshot):
    fn = getattr(service_module, 'restore_publication_from_snapshot', None)
    if fn:
        fn(publication, snapshot)


def _upsert_external_edges(publication_id: int, edges: list) -> int:
    """Upsert edge dicts into publication_external_edges; returns count."""
    if not edges:
        return 0
    now = datetime.utcnow()
    count = 0
    for edge in edges:
        stmt = pg_insert(PublicationExternalEdge).values(
            publication_id=publication_id,
            object_id_kind=edge['object_id_kind'],
            object_id=edge['object_id'],
            object_label=edge.get('object_label'),
            relation=edge['relation'],
            source_name=edge['source_name'],
            confidence=edge.get('confidence'),
            raw_metadata=edge.get('raw_metadata'),
            created_at=now,
            updated_at=now,
        ).on_conflict_do_update(
            constraint='uq_publication_external_edge',
            set_={
                'object_label': edge.get('object_label'),
                'confidence':   edge.get('confidence'),
                'raw_metadata': edge.get('raw_metadata'),
                'updated_at':   now,
            },
        )
        db.session.execute(stmt)
        count += 1
    return count


def _serialise_row(row):
    if not row:
        return None
    raw = row.raw_response or {}
    return {
        'id':            row.id,
        'publication_id':row.publication_id,
        'source_name':   row.source_name,
        'status':        row.status,
        'review_status': row.review_status,
        'reviewed_by':   row.reviewed_by,
        'reviewed_at':   row.reviewed_at.isoformat() + 'Z' if row.reviewed_at else None,
        'review_note':   row.review_note,
        'enriched_at':   row.enriched_at.isoformat() + 'Z' if row.enriched_at else None,
        'error_message': row.error_message,
        'provenance':    raw.get('provenance') if isinstance(raw, dict) else None,
    }


# ---------------------------------------------------------------------------
# Per-publication enrichment routes
# ---------------------------------------------------------------------------

@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>',
    methods=['POST'],
)
@jwt_required()
def run_enrichment(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown enrichment source: {source_name!r}'}), 404

    try:
        service_module = get_service(source_name)
    except ProviderNotImplementedError as exc:
        return jsonify({'message': 'Not implemented', 'reason': str(exc)}), 501
    except KeyError as exc:
        return jsonify({'message': str(exc)}), 404

    publication, user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    allow_title_fallback = request.args.get('title_fallback', '').lower() in ('1', 'true', 'yes')
    performed_by = f'user:{user_id}'

    client, mapper = _build_provider_client(source_name, service_module)
    if client is None:
        return jsonify({
            'status': 'error',
            'message': f'{source_name.upper()}_API_KEY not configured. Add it to .env and restart.',
        }), 503

    try:
        status, error_message, payload = _fetch_candidate(
            source_name, service_module, publication, client, mapper,
            performed_by=performed_by, allow_title_fallback=allow_title_fallback,
        )
    except Exception as exc:
        db.session.rollback()
        logger.exception('Enrichment failed for pub %s source %s', publication_id, source_name)
        return jsonify({'status': 'error', 'message': str(exc)}), 502

    review_status = None
    edges_upserted = 0

    if status == 'enriched' and payload:
        match_method = payload.get('match_method')
        # opencitations has no publication columns to apply — edges only.
        applies_columns = bool(getattr(service_module, f'{"_".join(["snapshot_publication", source_name, "fields"])}', None))
        is_auto_accept = (match_method == 'doi' and source_name != 'opencitations')

        if is_auto_accept:
            review_status = 'accepted'
            payload['pre_apply_snapshot'] = _snapshot_fields(source_name, service_module, publication)
            if isinstance(payload.get('provenance'), dict):
                payload['provenance']['status'] = 'accepted'
            _apply_enrichment(source_name, service_module, publication, payload)
            publication.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        elif source_name == 'opencitations':
            # No publication columns; edges always auto-accepted.
            review_status = 'accepted'
        else:
            review_status = 'pending_review'
            if isinstance(payload.get('provenance'), dict):
                payload['provenance']['status'] = 'pending_review'

        # Persist edges regardless of review path.
        edges = payload.get('edges') or []
        if edges:
            try:
                edges_upserted = _upsert_external_edges(publication.id, edges)
            except Exception as exc:
                logger.warning("Edge upsert failed (non-fatal): %s", exc)

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name=source_name
    ).first()
    if row is None:
        row = PublicationEnrichment(
            publication_id=publication.id,
            source_name=source_name,
            retry_count=0,
        )
        db.session.add(row)
    else:
        row.retry_count = (row.retry_count or 0) + 1

    row.status        = status
    row.error_message = error_message
    row.raw_response  = payload if status == 'enriched' else None
    if status == 'enriched':
        row.enriched_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if review_status:
        row.review_status = review_status
        if review_status == 'accepted':
            row.reviewed_by  = user_id
            row.reviewed_at  = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        logger.exception('Commit failed for pub %s source %s', publication_id, source_name)
        return jsonify({'status': 'error', 'message': str(exc)}), 500

    body = {
        'status':        status,
        'review_status': review_status,
        'publication_id':publication.id,
        'source_name':   source_name,
        'match_method':  payload.get('match_method') if payload else None,
        'enrichment':    payload.get('enrichment') if payload else None,
        'edges_upserted':edges_upserted,
        'provenance':    payload.get('provenance') if payload else None,
    }
    if error_message:
        body['reason'] = error_message
    return jsonify(body), 200


@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>/accept',
    methods=['POST'],
)
@jwt_required()
def accept_enrichment(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown source: {source_name!r}'}), 404

    try:
        service_module = get_service(source_name)
    except (ProviderNotImplementedError, KeyError) as exc:
        return jsonify({'message': str(exc)}), 501

    publication, user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name=source_name
    ).first()
    if not row or row.status != 'enriched' or not row.raw_response:
        return jsonify({'message': f'No enriched {source_name} candidate to accept'}), 404
    if row.review_status == 'accepted':
        return jsonify({'message': 'Already accepted', 'review_status': 'accepted'}), 200
    if row.review_status == 'rejected':
        return jsonify({'message': 'Candidate was rejected — re-run POST /enrich first'}), 409

    payload = row.raw_response or {}
    if isinstance(payload, dict) and not payload.get('pre_apply_snapshot'):
        payload['pre_apply_snapshot'] = _snapshot_fields(source_name, service_module, publication)
    _apply_enrichment(source_name, service_module, publication, payload)

    # Persist any edges that arrived with the payload (edge-only providers skip this).
    edges = payload.get('edges') or [] if isinstance(payload, dict) else []
    if edges:
        try:
            _upsert_external_edges(publication.id, edges)
        except Exception as exc:
            logger.warning("Edge upsert on accept failed (non-fatal): %s", exc)

    note = (request.get_json(silent=True) or {}).get('review_note') if request.is_json else None
    row.review_status = 'accepted'
    row.reviewed_by   = user_id
    row.reviewed_at   = datetime.now(timezone.utc).replace(tzinfo=None)
    row.review_note   = note
    if isinstance(payload, dict) and isinstance(payload.get('provenance'), dict):
        payload['provenance']['status'] = 'accepted'
        payload['provenance']['reviewedBy'] = f'user:{user_id}'
        row.raw_response = payload
        flag_modified(row, 'raw_response')
    publication.updated_at = row.reviewed_at

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 500

    return jsonify({
        'status':       'accepted',
        'source_name':  source_name,
        'publication_id': publication.id,
        'reviewed_by':  user_id,
        'reviewed_at':  row.reviewed_at.isoformat() + 'Z',
    }), 200


@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>/reject',
    methods=['POST'],
)
@jwt_required()
def reject_enrichment(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown source: {source_name!r}'}), 404

    publication, user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name=source_name
    ).first()
    if not row:
        return jsonify({'message': 'No enrichment row to reject'}), 404
    if row.review_status == 'rejected':
        return jsonify({'message': 'Already rejected', 'review_status': 'rejected'}), 200

    note = (request.get_json(silent=True) or {}).get('review_note') if request.is_json else None
    row.review_status = 'rejected'
    row.reviewed_by   = user_id
    row.reviewed_at   = datetime.now(timezone.utc).replace(tzinfo=None)
    row.review_note   = note
    payload = row.raw_response
    if isinstance(payload, dict) and isinstance(payload.get('provenance'), dict):
        payload['provenance']['status'] = 'rejected'
        payload['provenance']['reviewedBy'] = f'user:{user_id}'
        row.raw_response = payload
        flag_modified(row, 'raw_response')

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 500

    return jsonify({
        'status':       'rejected',
        'source_name':  source_name,
        'publication_id': publication.id,
        'reviewed_by':  user_id,
        'reviewed_at':  row.reviewed_at.isoformat() + 'Z',
    }), 200


@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>/undo',
    methods=['POST'],
)
@jwt_required()
def undo_enrichment(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown source: {source_name!r}'}), 404

    try:
        service_module = get_service(source_name)
    except (ProviderNotImplementedError, KeyError) as exc:
        return jsonify({'message': str(exc)}), 501

    publication, user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name=source_name
    ).first()
    if not row:
        return jsonify({'message': 'No enrichment row to undo'}), 404
    if row.review_status != 'accepted':
        return jsonify({
            'message': f'Cannot undo: review_status={row.review_status!r}; only accepted rows are reversible.',
        }), 409

    payload = row.raw_response or {}
    snapshot = payload.get('pre_apply_snapshot') if isinstance(payload, dict) else None
    if not isinstance(snapshot, dict):
        return jsonify({'message': 'No pre-apply snapshot — cannot safely undo.'}), 409

    _restore_from_snapshot(service_module, publication, snapshot)

    note = (request.get_json(silent=True) or {}).get('review_note') if request.is_json else None
    row.review_status = 'rejected'
    row.reviewed_by   = user_id
    row.reviewed_at   = datetime.now(timezone.utc).replace(tzinfo=None)
    row.review_note   = note or 'undone'
    if isinstance(payload, dict) and isinstance(payload.get('provenance'), dict):
        payload['provenance']['status']    = 'rejected'
        payload['provenance']['reviewedBy']= f'user:{user_id}'
        payload['provenance']['undone']    = True
        row.raw_response = payload
        flag_modified(row, 'raw_response')
    publication.updated_at = row.reviewed_at

    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'message': str(exc)}), 500

    return jsonify({
        'status':          'undone',
        'source_name':     source_name,
        'review_status':   'rejected',
        'publication_id':  publication.id,
        'restored_fields': list(snapshot.keys()),
        'reviewed_by':     user_id,
        'reviewed_at':     row.reviewed_at.isoformat() + 'Z',
    }), 200


@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>/preview',
    methods=['GET'],
)
@jwt_required()
def preview_enrichment(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown source: {source_name!r}'}), 404

    try:
        service_module = get_service(source_name)
    except (ProviderNotImplementedError, KeyError) as exc:
        return jsonify({'message': str(exc)}), 501

    publication, user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    allow_title_fallback = request.args.get('title_fallback', '').lower() in ('1', 'true', 'yes')
    client, mapper = _build_provider_client(source_name, service_module)
    if client is None:
        return jsonify({'status': 'error', 'message': f'{source_name} API key not configured'}), 503

    try:
        status, error_message, payload = _fetch_candidate(
            source_name, service_module, publication, client, mapper,
            performed_by='preview', allow_title_fallback=allow_title_fallback,
        )
    except Exception as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 502

    if status != 'enriched':
        return jsonify({'status': status, 'reason': error_message}), 404 if status == 'not_found' else 400

    return jsonify({
        'status':        'preview',
        'source_name':   source_name,
        'publication_id':publication.id,
        'match_method':  payload.get('match_method'),
        'enrichment':    payload.get('enrichment'),
        'edges_count':   len(payload.get('edges') or []),
        'provenance':    payload.get('provenance'),
    }), 200


@enrichment_generic_bp.route(
    '/api/v1/publications/<int:publication_id>/enrich/<source_name>',
    methods=['GET'],
)
@jwt_required()
def get_enrichment_row(publication_id, source_name):
    if source_name not in _ENRICHMENT_SOURCES:
        return jsonify({'message': f'Unknown source: {source_name!r}'}), 404

    publication, _user_id, _admin, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name=source_name
    ).first()
    if not row:
        return jsonify({'status': 'none', 'publication_id': publication.id, 'source_name': source_name}), 404

    return jsonify(_serialise_row(row)), 200


# ---------------------------------------------------------------------------
# OAI-PMH harvest trigger routes (admin only)
# ---------------------------------------------------------------------------

@enrichment_generic_bp.route('/api/v1/harvest/<source_name>', methods=['POST'])
@jwt_required()
def trigger_harvest(source_name):
    """Trigger an incremental OAI-PMH harvest for source_name (admin only)."""
    if source_name not in _OAI_PMH_SOURCES:
        return jsonify({'message': f'Unknown harvest source: {source_name!r}'}), 404

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'message': 'Authentication required'}), 401
    if not _is_admin(user_id):
        return jsonify({'message': 'Admin required'}), 403

    try:
        service_module = get_service(source_name)
    except (ProviderNotImplementedError, KeyError) as exc:
        return jsonify({'message': str(exc)}), 501

    body = request.get_json(silent=True) or {}
    page_limit = int(body.get('page_limit', 0))

    try:
        summary = service_module.harvest(db.session, page_limit=page_limit)
    except Exception as exc:
        logger.exception('Harvest failed for %s', source_name)
        return jsonify({'status': 'error', 'message': str(exc)}), 502

    return jsonify({'source_name': source_name, **summary}), 200


@enrichment_generic_bp.route('/api/v1/harvest/<source_name>/status', methods=['GET'])
@jwt_required()
def harvest_status(source_name):
    """Return the current HarvestState row for source_name (admin only)."""
    if source_name not in _OAI_PMH_SOURCES:
        return jsonify({'message': f'Unknown harvest source: {source_name!r}'}), 404

    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return jsonify({'message': 'Authentication required'}), 401
    if not _is_admin(user_id):
        return jsonify({'message': 'Admin required'}), 403

    try:
        service_module = get_service(source_name)
    except (ProviderNotImplementedError, KeyError) as exc:
        return jsonify({'message': str(exc)}), 501

    client = service_module.get_scienceopen_client() if source_name == 'scienceopen' else service_module.get_citeseerx_client()

    from app.models import HarvestState
    import sqlalchemy as sa
    row = db.session.execute(
        sa.text(
            "SELECT id, endpoint, metadata_prefix, set_spec, last_success_from, "
            "last_success_until, in_progress, last_run_at, last_run_status, "
            "consecutive_failures, last_error_message "
            "FROM harvest_state WHERE endpoint = :ep AND metadata_prefix = :pfx "
            "AND COALESCE(set_spec,'') = COALESCE(:ss,'')"
        ),
        {"ep": client.endpoint, "pfx": client.metadata_prefix, "ss": client.set_spec},
    ).fetchone()

    if not row:
        return jsonify({'status': 'never_run', 'source_name': source_name}), 200

    return jsonify({
        'source_name':        source_name,
        'endpoint':           row[1],
        'last_success_from':  row[4].isoformat() if row[4] else None,
        'last_success_until': row[5].isoformat() if row[5] else None,
        'in_progress':        row[6],
        'last_run_at':        row[7].isoformat() if row[7] else None,
        'last_run_status':    row[8],
        'consecutive_failures': row[9],
        'last_error_message': row[10],
    }), 200
