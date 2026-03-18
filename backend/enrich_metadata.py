#!/usr/bin/env python3
"""
Metadata Enrichment Orchestrator for DOCiD Publications.

Enriches publications with metadata from external APIs:
  - OpenAlex: citations, topics, OA status, author data
  - Unpaywall: definitive Open Access status and PDF links
  - Semantic Scholar: influential citations, abstracts
  - OpenAIRE: EU project/funding links

Usage:
    python3 enrich_metadata.py --source openalex --batch-size 10
    python3 enrich_metadata.py --source all --batch-size 5 --dry-run
    python3 enrich_metadata.py --source unpaywall --limit 50
    python3 enrich_metadata.py --source all --force-reprocess

Safe to re-run: skips publications already enriched by each source.
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications, PublicationEnrichment, EnrichmentRun

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Source configuration
ENRICHMENT_SOURCES = ['openalex', 'unpaywall', 'semantic_scholar', 'openaire']


def get_publications_to_enrich(source_name, batch_size, force_reprocess=False, require_doi=True):
    """
    Find publications that need enrichment from a specific source.
    Skips publications already enriched, not_found, or skipped — unless force_reprocess is True.
    """
    if force_reprocess:
        # Delete existing enrichment records for this source so they get reprocessed
        PublicationEnrichment.query.filter_by(source_name=source_name).delete()
        db.session.flush()
        already_enriched_ids = db.session.query(PublicationEnrichment.publication_id).filter(
            PublicationEnrichment.source_name == source_name
        ).distinct()
    else:
        # Skip publications with terminal statuses
        already_enriched_ids = db.session.query(PublicationEnrichment.publication_id).filter(
            PublicationEnrichment.source_name == source_name,
            PublicationEnrichment.status.in_(['enriched', 'not_found', 'skipped'])
        ).distinct()

    query = Publications.query.filter(
        ~Publications.id.in_(already_enriched_ids)
    )

    if require_doi:
        query = query.filter(
            Publications.doi.isnot(None),
            Publications.doi != ''
        )

    return query.order_by(Publications.id.asc()).limit(batch_size).all()


def enrich_with_openalex(publication, client, mapper):
    """Enrich a single publication with OpenAlex data."""
    from app.service_openalex import normalize_doi

    normalized_doi = normalize_doi(publication.doi)
    if not normalized_doi:
        return 'skipped', 'no_valid_doi', None

    work_data = client.get_work_by_doi(normalized_doi)
    if not work_data:
        return 'not_found', None, None

    enrichment_data = mapper.extract_work_enrichment(work_data)

    # Apply to publication — OpenAlex is primary for citations and topics
    if enrichment_data.get('citation_count') is not None:
        publication.citation_count = enrichment_data['citation_count']
    if enrichment_data.get('open_access_status'):
        publication.open_access_status = enrichment_data['open_access_status']
    if enrichment_data.get('open_access_url'):
        publication.open_access_url = enrichment_data['open_access_url']
    if enrichment_data.get('topics'):
        publication.openalex_topics = enrichment_data['topics']
    if enrichment_data.get('openalex_id'):
        publication.openalex_id = enrichment_data['openalex_id']
    if enrichment_data.get('abstract') and not publication.abstract_text:
        publication.abstract_text = enrichment_data['abstract']

    return 'enriched', None, work_data


def enrich_with_unpaywall(publication, client, mapper):
    """Enrich a single publication with Unpaywall OA data."""
    from app.service_openalex import normalize_doi

    normalized_doi = normalize_doi(publication.doi)
    if not normalized_doi:
        return 'skipped', 'no_valid_doi', None

    oa_data = client.get_oa_status(normalized_doi)
    if not oa_data:
        return 'not_found', None, None

    enrichment_data = mapper.extract_enrichment(oa_data)

    # Unpaywall is authoritative for OA status — always override
    if enrichment_data.get('open_access_status'):
        publication.open_access_status = enrichment_data['open_access_status']
    if enrichment_data.get('open_access_url'):
        publication.open_access_url = enrichment_data['open_access_url']

    return 'enriched', None, oa_data


def enrich_with_semantic_scholar(publication, client, mapper):
    """Enrich a single publication with Semantic Scholar data."""
    from app.service_semantic_scholar import normalize_doi

    normalized_doi = normalize_doi(publication.doi)

    paper_data = None
    if normalized_doi:
        paper_data = client.get_paper_by_doi(normalized_doi)

    # Fallback: search by title if no DOI or DOI lookup failed
    if not paper_data and publication.document_title:
        paper_data = client.get_paper_by_title(publication.document_title)

    if not paper_data:
        return 'not_found', None, None

    enrichment_data = mapper.extract_enrichment(paper_data)

    # Semantic Scholar is primary for influential citations
    if enrichment_data.get('influential_citation_count') is not None:
        publication.influential_citation_count = enrichment_data['influential_citation_count']
    if enrichment_data.get('semantic_scholar_id'):
        publication.semantic_scholar_id = enrichment_data['semantic_scholar_id']
    # Prefer Semantic Scholar abstract over OpenAlex (plain text vs reconstructed)
    if enrichment_data.get('abstract'):
        publication.abstract_text = enrichment_data['abstract']
    # Only set citation_count from S2 if OpenAlex didn't set it
    if enrichment_data.get('citation_count') is not None and publication.citation_count is None:
        publication.citation_count = enrichment_data['citation_count']

    return 'enriched', None, paper_data


def enrich_with_openaire(publication, client, mapper):
    """Enrich a single publication with OpenAIRE project/funding data."""
    from app.service_openaire import normalize_doi

    normalized_doi = normalize_doi(publication.doi)
    if not normalized_doi:
        return 'skipped', 'no_valid_doi', None

    publication_data = client.search_by_doi(normalized_doi)
    projects_data = client.get_projects_for_doi(normalized_doi)

    if not publication_data and not projects_data:
        return 'not_found', None, None

    enrichment_data = mapper.extract_enrichment(publication_data, projects_data)

    if enrichment_data.get('openaire_id'):
        publication.openaire_id = enrichment_data['openaire_id']

    # Store project data in raw_response for now (could be linked to publication_projects later)
    raw_response = {
        'publication': publication_data,
        'projects': projects_data
    }

    return 'enriched', None, raw_response


# Map source names to their enrichment functions and client/mapper factories
SOURCE_REGISTRY = {
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
        'require_doi': False,  # Can fallback to title search
    },
    'openaire': {
        'enrich_function': enrich_with_openaire,
        'require_doi': True,
    },
}


def create_client_and_mapper(source_name, app_config):
    """Create the appropriate client and mapper for a given source."""
    if source_name == 'openalex':
        from app.service_openalex import OpenAlexClient, OpenAlexEnrichmentMapper
        contact_email = app_config.get('OPENALEX_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')
        return OpenAlexClient(contact_email), OpenAlexEnrichmentMapper

    elif source_name == 'unpaywall':
        from app.service_unpaywall import UnpaywallClient, UnpaywallEnrichmentMapper
        contact_email = app_config.get('UNPAYWALL_CONTACT_EMAIL', 'admin@docid.africapidalliance.org')
        return UnpaywallClient(contact_email), UnpaywallEnrichmentMapper

    elif source_name == 'semantic_scholar':
        from app.service_semantic_scholar import SemanticScholarClient, SemanticScholarEnrichmentMapper
        api_key = app_config.get('SEMANTIC_SCHOLAR_API_KEY', '') or None
        return SemanticScholarClient(api_key=api_key), SemanticScholarEnrichmentMapper

    elif source_name == 'openaire':
        from app.service_openaire import OpenAIREClient, OpenAIREEnrichmentMapper
        return OpenAIREClient(), OpenAIREEnrichmentMapper

    else:
        raise ValueError(f"Unknown source: {source_name}")


def enrich_publications(source_name, batch_size=100, dry_run=False, force_reprocess=False, limit=None):
    """
    Main enrichment loop for a given source.
    Returns results dict with counts.
    """
    from flask import current_app

    source_config = SOURCE_REGISTRY[source_name]
    enrich_function = source_config['enrich_function']
    require_doi = source_config['require_doi']

    client, mapper = create_client_and_mapper(source_name, current_app.config)

    effective_batch_size = limit if limit else batch_size

    publications = get_publications_to_enrich(
        source_name, effective_batch_size, force_reprocess, require_doi
    )

    total_publications = len(publications)
    if total_publications == 0:
        logger.info(f"[{source_name}] No publications need enrichment")
        return {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}

    logger.info(f"[{source_name}] Found {total_publications} publications to enrich")

    # Create enrichment run record
    enrichment_run = EnrichmentRun(
        run_type='enrich',
        source_name=source_name,
        status='running',
        started_at=datetime.utcnow()
    )
    if not dry_run:
        db.session.add(enrichment_run)
        db.session.flush()

    results = {'processed': 0, 'enriched': 0, 'not_found': 0, 'skipped': 0, 'errors': 0}

    for idx, publication in enumerate(publications, 1):
        savepoint = db.session.begin_nested()
        try:
            status, error_message, raw_response = enrich_function(publication, client, mapper)

            # Create enrichment tracking record
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

            status_icon = {'enriched': '+', 'not_found': '-', 'skipped': '~', 'error': '!'}
            logger.info(
                f"[{source_name}] [{idx}/{total_publications}] "
                f"{status_icon.get(status, '?')} pub_id={publication.id} "
                f"doi={publication.doi or 'N/A'} → {status}"
            )

        except Exception as enrichment_error:
            try:
                savepoint.rollback()
            except Exception:
                db.session.rollback()

            results['errors'] += 1
            results['processed'] += 1
            logger.error(f"[{source_name}] Error enriching pub_id={publication.id}: {enrichment_error}")

    # Update enrichment run
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
        logger.info(f"[{source_name}] [DRY RUN] Would enrich {results['enriched']}, "
                     f"not_found={results['not_found']}, skipped={results['skipped']}, errors={results['errors']}")
    else:
        try:
            db.session.commit()
            logger.info(f"[{source_name}] Committed: enriched={results['enriched']}, "
                         f"not_found={results['not_found']}, skipped={results['skipped']}, errors={results['errors']}")
        except Exception as commit_error:
            db.session.rollback()
            logger.error(f"[{source_name}] Commit failed: {commit_error}")

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Enrich DOCiD publications with metadata from external APIs"
    )
    parser.add_argument(
        "--source",
        choices=ENRICHMENT_SOURCES + ['all'],
        default='all',
        help="Which enrichment source to use (default: all)"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of publications to process per source (default: 100)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to the database"
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Re-enrich publications even if already processed"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum total publications to process (overrides batch-size)"
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        sources = ENRICHMENT_SOURCES if args.source == 'all' else [args.source]

        all_results = {}
        for source_name in sources:
            logger.info(f"\n{'='*60}")
            logger.info(f"Starting enrichment: {source_name}")
            logger.info(f"{'='*60}")

            results = enrich_publications(
                source_name=source_name,
                batch_size=args.batch_size,
                dry_run=args.dry_run,
                force_reprocess=args.force_reprocess,
                limit=args.limit,
            )
            all_results[source_name] = results

        # Print summary
        print(f"\n{'='*60}")
        print(f"{'[DRY RUN] ' if args.dry_run else ''}Enrichment Summary")
        print(f"{'='*60}")
        for source_name, results in all_results.items():
            print(f"  {source_name:20s} | processed={results['processed']:4d} | "
                  f"enriched={results['enriched']:4d} | "
                  f"not_found={results['not_found']:4d} | "
                  f"errors={results['errors']:4d}")


if __name__ == "__main__":
    main()
