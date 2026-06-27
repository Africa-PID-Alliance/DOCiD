#!/usr/bin/env python3
"""
Metadata Enrichment Orchestrator for DOCiD Publications.

Enriches publications with metadata from external APIs.
Active providers are controlled by the ENRICHMENT_SOURCES env var (see config.py).

Usage:
    python3 enrich_metadata.py --source openalex --batch-size 10
    python3 enrich_metadata.py --source all --batch-size 5 --dry-run
    python3 enrich_metadata.py --source unpaywall --limit 50
    python3 enrich_metadata.py --source all --force-reprocess

Safe to re-run: skips publications already in a terminal status for each source.
Terminal statuses: enriched | not_found | skipped | auth_error
Retryable statuses: transient_error | quota_exhausted | malformed_response
"""

import os
import sys
import logging
import argparse
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications, PublicationEnrichment, EnrichmentRun

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Statuses that mean "don't try again" — retryable statuses are NOT in this set.
_TERMINAL_STATUSES = ('enriched', 'not_found', 'skipped', 'auth_error')


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_publications_to_enrich(source_name, batch_size, force_reprocess=False, require_doi=True):
    """
    Return publications that still need enrichment from source_name.
    force_reprocess deletes existing rows so the whole batch re-runs.
    """
    if force_reprocess:
        PublicationEnrichment.query.filter_by(source_name=source_name).delete()
        db.session.flush()

    already_done_ids = (
        db.session.query(PublicationEnrichment.publication_id)
        .filter(
            PublicationEnrichment.source_name == source_name,
            PublicationEnrichment.status.in_(_TERMINAL_STATUSES),
        )
        .distinct()
    )

    query = Publications.query.filter(~Publications.id.in_(already_done_ids))

    if require_doi:
        query = query.filter(
            Publications.doi.isnot(None),
            Publications.doi != '',
        )

    return query.order_by(Publications.id.asc()).limit(batch_size).all()


def _upsert_external_edges(publication_id: int, edges: list) -> int:
    """Upsert edge dicts into publication_external_edges; returns count."""
    if not edges:
        return 0
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from app.models import PublicationExternalEdge
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


# ---------------------------------------------------------------------------
# Legacy per-provider enrich functions (openalex / unpaywall / semantic_scholar / openaire)
# These call the old mapper APIs directly for backward compatibility.
# ---------------------------------------------------------------------------

def enrich_with_openalex(publication, client, mapper):
    from app.service_openalex import enrich_publication_openalex
    return enrich_publication_openalex(publication, client, mapper, performed_by='system')


def enrich_with_unpaywall(publication, client, mapper):
    from app.service_openalex import normalize_doi
    normalized_doi = normalize_doi(publication.doi)
    if not normalized_doi:
        return 'skipped', 'no_valid_doi', None
    oa_data = client.get_oa_status(normalized_doi)
    if not oa_data:
        return 'not_found', None, None
    enrichment_data = mapper.extract_enrichment(oa_data)
    if enrichment_data.get('open_access_status'):
        publication.open_access_status = enrichment_data['open_access_status']
    if enrichment_data.get('open_access_url'):
        publication.open_access_url = enrichment_data['open_access_url']
    return 'enriched', None, oa_data


def enrich_with_semantic_scholar(publication, client, mapper):
    from app.service_openalex import normalize_doi
    normalized_doi = normalize_doi(publication.doi) if publication.doi else None
    paper_data = None
    if normalized_doi:
        paper_data = client.get_paper_by_doi(normalized_doi)
    if not paper_data and publication.document_title:
        paper_data = client.get_paper_by_title(publication.document_title)
    if not paper_data:
        return 'not_found', None, None
    enrichment_data = mapper.extract_enrichment(paper_data)
    if enrichment_data.get('influential_citation_count') is not None:
        publication.influential_citation_count = enrichment_data['influential_citation_count']
    if enrichment_data.get('semantic_scholar_id'):
        publication.semantic_scholar_id = enrichment_data['semantic_scholar_id']
    if enrichment_data.get('abstract'):
        publication.abstract_text = enrichment_data['abstract']
    if enrichment_data.get('citation_count') is not None and publication.citation_count is None:
        publication.citation_count = enrichment_data['citation_count']
    return 'enriched', None, paper_data


def enrich_with_openaire(publication, client, mapper):
    from app.service_openalex import normalize_doi
    normalized_doi = normalize_doi(publication.doi) if publication.doi else None
    if not normalized_doi:
        return 'skipped', 'no_valid_doi', None
    publication_data = client.search_by_doi(normalized_doi)
    projects_data = client.get_projects_for_doi(normalized_doi)
    if not publication_data and not projects_data:
        return 'not_found', None, None
    enrichment_data = mapper.extract_enrichment(publication_data, projects_data)
    if enrichment_data.get('openaire_id'):
        publication.openaire_id = enrichment_data['openaire_id']
    return 'enriched', None, {'publication': publication_data, 'projects': projects_data}


# ---------------------------------------------------------------------------
# Generic enrich function for Wave 1-4 providers
# Uses fetch_*_candidate + apply_* pattern, with edge persistence.
# ---------------------------------------------------------------------------

def enrich_with_generic_source(source_name, publication, client, mapper):
    """
    Dispatch to fetch_<source>_candidate (or fetch_opencitations_edges),
    auto-apply on DOI match, and persist edges if any.
    Returns (status, error_message, payload).
    """
    from app.service_registry import get_service

    service_module = get_service(source_name)

    # opencitations has a different fetch function name — edges only, no column mutations
    if source_name == 'opencitations':
        fetch_fn = getattr(service_module, 'fetch_opencitations_edges')
        status, error_message, payload = fetch_fn(
            publication, client, mapper, performed_by='system'
        )
    else:
        fetch_fn = getattr(service_module, f'fetch_{source_name}_candidate')
        status, error_message, payload = fetch_fn(
            publication, client, mapper, performed_by='system', allow_title_fallback=False
        )

    if status == 'enriched' and payload:
        # Auto-apply on DOI match (same rule as the route layer)
        match_method = payload.get('match_method')
        is_auto_accept = match_method == 'doi' and source_name != 'opencitations'

        if is_auto_accept:
            snap_fn = getattr(service_module, f'snapshot_publication_{source_name}_fields', None)
            if snap_fn:
                payload['pre_apply_snapshot'] = snap_fn(publication)
            apply_fn = getattr(service_module, f'apply_{source_name}_enrichment_to_publication', None)
            if apply_fn:
                apply_fn(publication, payload)

        # Persist edges (idempotent — on_conflict_do_update)
        edges = payload.get('edges') or []
        if edges:
            try:
                n = _upsert_external_edges(publication.id, edges)
                logger.debug("[%s] pub_id=%s — upserted %d edge(s)", source_name, publication.id, n)
            except Exception as exc:
                logger.warning("[%s] Edge upsert failed (non-fatal): %s", source_name, exc)

    return status, error_message, payload


# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

SOURCE_REGISTRY = {
    # Legacy providers — use their own inline enrich functions
    'openalex': {
        'enrich_function': enrich_with_openalex,
        'require_doi': True,
    },
    'unpaywall': {
        'enrich_function': enrich_with_unpaywall,
        'require_doi': True,
    },
    'semantic_scholar': {
        'enrich_function': enrich_with_semantic_scholar,
        'require_doi': False,
    },
    'openaire': {
        'enrich_function': enrich_with_openaire,
        'require_doi': True,
    },
    # Wave 1 providers — use generic fetch/apply pattern
    'core': {
        'enrich_function': lambda pub, client, mapper: enrich_with_generic_source('core', pub, client, mapper),
        'require_doi': True,
    },
    'opencitations': {
        'enrich_function': lambda pub, client, mapper: enrich_with_generic_source('opencitations', pub, client, mapper),
        'require_doi': True,
    },
    # Wave 2
    'lens_org': {
        'enrich_function': lambda pub, client, mapper: enrich_with_generic_source('lens_org', pub, client, mapper),
        'require_doi': True,
    },
    # Wave 4
    'base': {
        'enrich_function': lambda pub, client, mapper: enrich_with_generic_source('base', pub, client, mapper),
        'require_doi': False,
    },
    'worldcat': {
        'enrich_function': lambda pub, client, mapper: enrich_with_generic_source('worldcat', pub, client, mapper),
        'require_doi': False,
    },
}


def create_client_and_mapper(source_name, app_config):
    """Return (client, mapper) for source_name using app config values."""
    if source_name == 'openalex':
        from app.service_openalex import OpenAlexClient, OpenAlexEnrichmentMapper
        return OpenAlexClient(app_config.get('OPENALEX_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')), OpenAlexEnrichmentMapper

    if source_name == 'unpaywall':
        from app.service_unpaywall import UnpaywallClient, UnpaywallEnrichmentMapper
        return UnpaywallClient(app_config.get('UNPAYWALL_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')), UnpaywallEnrichmentMapper

    if source_name == 'semantic_scholar':
        from app.service_semantic_scholar import SemanticScholarClient, SemanticScholarEnrichmentMapper
        return SemanticScholarClient(api_key=app_config.get('SEMANTIC_SCHOLAR_API_KEY') or None), SemanticScholarEnrichmentMapper

    if source_name == 'openaire':
        from app.service_openaire import OpenAIREClient, OpenAIREEnrichmentMapper
        return OpenAIREClient(base_url=app_config.get('OPENAIRE_API_BASE_URL', 'https://graph.openaire.eu/api')), OpenAIREEnrichmentMapper

    if source_name == 'core':
        from app.service_core import CoreClient, CoreEnrichmentMapper
        api_key = app_config.get('CORE_API_KEY', '')
        if not api_key:
            raise ValueError("CORE_API_KEY not set — add it to .env to enable CORE enrichment")
        return CoreClient(api_key=api_key, base_url=app_config.get('CORE_API_BASE_URL', 'https://api.core.ac.uk/v3')), CoreEnrichmentMapper()

    if source_name == 'opencitations':
        from app.service_opencitations import OpenCitationsClient, OpenCitationsMapper
        return OpenCitationsClient(access_token=app_config.get('OPENCITATIONS_ACCESS_TOKEN', '')), OpenCitationsMapper()

    if source_name == 'lens_org':
        from app.service_lens import LensClient, LensEnrichmentMapper
        return LensClient(
            scholar_api_key=app_config.get('LENS_SCHOLAR_API_KEY', ''),
            patent_api_key=app_config.get('LENS_PATENT_API_KEY', ''),
            base_url=app_config.get('LENS_API_BASE_URL', 'https://api.lens.org'),
        ), LensEnrichmentMapper()

    if source_name == 'base':
        from app.service_base import BaseSearchClient, BaseEnrichmentMapper
        api_key = app_config.get('BASE_API_KEY', '')
        if not api_key:
            raise ValueError("BASE_API_KEY not set — add it to .env to enable BASE enrichment")
        return BaseSearchClient(api_key=api_key, base_url=app_config.get('BASE_API_BASE_URL', 'https://api.base-search.net/cgi-bin/BaseHttpSearchInterface.fcgi')), BaseEnrichmentMapper()

    if source_name == 'worldcat':
        from app.service_worldcat import WorldCatClient, WorldCatEnrichmentMapper
        client_id = app_config.get('WORLDCAT_CLIENT_ID', '')
        client_secret = app_config.get('WORLDCAT_CLIENT_SECRET', '')
        if not client_id or not client_secret:
            raise ValueError("WORLDCAT_CLIENT_ID and WORLDCAT_CLIENT_SECRET not set — add them to .env")
        return WorldCatClient(
            client_id=client_id,
            client_secret=client_secret,
            search_base_url=app_config.get('WORLDCAT_SEARCH_BASE_URL', 'https://americas.discovery.api.oclc.org/worldcat/search/v2'),
            metadata_base_url=app_config.get('WORLDCAT_METADATA_BASE_URL', 'https://metadata.api.oclc.org'),
        ), WorldCatEnrichmentMapper()

    raise ValueError(f"Unknown source: {source_name!r}")


# ---------------------------------------------------------------------------
# Main enrichment loop
# ---------------------------------------------------------------------------

def enrich_publications(source_name, batch_size=100, dry_run=False, force_reprocess=False, limit=None):
    """Enrich publications from source_name. Returns a results dict with counts."""
    from flask import current_app

    source_config = SOURCE_REGISTRY.get(source_name)
    if not source_config:
        logger.error("Source %r is not in SOURCE_REGISTRY", source_name)
        return {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}

    enrich_function = source_config['enrich_function']
    require_doi = source_config['require_doi']

    try:
        client, mapper = create_client_and_mapper(source_name, current_app.config)
    except ValueError as exc:
        logger.error("[%s] Cannot start: %s", source_name, exc)
        return {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}

    effective_batch_size = limit if limit else batch_size
    publications = get_publications_to_enrich(source_name, effective_batch_size, force_reprocess, require_doi)
    total = len(publications)

    if total == 0:
        logger.info("[%s] No publications need enrichment", source_name)
        return {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}

    logger.info("[%s] Found %d publications to enrich", source_name, total)

    enrichment_run = EnrichmentRun(
        run_type='enrich',
        source_name=source_name,
        status='running',
        started_at=datetime.utcnow(),
    )
    if not dry_run:
        db.session.add(enrichment_run)
        db.session.flush()

    results = {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}
    _STATUS_ICON = {'enriched': '+', 'not_found': '-', 'skipped': '~', 'auth_error': '🔑',
                    'transient_error': '⚠', 'quota_exhausted': '⏸', 'malformed_response': '?'}

    for idx, publication in enumerate(publications, 1):
        savepoint = db.session.begin_nested()
        try:
            status, error_message, raw_response = enrich_function(publication, client, mapper)

            enrichment_record = PublicationEnrichment(
                publication_id=publication.id,
                source_name=source_name,
                status=status,
                enriched_at=datetime.utcnow() if status == 'enriched' else None,
                error_message=error_message,
                raw_response=raw_response if status == 'enriched' else None,
            )
            db.session.add(enrichment_record)
            savepoint.commit()

            results[status] = results.get(status, 0) + 1
            results['processed'] += 1

            logger.info(
                "[%s] [%d/%d] %s pub_id=%s doi=%s → %s",
                source_name, idx, total,
                _STATUS_ICON.get(status, '?'),
                publication.id,
                publication.doi or 'N/A',
                status,
            )

            # Stop the batch early on auth_error — no point retrying every record
            if status == 'auth_error':
                logger.error("[%s] auth_error — stopping batch. Fix the API key and retry.", source_name)
                break

        except Exception as exc:
            try:
                savepoint.rollback()
            except Exception:
                db.session.rollback()
            results['errors'] += 1
            results['processed'] += 1
            logger.error("[%s] Error enriching pub_id=%s: %s", source_name, publication.id, exc)

    if not dry_run:
        enrichment_run.status = 'completed'
        enrichment_run.completed_at = datetime.utcnow()
        enrichment_run.publications_processed = results['processed']
        enrichment_run.publications_enriched = results['enriched']
        enrichment_run.publications_skipped = results.get('skipped', 0) + results.get('not_found', 0)
        enrichment_run.publications_failed = results['errors']
        if publications:
            enrichment_run.last_processed_publication_id = publications[-1].id

    if dry_run:
        db.session.rollback()
        logger.info("[%s] [DRY RUN] enriched=%d not_found=%d skipped=%d errors=%d",
                    source_name, results['enriched'], results['not_found'], results['skipped'], results['errors'])
    else:
        try:
            db.session.commit()
            logger.info("[%s] Committed: enriched=%d not_found=%d skipped=%d errors=%d",
                        source_name, results['enriched'], results['not_found'], results['skipped'], results['errors'])
        except Exception as exc:
            db.session.rollback()
            logger.error("[%s] Commit failed: %s", source_name, exc)

    return results


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    # We need the app context to read ENRICHMENT_SOURCES from config,
    # but argparse runs before the app is created. Accept 'all' or any
    # known source name — validate against SOURCE_REGISTRY at runtime.
    all_known_sources = list(SOURCE_REGISTRY.keys())

    parser = argparse.ArgumentParser(
        description="Enrich DOCiD publications with metadata from external APIs"
    )
    parser.add_argument(
        "--source",
        default='all',
        help=(
            "Which enrichment source to run. "
            f"Known values: all, {', '.join(all_known_sources)}. "
            "When 'all', only sources listed in ENRICHMENT_SOURCES config are run."
        ),
    )
    parser.add_argument("--batch-size", type=int, default=100,
                        help="Publications to process per source (default: 100)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Preview without committing to the database")
    parser.add_argument("--force-reprocess", action="store_true",
                        help="Re-enrich publications already in a terminal status")
    parser.add_argument("--limit", type=int, default=None,
                        help="Maximum publications to process (overrides --batch-size)")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # Determine which sources to run
        if args.source == 'all':
            # Read the canonical list from config (controlled by ENRICHMENT_SOURCES env var)
            configured_sources = app.config.get('ENRICHMENT_SOURCES', ['openalex', 'unpaywall'])
            # Only run sources that are wired up in SOURCE_REGISTRY
            sources = [s for s in configured_sources if s in SOURCE_REGISTRY]
            unknown = [s for s in configured_sources if s not in SOURCE_REGISTRY]
            if unknown:
                logger.warning("Sources in ENRICHMENT_SOURCES but not in SOURCE_REGISTRY (skipped): %s", unknown)
        else:
            if args.source not in SOURCE_REGISTRY:
                parser.error(f"Unknown source {args.source!r}. Known: {', '.join(all_known_sources)}")
            sources = [args.source]

        all_results = {}
        for source_name in sources:
            logger.info("\n%s", '=' * 60)
            logger.info("Starting enrichment: %s", source_name)
            logger.info('%s', '=' * 60)
            all_results[source_name] = enrich_publications(
                source_name=source_name,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                force_reprocess=args.force_reprocess,
                limit=args.limit,
            )

        print(f"\n{'='*60}")
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Enrichment Summary")
        print(f"{'='*60}")
        for source_name, results in all_results.items():
            print(
                f"  {source_name:20s} | processed={results['processed']:4d} | "
                f"enriched={results['enriched']:4d} | "
                f"not_found={results.get('not_found', 0):4d} | "
                f"errors={results['errors']:4d}"
            )


if __name__ == "__main__":
    main()
