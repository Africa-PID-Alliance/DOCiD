#!/usr/bin/env python3
"""
Seed or update per-client tenant branding (whitelabel subdomains).

Usage (from backend/, with venv active):
    PYTHONPATH=. python seed_tenants.py
    PYTHONPATH=. python seed_tenants.py --dry-run

Safe to re-run: upserts by unique slug (updateOrCreate). Edit TENANTS below
and run again to push changes to an existing row.

Requires: flask db upgrade (tenants table) before first run.
"""

import argparse
import logging
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app, db
from app.models import Tenant

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Keys other than slug that are applied on create and update.
TENANT_FIELDS = (
    "display_name",
    "logo_url",
    "logo_dark_url",
    "favicon_url",
    "og_image_url",
    "primary_color",
    "primary_color_dark",
    "accent_color",
    "page_title",
    "page_description",
    "hero_tagline",
    "footer_copyright",
    "contact_email",
    "email_from_name",
    "feature_flags",
    "is_active",
)

# Stellenbosch University brand (from official logo):
#   Maroon wordmark  → primary / navbar
#   Dark maroon      → footer, hover, dark text
#   Crest gold       → highlights (UI uses a light gold tint for surfaces)
_STELLENBOSCH_BRANDING = {
    "display_name": "Stellenbosch University",
    "logo_url": "https://africapidalliance.org/institutions/stellenbosch.jpeg",
    "logo_dark_url": None,
    "favicon_url": "/favicon.ico",
    "og_image_url": "https://africapidalliance.org/institutions/stellenbosch.jpeg",
    "primary_color": "#7F1734",
    "primary_color_dark": "#4D0F20",
    "accent_color": "#E8DCC8",
    "page_title": "Stellenbosch DOCiD",
    "page_description": None,
    "hero_tagline": None,
    "footer_copyright": "Stellenbosch University",
    "contact_email": "info@sun.ac.za",
    "email_from_name": "Stellenbosch University",
    "feature_flags": None,
    "is_active": True,
}

TENANTS = [
    {**_STELLENBOSCH_BRANDING, "slug": "stellenbosch"},
    # Demo/test host: stellenbosch-test.africapidalliance.org
    {**_STELLENBOSCH_BRANDING, "slug": "stellenbosch-test"},
]


def upsert_tenant(config: dict) -> str:
    """
    Insert or update a tenant row keyed by slug.

    Returns: 'created' | 'updated'
    """
    slug = config["slug"]
    now = datetime.utcnow()
    tenant = Tenant.query.filter_by(slug=slug).first()

    payload = {field: config.get(field) for field in TENANT_FIELDS}
    if payload.get("feature_flags") is None:
        payload["feature_flags"] = {}

    if tenant:
        for field, value in payload.items():
            setattr(tenant, field, value)
        tenant.updated_at = now
        logger.info("Updated tenant slug=%s (id=%s)", slug, tenant.id)
        return "updated"

    tenant = Tenant(
        slug=slug,
        created_at=now,
        updated_at=now,
        **payload,
    )
    db.session.add(tenant)
    logger.info("Created tenant slug=%s", slug)
    return "created"


def seed_tenants(dry_run: bool = False) -> None:
    created = 0
    updated = 0

    for config in TENANTS:
        if "slug" not in config:
            raise ValueError(f"Tenant config missing slug: {config}")
        result = upsert_tenant(config)
        if result == "created":
            created += 1
        else:
            updated += 1

    if dry_run:
        db.session.rollback()
        logger.info(
            "[DRY RUN] Would upsert %s tenant(s): %s created, %s updated",
            len(TENANTS),
            created,
            updated,
        )
        return

    try:
        db.session.commit()
        logger.info(
            "Tenants seed complete: %s created, %s updated",
            created,
            updated,
        )
    except Exception as exc:
        db.session.rollback()
        logger.error("Commit failed: %s", exc)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed DOCiD tenant branding rows")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview upserts without committing",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        seed_tenants(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
