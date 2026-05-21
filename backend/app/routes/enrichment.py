"""
On-demand OpenAlex enrichment routes.

Endpoints:
    POST /api/v1/publications/<id>/enrich/openalex            -- fetch + upsert candidate; auto-apply iff DOI match + no high-severity conflicts
    POST /api/v1/publications/<id>/enrich/openalex/accept     -- curator (admin/owner) applies a pending candidate
    POST /api/v1/publications/<id>/enrich/openalex/reject     -- curator marks the candidate rejected (no Publication mutation)
    GET  /api/v1/publications/<id>/enrich/openalex/preview    -- read-only fetch + conflict diff
    GET  /api/v1/publications/<id>/enrich/openalex            -- last stored enrichment row

Query string: ``?title_fallback=1`` on POST opts in to title-search when no DOI
is available; results from title search are NEVER auto-applied — they always
land in ``pending_review``.
"""

import logging
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models import Publications, PublicationEnrichment, UserAccount
from app.service_openalex import (
    OpenAlexClient,
    OpenAlexEnrichmentMapper,
    fetch_openalex_candidate,
    apply_openalex_enrichment_to_publication,
    normalize_doi,
)

logger = logging.getLogger(__name__)

enrichment_bp = Blueprint('enrichment', __name__, url_prefix='/api/v1/publications')


def _is_admin(user_id):
    user = UserAccount.query.get(user_id)
    return bool(user and (user.role or '').lower() == 'admin')


def _authorise(publication_id):
    """Return (publication, user_id, is_admin, error_response) tuple."""
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
            jsonify({'message': 'Access denied: not the publication owner'}),
            403,
        )

    return publication, user_id, is_admin, None


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
        'review_status': row.review_status,
        'reviewed_by': row.reviewed_by,
        'reviewed_at': row.reviewed_at.isoformat() + 'Z' if row.reviewed_at else None,
        'review_note': row.review_note,
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


def _has_high_severity_conflict(conflicts):
    return any(c.get('severity') == 'high' for c in conflicts)


@enrichment_bp.route('/<int:publication_id>/enrich/openalex', methods=['POST'])
@jwt_required()
def run_openalex_enrichment(publication_id):
    publication, user_id, _is_admin_flag, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    allow_title_fallback = request.args.get('title_fallback', '').lower() in ('1', 'true', 'yes')

    if not normalize_doi(publication.doi or '') and not allow_title_fallback:
        return jsonify({
            'status': 'skipped',
            'reason': 'no_valid_doi',
            'message': 'Publication has no valid DOI. Re-run with ?title_fallback=1 to opt into title search (requires curator review).',
        }), 400

    client, mapper = _build_client()
    performed_by = f'user:{user_id}'

    try:
        status, error_message, payload = fetch_openalex_candidate(
            publication, client, mapper,
            performed_by=performed_by,
            allow_title_fallback=allow_title_fallback,
        )
    except Exception as enrichment_error:
        db.session.rollback()
        logger.exception('OpenAlex enrichment failed for publication %s', publication_id)
        return jsonify({
            'status': 'error',
            'message': str(enrichment_error),
        }), 502

    # Decide auto-accept vs pending_review BEFORE any Publication mutation
    review_status = None
    conflicts = []
    if status == 'enriched' and payload:
        summary = mapper.extract_work_summary(payload['work'])
        conflicts = _build_conflicts(publication, summary)
        match_method = payload.get('match_method')
        if match_method == 'doi' and not _has_high_severity_conflict(conflicts):
            review_status = 'accepted'
            # Stamp provenance status to match
            payload['provenance']['status'] = 'accepted'
            apply_openalex_enrichment_to_publication(publication, payload)
        else:
            review_status = 'pending_review'
            payload['provenance']['status'] = 'pending_review'

    # Upsert PublicationEnrichment row (respects uq_publication_source_enrichment)
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
    if review_status:
        row.review_status = review_status
        if review_status == 'accepted':
            row.reviewed_by = user_id
            row.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)

    try:
        db.session.commit()
    except Exception as commit_error:
        db.session.rollback()
        logger.exception('Failed to commit enrichment row for publication %s', publication_id)
        return jsonify({'status': 'error', 'message': str(commit_error)}), 500

    response_body = {
        'status': status,
        'review_status': review_status,
        'publication_id': publication.id,
        'openalex_id': publication.openalex_id if review_status == 'accepted' else None,
        'provenance': payload.get('provenance') if payload else None,
        'enrichment': payload.get('enrichment') if payload else None,
        'conflicts': conflicts,
        'match_method': payload.get('match_method') if payload else None,
    }
    if error_message:
        response_body['reason'] = error_message
    return jsonify(response_body), 200


@enrichment_bp.route('/<int:publication_id>/enrich/openalex/accept', methods=['POST'])
@jwt_required()
def accept_openalex_enrichment(publication_id):
    """Curator (owner or admin) accepts a pending OpenAlex candidate: apply to Publication."""
    publication, user_id, _is_admin_flag, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex'
    ).first()
    if not row or row.status != 'enriched' or not row.raw_response:
        return jsonify({'message': 'No enriched OpenAlex candidate to accept'}), 404
    if row.review_status == 'accepted':
        return jsonify({'message': 'Already accepted', 'review_status': 'accepted'}), 200
    if row.review_status == 'rejected':
        return jsonify({'message': 'Candidate was rejected — re-run POST /enrich/openalex first'}), 409

    payload = row.raw_response or {}
    apply_openalex_enrichment_to_publication(publication, payload)

    note = (request.get_json(silent=True) or {}).get('review_note') if request.is_json else None
    row.review_status = 'accepted'
    row.reviewed_by = user_id
    row.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    row.review_note = note
    # Reflect decision inside provenance for the audit trail
    if isinstance(payload, dict) and isinstance(payload.get('provenance'), dict):
        payload['provenance']['status'] = 'accepted'
        payload['provenance']['reviewedBy'] = f'user:{user_id}'
        row.raw_response = payload

    try:
        db.session.commit()
    except Exception as commit_error:
        db.session.rollback()
        logger.exception('Failed to commit accept for publication %s', publication_id)
        return jsonify({'message': str(commit_error)}), 500

    return jsonify({
        'status': 'accepted',
        'publication_id': publication.id,
        'openalex_id': publication.openalex_id,
        'reviewed_by': user_id,
        'reviewed_at': row.reviewed_at.isoformat() + 'Z',
    }), 200


@enrichment_bp.route('/<int:publication_id>/enrich/openalex/reject', methods=['POST'])
@jwt_required()
def reject_openalex_enrichment(publication_id):
    """Curator rejects a pending OpenAlex candidate. Publication fields are NOT touched."""
    publication, user_id, _is_admin_flag, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex'
    ).first()
    if not row:
        return jsonify({'message': 'No enrichment row to reject'}), 404
    if row.review_status == 'rejected':
        return jsonify({'message': 'Already rejected', 'review_status': 'rejected'}), 200

    note = (request.get_json(silent=True) or {}).get('review_note') if request.is_json else None
    row.review_status = 'rejected'
    row.reviewed_by = user_id
    row.reviewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    row.review_note = note
    payload = row.raw_response
    if isinstance(payload, dict) and isinstance(payload.get('provenance'), dict):
        payload['provenance']['status'] = 'rejected'
        payload['provenance']['reviewedBy'] = f'user:{user_id}'
        row.raw_response = payload

    try:
        db.session.commit()
    except Exception as commit_error:
        db.session.rollback()
        logger.exception('Failed to commit reject for publication %s', publication_id)
        return jsonify({'message': str(commit_error)}), 500

    return jsonify({
        'status': 'rejected',
        'publication_id': publication.id,
        'reviewed_by': user_id,
        'reviewed_at': row.reviewed_at.isoformat() + 'Z',
    }), 200


@enrichment_bp.route('/<int:publication_id>/enrich/openalex/preview', methods=['GET'])
@jwt_required()
def preview_openalex_enrichment(publication_id):
    publication, _user_id, _is_admin_flag, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    allow_title_fallback = request.args.get('title_fallback', '').lower() in ('1', 'true', 'yes')
    normalized_doi = normalize_doi(publication.doi or '')

    if not normalized_doi and not allow_title_fallback:
        return jsonify({
            'status': 'skipped',
            'reason': 'no_valid_doi',
            'message': 'Publication has no valid DOI. Re-run with ?title_fallback=1 for title-based preview.',
        }), 400

    client, mapper = _build_client()
    work_data = None
    match_method = None
    if normalized_doi:
        work_data = client.get_work_by_doi(normalized_doi)
        if work_data:
            match_method = 'doi'
    if not work_data and allow_title_fallback and publication.document_title:
        candidates = client.search_work_by_title(publication.document_title, per_page=1)
        if candidates:
            work_data = candidates[0]
            match_method = 'title_search'

    if not work_data:
        return jsonify({'status': 'not_found', 'doi': normalized_doi}), 404

    enrichment_data = mapper.extract_work_enrichment(work_data)
    summary = mapper.extract_work_summary(work_data)
    conflicts = _build_conflicts(publication, summary)

    return jsonify({
        'status': 'preview',
        'publication_id': publication.id,
        'match_method': match_method,
        'enrichment': enrichment_data,
        'summary': summary,
        'conflicts': conflicts,
    }), 200


@enrichment_bp.route('/<int:publication_id>/jsonld', methods=['GET'])
def publication_jsonld(publication_id):
    """
    Public schema.org/ScholarlyArticle JSON-LD for a publication.

    Returns application/ld+json. Designed to be embedded as
    ``<script type="application/ld+json">`` on the Next.js landing page or
    consumed directly by structured-data crawlers (Google Scholar, etc.).

    Includes OpenAlex Work URL under ``sameAs`` only when an OpenAlex
    enrichment row exists with status='enriched' and review_status='accepted'
    (NULL review_status counts as accepted for Phase 1 backfilled rows).
    """
    publication = Publications.query.filter_by(id=publication_id).first()
    if not publication:
        return jsonify({'message': 'Publication not found'}), 404

    same_as = []
    if publication.doi:
        same_as.append(f'https://doi.org/{normalize_doi(publication.doi) or publication.doi}')

    accepted = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex', status='enriched'
    ).filter(
        (PublicationEnrichment.review_status == 'accepted')
        | (PublicationEnrichment.review_status.is_(None))
    ).first()
    if accepted and publication.openalex_id:
        oid = publication.openalex_id
        same_as.append(oid if oid.startswith('http') else f'https://openalex.org/{oid}')

    creators_list = []
    if getattr(publication, 'publication_creators', None):
        for creator in publication.publication_creators:
            name = (
                getattr(creator, 'family_name', None)
                or getattr(creator, 'given_name', None)
                or getattr(creator, 'creator_name', None)
            )
            if not name:
                continue
            author = {'@type': 'Person', 'name': name}
            identifier = getattr(creator, 'identifier', None)
            if identifier:
                author['sameAs'] = identifier
            creators_list.append(author)

    keywords = []
    if accepted and publication.openalex_topics:
        keywords = [t.get('name') for t in publication.openalex_topics if isinstance(t, dict) and t.get('name')]

    jsonld = {
        '@context': 'https://schema.org',
        '@type': 'ScholarlyArticle',
        '@id': f'https://docid.africapidalliance.org/docid/{publication.document_docid}'
                if publication.document_docid else None,
        'name': publication.document_title,
        'headline': publication.document_title,
        'description': (publication.document_description or '')[:5000] or None,
        'identifier': publication.doi,
        'sameAs': same_as or None,
        'author': creators_list or None,
        'datePublished': publication.published.isoformat() if publication.published else None,
        'abstract': publication.abstract_text or None,
        'keywords': ', '.join(keywords) if keywords else None,
        'citation': publication.citation_count,
    }
    if accepted and publication.open_access_status:
        jsonld['isAccessibleForFree'] = publication.open_access_status not in ('closed',)

    jsonld_clean = {k: v for k, v in jsonld.items() if v not in (None, '', [])}

    return current_app.response_class(
        response=jsonify(jsonld_clean).get_data(),
        status=200,
        mimetype='application/ld+json',
    )


@enrichment_bp.route('/<int:publication_id>/enrich/openalex', methods=['GET'])
@jwt_required()
def get_openalex_enrichment(publication_id):
    publication, _user_id, _is_admin_flag, error_response = _authorise(publication_id)
    if error_response:
        return error_response

    row = PublicationEnrichment.query.filter_by(
        publication_id=publication.id, source_name='openalex'
    ).first()
    if not row:
        return jsonify({'status': 'none', 'publication_id': publication.id}), 404

    return jsonify(_serialise_enrichment_row(row)), 200
