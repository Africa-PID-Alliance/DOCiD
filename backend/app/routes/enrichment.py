"""
On-demand OpenAlex enrichment routes (Phase 1).

Endpoints:
    POST /api/v1/publications/<id>/enrich/openalex          -- run + upsert
    GET  /api/v1/publications/<id>/enrich/openalex/preview  -- read-only fetch + conflict diff
    GET  /api/v1/publications/<id>/enrich/openalex          -- last stored enrichment row

Auto-accepts DOI matches only (per integration guide §11.3). Title-search fallback
and curator review workflow are deferred to Phase 2.
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Publications, PublicationEnrichment, UserAccount
from app.service_openalex import (
    OpenAlexClient,
    OpenAlexEnrichmentMapper,
    enrich_publication_openalex,
    normalize_doi,
)

logger = logging.getLogger(__name__)

enrichment_bp = Blueprint('enrichment', __name__, url_prefix='/api/v1/publications')


def _is_admin(user_id):
    user = UserAccount.query.get(user_id)
    return bool(user and (user.role or '').lower() == 'admin')


def _authorise(publication_id):
    """Return (publication, user_id, error_response) tuple."""
    try:
        user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, None, (jsonify({'message': 'Authentication required'}), 401)

    publication = Publications.query.filter_by(id=publication_id).first()
    if not publication:
        return None, user_id, (jsonify({'message': 'Publication not found'}), 404)

    if publication.user_id != user_id and not _is_admin(user_id):
        return publication, user_id, (
            jsonify({'message': 'Access denied: not the publication owner'}),
            403,
        )

    return publication, user_id, None


def _build_client():
    contact_email = current_app.config.get(
        'OPENALEX_CONTACT_EMAIL', 'admin@docid.africapidalliance.org'
    )
    return OpenAlexClient(contact_email), OpenAlexEnrichmentMapper


def _serialise_enrichment_row(row):
    if not row:
        return None
    raw = row.raw_response or {}
    provenance = raw.get('provenance') if isinstance(raw, dict) else None
    return {
        'id': row.id,
        'publication_id': row.publication_id,
        'source_name': row.source_name,
        'status': row.status,
        'enriched_at': row.enriched_at.isoformat() + 'Z' if row.enriched_at else None,
        'error_message': row.error_message,
        'retry_count': row.retry_count or 0,
        'provenance': provenance,
    }


def _build_conflicts(publication, summary):
    """Compare DOCiD publication fields against OpenAlex summary."""
    conflicts = []

    def _norm(text):
        return (text or '').strip().lower()

    oa_title = summary.get('title')
    if oa_title and publication.document_title and _norm(oa_title) != _norm(publication.document_title):
        conflicts.append({
            'field': 'title',
            'docidValue': publication.document_title,
            'openAlexValue': oa_title,
            'severity': 'medium',
        })

    oa_doi = normalize_doi(summary.get('doi') or '')
    pub_doi = normalize_doi(publication.doi or '')
    if oa_doi and pub_doi and oa_doi.lower() != pub_doi.lower():
        conflicts.append({
            'field': 'doi',
            'docidValue': publication.doi,
            'openAlexValue': summary.get('doi'),
            'severity': 'high',
        })

    oa_year = summary.get('publication_year')
    pub_year = publication.publication_date.year if getattr(publication, 'publication_date', None) else None
    if oa_year and pub_year and oa_year != pub_year:
        conflicts.append({
            'field': 'publication_year',
            'docidValue': pub_year,
            'openAlexValue': oa_year,
            'severity': 'medium',
        })

    oa_is_oa = summary.get('is_oa')
    docid_is_oa = publication.open_access_status not in (None, '', 'closed')
    if oa_is_oa is not None and bool(oa_is_oa) != docid_is_oa:
        conflicts.append({
            'field': 'open_access',
            'docidValue': publication.open_access_status,
            'openAlexValue': oa_is_oa,
            'severity': 'low',
        })

    return conflicts


@enrichment_bp.route('/<int:publication_id>/enrich/openalex', methods=['POST'])
@jwt_required()
def run_openalex_enrichment(publication_id):
    publication, user_id, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    if not normalize_doi(publication.doi or ''):
        return jsonify({
            'status': 'skipped',
            'reason': 'no_valid_doi',
            'message': 'Publication has no valid DOI for OpenAlex lookup',
        }), 400

    client, mapper = _build_client()
    performed_by = f'user:{user_id}'

    try:
        status, error_message, payload = enrich_publication_openalex(
            publication, client, mapper, performed_by=performed_by
        )
    except Exception as enrichment_error:
        db.session.rollback()
        logger.exception('OpenAlex enrichment failed for publication %s', publication_id)
        return jsonify({
            'status': 'error',
            'message': str(enrichment_error),
        }), 502

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex'
    ).first()
    if row is None:
        row = PublicationEnrichment(
            publication_id=publication.id,
            source_name='openalex',
            retry_count=0,
        )
        db.session.add(row)
    else:
        row.retry_count = (row.retry_count or 0) + 1

    row.status = status
    row.error_message = error_message
    row.enriched_at = datetime.now(timezone.utc).replace(tzinfo=None) if status == 'enriched' else row.enriched_at
    row.raw_response = payload if status == 'enriched' else None

    try:
        db.session.commit()
    except Exception as commit_error:
        db.session.rollback()
        logger.exception('Failed to commit enrichment row for publication %s', publication_id)
        return jsonify({'status': 'error', 'message': str(commit_error)}), 500

    response_body = {
        'status': status,
        'publication_id': publication.id,
        'openalex_id': publication.openalex_id,
        'provenance': payload.get('provenance') if payload else None,
        'enrichment': payload.get('enrichment') if payload else None,
    }
    if error_message:
        response_body['reason'] = error_message
    return jsonify(response_body), 200


@enrichment_bp.route('/<int:publication_id>/enrich/openalex/preview', methods=['GET'])
@jwt_required()
def preview_openalex_enrichment(publication_id):
    publication, _user_id, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    normalized_doi = normalize_doi(publication.doi or '')
    if not normalized_doi:
        return jsonify({
            'status': 'skipped',
            'reason': 'no_valid_doi',
            'message': 'Publication has no valid DOI for OpenAlex lookup',
        }), 400

    client, mapper = _build_client()
    work_data = client.get_work_by_doi(normalized_doi)
    if not work_data:
        return jsonify({'status': 'not_found', 'doi': normalized_doi}), 404

    enrichment_data = mapper.extract_work_enrichment(work_data)
    summary = mapper.extract_work_summary(work_data)
    conflicts = _build_conflicts(publication, summary)

    return jsonify({
        'status': 'preview',
        'publication_id': publication.id,
        'enrichment': enrichment_data,
        'summary': summary,
        'conflicts': conflicts,
    }), 200


@enrichment_bp.route('/<int:publication_id>/enrich/openalex', methods=['GET'])
@jwt_required()
def get_openalex_enrichment(publication_id):
    publication, _user_id, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex'
    ).first()
    if not row:
        return jsonify({'status': 'none', 'publication_id': publication.id}), 404

    return jsonify(_serialise_enrichment_row(row)), 200
