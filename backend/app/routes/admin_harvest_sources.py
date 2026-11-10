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
from app.models import HarvestSource, HarvestSourceCollection, ResourceTypes, UserAccount
from app.authz import admin_required
from app.service_dspace_collections import check_collection_connection, make_reader
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
@admin_required
def list_sources():
    sources = HarvestSource.query.order_by(HarvestSource.id).all()
    return jsonify({"sources": [_serialize_with_status(source) for source in sources]})


@admin_harvest_sources_bp.route("/<int:source_id>", methods=["GET"])
@jwt_required()
@admin_required
def get_source(source_id):
    source = HarvestSource.query.get_or_404(source_id)
    return jsonify(_serialize_with_status(source))


@admin_harvest_sources_bp.route("", methods=["POST"])
@jwt_required()
@admin_required
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
@admin_required
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
@admin_required
def resolve_owner(source_id):
    """Manual re-resolution endpoint — useful after the institutional user_account is created."""
    source = HarvestSource.query.get_or_404(source_id)
    source.owner_user_id = None
    source.resolve_owner()
    db.session.commit()
    return jsonify(_serialize_with_status(source))


# ---------------------------------------------------------------------------
# Watched collections: the DSpace collections (IK, CH, ...) DOCiD harvests for
# a source, with the DOCiD URL written back into each record.
# ---------------------------------------------------------------------------

def _get_collection_or_404(source_id, collection_id):
    collection = HarvestSourceCollection.query.filter_by(
        id=collection_id, harvest_source_id=source_id
    ).first()
    if collection is None:
        return None, (jsonify({"error": "Collection not found for this source"}), 404)
    return collection, None


def _validate_resource_type(resource_type_id):
    if resource_type_id is None:
        return "resource_type_id is required"
    try:
        resource_type_id = int(resource_type_id)
    except (TypeError, ValueError):
        return "resource_type_id must be an integer"
    if db.session.get(ResourceTypes, resource_type_id) is None:
        return f"resource_type_id {resource_type_id} does not exist"
    return None


@admin_harvest_sources_bp.route("/<int:source_id>/collections", methods=["GET"])
@jwt_required()
@admin_required
def list_collections(source_id):
    source = HarvestSource.query.get_or_404(source_id)
    return jsonify({"collections": [collection.serialize() for collection in source.collections]})


@admin_harvest_sources_bp.route("/<int:source_id>/collections", methods=["POST"])
@jwt_required()
@admin_required
def add_collection(source_id):
    """
    Watch a DSpace collection. Body: {"collection": "<link, handle or UUID>",
    "resource_type_id": <int>, "write_back_enabled": true}. The collection is
    looked up in the source's DSpace, so a typo fails here, not at harvest time.
    """
    source = HarvestSource.query.get_or_404(source_id)
    if source.api_type != "modern":
        return jsonify({"error": "Watched collections need a DSpace 7+ source (api_type 'modern')"}), 400

    payload = request.get_json(silent=True) or {}
    reference = (payload.get("collection") or "").strip()
    if not reference:
        return jsonify({"error": "collection is required (a collection link, handle or UUID)"}), 400
    error = _validate_resource_type(payload.get("resource_type_id"))
    if error:
        return jsonify({"error": error}), 400

    try:
        dspace_collection = make_reader(source).find_collection(reference)
    except Exception as lookup_error:
        logger.warning(f"Collection lookup failed for source {source_id}: {lookup_error}")
        return jsonify({"error": f"Could not reach {source.base_url}: {lookup_error}"}), 502
    if dspace_collection is None:
        return jsonify({"error": f"No collection found in {source.base_url} for {reference!r}"}), 404

    collection = HarvestSourceCollection(
        harvest_source_id=source.id,
        dspace_collection_uuid=dspace_collection["uuid"],
        dspace_collection_handle=dspace_collection.get("handle"),
        collection_name=(dspace_collection.get("name") or "")[:255] or None,
        resource_type_id=int(payload["resource_type_id"]),
        write_back_enabled=bool(payload.get("write_back_enabled", True)),
    )
    db.session.add(collection)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "This collection is already watched for this source"}), 409
    return jsonify(collection.serialize()), 201


@admin_harvest_sources_bp.route("/<int:source_id>/collections/<int:collection_id>", methods=["PATCH"])
@jwt_required()
@admin_required
def update_collection(source_id, collection_id):
    collection, error_response = _get_collection_or_404(source_id, collection_id)
    if error_response:
        return error_response
    payload = request.get_json(silent=True) or {}
    if "resource_type_id" in payload:
        error = _validate_resource_type(payload["resource_type_id"])
        if error:
            return jsonify({"error": error}), 400
        collection.resource_type_id = int(payload["resource_type_id"])
    for field in ("write_back_enabled", "is_active"):
        if field in payload:
            setattr(collection, field, bool(payload[field]))
    db.session.commit()
    return jsonify(collection.serialize())


@admin_harvest_sources_bp.route("/<int:source_id>/collections/<int:collection_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def remove_collection(source_id, collection_id):
    """Stop watching a collection. Records already harvested, and their DOCiDs, stay."""
    collection, error_response = _get_collection_or_404(source_id, collection_id)
    if error_response:
        return error_response
    db.session.delete(collection)
    db.session.commit()
    return jsonify({"message": "Collection removed", "id": collection_id})


@admin_harvest_sources_bp.route("/<int:source_id>/collections/<int:collection_id>/test", methods=["POST"])
@jwt_required()
@admin_required
def check_collection(source_id, collection_id):
    """
    Connection test: lists the collection anonymously, logs in with the
    source's DSpace account and checks it may edit metadata there (the
    Administrators role). Stores the answer as write_back_ok.
    """
    collection, error_response = _get_collection_or_404(source_id, collection_id)
    if error_response:
        return error_response
    report = check_collection_connection(
        collection.source, collection, current_app.config.get("SECRET_KEY", "")
    )
    return jsonify({"collection": collection.serialize(), "report": report})
