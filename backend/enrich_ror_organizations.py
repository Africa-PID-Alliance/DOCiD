#!/usr/bin/env python3
"""
Enrich DSpace-synced publications with ROR organization data.

Finds publications that have an `owner` field set (from DSpace sync) but no
corresponding PublicationOrganization record, looks up the institution via
the ROR API, and creates organization records with resolved ROR IDs.

Usage:
    python3 enrich_ror_organizations.py              # Run enrichment
    python3 enrich_ror_organizations.py --dry-run     # Preview without committing

Safe to re-run: skips publications that already have organization records.
"""

import os
import sys
import logging
import argparse

import requests

# Add backend directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Publications, PublicationOrganization

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

ROR_API_BASE_URL = "https://api.ror.org/organizations"


def search_ror_by_name(institution_name):
    """
    Search the ROR API for an institution by name.
    Returns the best match with ror_id, display name, and country.
    """
    try:
        response = requests.get(
            ROR_API_BASE_URL,
            params={"query": institution_name},
            timeout=15
        )
        if response.status_code != 200:
            logger.error(f"ROR API returned {response.status_code} for '{institution_name}'")
            return None

        data = response.json()
        items = data.get("items", [])
        if not items:
            logger.warning(f"No ROR results for '{institution_name}'")
            return None

        first_result = items[0]

        # Check confidence — ROR API includes a score; skip low-confidence matches
        match_score = first_result.get("score", 0)
        if match_score < 1.0:
            logger.warning(
                f"Low-confidence ROR match (score={match_score}) for '{institution_name}', skipping"
            )
            return None

        # Extract ROR ID from full URL (e.g., "https://ror.org/05bk57929" -> "05bk57929")
        ror_url = first_result.get("id", "")
        ror_id = ror_url.split("/")[-1] if ror_url else None

        # Extract display name (prefer ror_display type)
        display_name = None
        names_list = first_result.get("names", [])
        for name_entry in names_list:
            if "ror_display" in name_entry.get("types", []):
                display_name = name_entry.get("value")
                break
        if not display_name and names_list:
            display_name = names_list[0].get("value", institution_name)

        # Extract country from locations
        country_name = None
        locations = first_result.get("locations", [])
        if locations and locations[0].get("geonames_details"):
            country_name = locations[0]["geonames_details"].get("country_name")

        logger.info(
            f"ROR match for '{institution_name}': "
            f"{display_name} (ROR: {ror_id}, Country: {country_name})"
        )

        return {
            "ror_id": ror_id,
            "name": display_name,
            "country": country_name,
            "ror_url": ror_url,
        }

    except requests.exceptions.RequestException as request_error:
        logger.error(f"ROR API request failed for '{institution_name}': {request_error}")
        return None


def enrich_organizations(dry_run=False):
    """
    Find publications without organization records and add ROR data.
    Groups by unique owner name to minimize ROR API calls.
    """
    # Find publications with owner set but no organization record
    existing_organization_publication_ids = (
        db.session.query(PublicationOrganization.publication_id)
        .distinct()
    )

    publications_without_organizations = Publications.query.filter(
        Publications.owner.isnot(None),
        Publications.owner != '',
        ~Publications.id.in_(existing_organization_publication_ids)
    ).all()

    total_publications = len(publications_without_organizations)
    if total_publications == 0:
        logger.info("No publications need organization enrichment")
        return 0

    logger.info(f"Found {total_publications} publications without organization records")

    # Skip generic/default owner names that won't resolve to real institutions
    generic_owner_names = {'DSpace Repository', 'DSpace Legacy Repository', 'System', ''}

    # Group by owner name for efficient ROR lookups
    publications_by_owner = {}
    for publication in publications_without_organizations:
        owner_name = publication.owner.strip()
        if owner_name in generic_owner_names:
            continue
        publications_by_owner.setdefault(owner_name, []).append(publication)

    logger.info(f"Unique institution names to resolve: {len(publications_by_owner)}")

    # Resolve each unique owner via ROR API
    ror_lookup_cache = {}
    for owner_name in publications_by_owner:
        ror_data = search_ror_by_name(owner_name)
        ror_lookup_cache[owner_name] = ror_data

    # Create organization records
    created_count = 0
    skipped_count = 0

    for owner_name, owner_publications in publications_by_owner.items():
        ror_data = ror_lookup_cache.get(owner_name)
        if not ror_data or not ror_data.get("ror_id"):
            logger.warning(
                f"No ROR match for '{owner_name}', "
                f"skipping {len(owner_publications)} publications"
            )
            skipped_count += len(owner_publications)
            continue

        resolvable_identifier = f"https://ror.org/{ror_data['ror_id']}"

        for publication in owner_publications:
            organization_record = PublicationOrganization(
                publication_id=publication.id,
                name=ror_data["name"],
                type="ROR",
                other_name=owner_name if owner_name != ror_data["name"] else None,
                identifier=resolvable_identifier,
                identifier_type="ror",
                country=ror_data.get("country") or "",
            )
            db.session.add(organization_record)
            created_count += 1

    if dry_run:
        db.session.rollback()
        logger.info(f"[DRY RUN] Would create {created_count} organization records, skipped {skipped_count}")
    else:
        try:
            db.session.commit()
            logger.info(f"Created {created_count} organization records, skipped {skipped_count}")
        except Exception as commit_error:
            db.session.rollback()
            logger.error(f"Commit failed, all changes rolled back: {commit_error}")
            return 0

    return created_count


def main():
    parser = argparse.ArgumentParser(
        description="Enrich DSpace-synced publications with ROR organization data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without committing to the database"
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        created_count = enrich_organizations(dry_run=args.dry_run)
        print(f"\nDone. {'[DRY RUN] ' if args.dry_run else ''}Organizations enriched: {created_count}")


if __name__ == "__main__":
    main()
