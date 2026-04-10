"""
Tenant branding config API.

Public read endpoint consumed by the Next.js frontend to resolve
per-client branding (logo, colors, title, etc.) based on the request
subdomain. Phase 1 is branding-only — no data scoping, no auth.

See: plan file mellow-kindling-hearth.md, and the Tenant model in
app/models.py for column definitions.
"""
import logging

from flask import Blueprint, jsonify

from app.models import Tenant

logger = logging.getLogger(__name__)

tenants_bp = Blueprint("tenants", __name__, url_prefix="/api/v1/tenants")


@tenants_bp.route("/<slug>", methods=["GET"])
def get_tenant_by_slug(slug):
    """
    Fetch branding config for a tenant slug.

    ---
    tags:
      - Tenants
    parameters:
      - in: path
        name: slug
        type: string
        required: true
        description: Tenant subdomain slug, e.g. "stellenbosch"
    responses:
      200:
        description: Tenant branding config
      404:
        description: Tenant not found or inactive
    """
    tenant = Tenant.query.filter_by(slug=slug, is_active=True).first()
    if not tenant:
        return jsonify({"error": "tenant not found"}), 404
    return jsonify(tenant.to_dict()), 200
