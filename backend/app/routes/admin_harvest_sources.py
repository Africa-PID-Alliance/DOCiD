"""Admin REST API for harvest_sources.

Onboarding a new university repository is a DB-only operation: POST a JSON
body here and the harvester picks it up on the next run. No code change,
config edit, or seed-script update needed.
"""
from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError
import logging

from app import db
from app.models import HarvestSource, UserAccount
from app.utils_crypto import encrypt_value

logger = logging.getLogger(__name__)

admin_harvest_sources_bp = Blueprint(
    "admin_harvest_sources", __name__, url_prefix="/api/v1/admin/harvest-sources"
)


REQUIRED_FIELDS = ("name", "base_url", "api_type", "owner_name", "owner_email")
ALLOWED_API_TYPES = ("legacy", "modern", "figshare", "ojs")
ALLOWED_FREQUENCIES = ("daily", "weekly", "biweekly", "monthly")


def _validate_payload(payload, partial=False):
    if not isinstance(payload, dict):
        return "Body must be a JSON object"
    if not partial:
        missing = [field for field in REQUIRED_FIELDS if not payload.get(field)]
        if missing:
            return f"Missing required field(s): {', '.join(missing)}"
    api_type = payload.get("api_type")
    if api_type and api_type not in ALLOWED_API_TYPES:
        return f"api_type must be one of {ALLOWED_API_TYPES}"
    frequency = payload.get("harvest_frequency")
    if frequency and frequency not in ALLOWED_FREQUENCIES:
        return f"harvest_frequency must be one of {ALLOWED_FREQUENCIES}"
    return None


def _apply_payload(source, payload, secret_key):
    """Copy whitelisted fields from payload into source. Encrypts credentials."""
    for field in ("name", "base_url", "ui_base_url", "dspace_version", "api_type",
                  "owner_name", "owner_email", "harvest_frequency"):
        if field in payload:
            setattr(source, field, payload[field])
    if "auth_required" in payload:
        source.auth_required = bool(payload["auth_required"])
    if "is_active" in payload:
        source.is_active = bool(payload["is_active"])
    if payload.get("username"):
        source.encrypted_username = encrypt_value(payload["username"], secret_key)
    if payload.get("password"):
        source.encrypted_password = encrypt_value(payload["password"], secret_key)


def _serialize_with_status(source):
    data = source.serialize()
    data["owner_resolved"] = source.owner_user_id is not None
    if source.owner_email and not source.owner_user_id:
        data["owner_resolution_hint"] = (
            f"No user_account exists with email={source.owner_email!r}. "
            "Create the institutional account, then PATCH this source to retrigger resolution."
        )
    return data


@admin_harvest_sources_bp.route("", methods=["GET"])
@jwt_required()
def list_sources():
    sources = HarvestSource.query.order_by(HarvestSource.id).all()
    return jsonify({"sources": [_serialize_with_status(source) for source in sources]})


@admin_harvest_sources_bp.route("/<int:source_id>", methods=["GET"])
@jwt_required()
def get_source(source_id):
    source = HarvestSource.query.get_or_404(source_id)
    return jsonify(_serialize_with_status(source))


@admin_harvest_sources_bp.route("", methods=["POST"])
@jwt_required()
def create_source():
    payload = request.get_json(silent=True) or {}
    error = _validate_payload(payload, partial=False)
    if error:
        return jsonify({"error": error}), 400

    secret_key = current_app.config.get("SECRET_KEY", "")
    if not secret_key:
        return jsonify({"error": "SECRET_KEY not configured — cannot encrypt credentials"}), 500

    source = HarvestSource()
    _apply_payload(source, payload, secret_key)
    db.session.add(source)
    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        logger.exception("create_source IntegrityError")
        return jsonify({"error": "Integrity error", "detail": str(exc.orig)}), 409

    # before_insert event already resolved owner_user_id from owner_email.
    return jsonify(_serialize_with_status(source)), 201


@admin_harvest_sources_bp.route("/<int:source_id>", methods=["PATCH"])
@jwt_required()
def update_source(source_id):
    source = HarvestSource.query.get_or_404(source_id)
    payload = request.get_json(silent=True) or {}
    error = _validate_payload(payload, partial=True)
    if error:
        return jsonify({"error": error}), 400

    secret_key = current_app.config.get("SECRET_KEY", "")
    _apply_payload(source, payload, secret_key)
    # Force re-resolution if owner_email was provided in this PATCH.
    if "owner_email" in payload:
        source.owner_user_id = None
        source.resolve_owner()
    db.session.commit()
    return jsonify(_serialize_with_status(source))


@admin_harvest_sources_bp.route("/<int:source_id>/resolve-owner", methods=["POST"])
@jwt_required()
def resolve_owner(source_id):
    """Manual re-resolution endpoint — useful after the institutional user_account is created."""
    source = HarvestSource.query.get_or_404(source_id)
    source.owner_user_id = None
    source.resolve_owner()
    db.session.commit()
    return jsonify(_serialize_with_status(source))
