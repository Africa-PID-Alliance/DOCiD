#!/usr/bin/env python3
"""
Seed harvest_sources and harvest_source_field_mappings tables
with initial university repository connections.

Usage:
    python3 seed_harvest_sources.py
    python3 seed_harvest_sources.py --dry-run

Safe to re-run: skips sources that already exist (by name).
"""

import os
import sys
import logging
import argparse

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import HarvestSource, HarvestSourceFieldMapping
from app.utils_crypto import encrypt_value

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Default Dublin Core field mappings (used by most DSpace instances)
DEFAULT_FIELD_MAPPINGS = [
    {'docid_field': 'document_title', 'source_field': 'dc.title', 'priority': 0},
    {'docid_field': 'document_description', 'source_field': 'dc.description.abstract', 'priority': 1},
    {'docid_field': 'document_description', 'source_field': 'dc.description', 'priority': 0},
    {'docid_field': 'authors', 'source_field': 'dc.contributor.author', 'priority': 0},
    {'docid_field': 'published_date', 'source_field': 'dc.date.issued', 'priority': 0},
    {'docid_field': 'resource_type', 'source_field': 'dc.type', 'priority': 0},
    {'docid_field': 'language', 'source_field': 'dc.language.iso', 'priority': 0},
    {'docid_field': 'doi', 'source_field': 'dc.identifier.doi', 'priority': 0},
    {'docid_field': 'handle', 'source_field': 'dc.identifier.uri', 'priority': 0},
    {'docid_field': 'publisher', 'source_field': 'dc.publisher', 'priority': 0},
]

SOURCES = [
    {
        'name': 'Stellenbosch University',
        'base_url': 'https://digital.lib.sun.ac.za',
        'dspace_version': '6.3',
        'api_type': 'legacy',
        'auth_required': True,
        'username': 'data@tcc-africa.org',
        'password': 'docid',
        'owner_name': 'Stellenbosch University',
        'harvest_frequency': 'weekly',
        'extra_mappings': [],  # Uses defaults only
    },
    {
        'name': 'University of Lagos',
        'base_url': 'https://api-ir.unilag.edu.ng/server',
        'ui_base_url': 'https://ir.unilag.edu.ng',
        'dspace_version': '9.1',
        'api_type': 'modern',
        'auth_required': False,
        'username': None,
        'password': None,
        'owner_name': 'University of Lagos',
        'harvest_frequency': 'daily',
        'extra_mappings': [
            # UNILAG stores DOIs in dc.identifier.other (non-standard)
            {'docid_field': 'doi', 'source_field': 'dc.identifier.other', 'priority': 1},
        ],
    },
]


def seed_sources(dry_run=False):
    """Seed harvest sources and field mappings."""
    from flask import current_app
    secret_key = current_app.config.get('SECRET_KEY', '')

    if not secret_key:
        logger.error("SECRET_KEY not configured — cannot encrypt credentials")
        return

    created_count = 0
    skipped_count = 0

    for source_config in SOURCES:
        existing_source = HarvestSource.query.filter_by(name=source_config['name']).first()
        if existing_source:
            logger.info(f"Source already exists: {source_config['name']} (id={existing_source.id}), skipping")
            skipped_count += 1
            continue

        # Encrypt credentials if provided
        encrypted_username = None
        encrypted_password = None
        if source_config.get('username'):
            encrypted_username = encrypt_value(source_config['username'], secret_key)
        if source_config.get('password'):
            encrypted_password = encrypt_value(source_config['password'], secret_key)

        harvest_source = HarvestSource(
            name=source_config['name'],
            base_url=source_config['base_url'],
            ui_base_url=source_config.get('ui_base_url'),
            dspace_version=source_config.get('dspace_version'),
            api_type=source_config['api_type'],
            auth_required=source_config.get('auth_required', False),
            encrypted_username=encrypted_username,
            encrypted_password=encrypted_password,
            owner_name=source_config['owner_name'],
            harvest_frequency=source_config.get('harvest_frequency', 'weekly'),
            is_active=True,
        )
        db.session.add(harvest_source)
        db.session.flush()  # Get the ID for field mappings

        # Add default field mappings
        all_mappings = DEFAULT_FIELD_MAPPINGS + source_config.get('extra_mappings', [])
        for mapping_config in all_mappings:
            field_mapping = HarvestSourceFieldMapping(
                harvest_source_id=harvest_source.id,
                docid_field=mapping_config['docid_field'],
                source_field=mapping_config['source_field'],
                priority=mapping_config.get('priority', 0),
            )
            db.session.add(field_mapping)

        logger.info(
            f"Created source: {source_config['name']} "
            f"(api_type={source_config['api_type']}, "
            f"auth={source_config.get('auth_required', False)}, "
            f"mappings={len(all_mappings)})"
        )
        created_count += 1

    if dry_run:
        db.session.rollback()
        logger.info(f"[DRY RUN] Would create {created_count} sources, skipped {skipped_count}")
    else:
        try:
            db.session.commit()
            logger.info(f"Created {created_count} sources, skipped {skipped_count}")
        except Exception as commit_error:
            db.session.rollback()
            logger.error(f"Commit failed: {commit_error}")


def main():
    parser = argparse.ArgumentParser(description="Seed harvest sources for DOCiD")
    parser.add_argument("--dry-run", action="store_true", help="Preview without committing")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        seed_sources(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
