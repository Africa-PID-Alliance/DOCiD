# app/routes/cordra.py
from flask import Blueprint, g, jsonify, make_response, request, current_app
from flask_limiter.util import get_remote_address
from flask_jwt_extended import get_jwt_identity, jwt_required
import hashlib
import json
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import re
import uuid
from datetime import datetime
import time
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app import db, limiter
from app.authz import admin_required, database_user_required, pid_minter_required
from app.models import PidMintAudit
from app.service_codra import deposit_metadata, list_operations, assign_doi_indigenous_knowledge, assign_doi_container_id, assign_doi_patent, assign_identifier_apa_handle
from app.service_codra import push_apa_metadata

# Configure logging with more detail
logger = logging.getLogger("cordoi_api_logger")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = RotatingFileHandler("logs/cordoi_api.log", maxBytes=1000000, backupCount=5)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Blueprint definition
cordoi_bp = Blueprint("cordoi", __name__, url_prefix="/api/v1/cordoi")


def _mint_rate_key():
    """Rate-limit by authenticated actor and source IP."""
    return f"{get_jwt_identity()}:{get_remote_address()}"


def _minute_limit():
    return current_app.config.get("PID_MINT_RATE_LIMIT", "5 per minute")


def _daily_limit():
    return current_app.config.get("PID_MINT_DAILY_LIMIT", "100 per day")


def _payload_sha256(payload):
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _safe_response_body(response):
    body = response.get_json(silent=True)
    if not isinstance(body, dict):
        return {"message": "PID registry operation completed"}
    allowed = {
        key: body[key]
        for key in ("success", "message", "id", "error", "error_code")
        if key in body
    }
    return allowed or {"message": "PID registry operation completed"}


def _audit_replay(audit):
    try:
        body = json.loads(audit.response_body or "{}")
    except (TypeError, ValueError):
        body = {"error": "Stored PID operation response is unavailable"}
    response = jsonify(body)
    response.status_code = audit.response_status or 409
    response.headers["X-Idempotent-Replay"] = "true"
    response.headers["X-Request-ID"] = audit.request_id
    return response


def audited_pid_write(operation, resource_type):
    """Reserve an idempotency key and persist a sanitized PID write audit."""

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            idempotency_key = (request.headers.get("Idempotency-Key") or "").strip()
            if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idempotency_key):
                return jsonify({
                    "error": "A valid Idempotency-Key header (8-128 characters) is required"
                }), 400

            user = g.current_user
            existing = PidMintAudit.query.filter_by(
                user_id=user.user_id,
                operation=operation,
                idempotency_key=idempotency_key,
            ).first()
            if existing:
                if existing.status == "in_progress":
                    return jsonify({
                        "error": "A request with this idempotency key is already in progress",
                        "request_id": existing.request_id,
                    }), 409
                return _audit_replay(existing)

            payload = request.get_json(silent=True) or {}
            audit = PidMintAudit(
                user_id=user.user_id,
                operation=operation,
                resource_type=resource_type,
                idempotency_key=idempotency_key,
                request_id=str(uuid.uuid4()),
                payload_sha256=_payload_sha256(payload),
                status="in_progress",
                ip_address=request.environ.get("HTTP_X_REAL_IP", request.remote_addr),
                user_agent=(request.headers.get("User-Agent") or "")[:1000],
            )
            db.session.add(audit)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                existing = PidMintAudit.query.filter_by(
                    user_id=user.user_id,
                    operation=operation,
                    idempotency_key=idempotency_key,
                ).first()
                if existing:
                    return _audit_replay(existing) if existing.status != "in_progress" else (
                        jsonify({"error": "A request with this idempotency key is already in progress"}),
                        409,
                    )
                return jsonify({"error": "Unable to reserve PID operation"}), 503
            except SQLAlchemyError:
                db.session.rollback()
                logger.exception("Unable to create PID audit reservation")
                return jsonify({"error": "PID audit service unavailable"}), 503

            try:
                response = make_response(function(*args, **kwargs))
                response_body = _safe_response_body(response)
                audit.response_status = response.status_code
                audit.response_body = json.dumps(response_body, sort_keys=True)
                audit.identifier = str(response_body.get("id"))[:255] if response_body.get("id") else None
                audit.status = "success" if 200 <= response.status_code < 300 else "failed"
                audit.error_code = response_body.get("error_code")
                audit.completed_at = datetime.utcnow()
                db.session.commit()
                response.headers["X-Request-ID"] = audit.request_id
                return response
            except Exception:
                db.session.rollback()
                try:
                    audit = db.session.get(PidMintAudit, audit.id)
                    if audit:
                        audit.status = "failed"
                        audit.response_status = 500
                        audit.response_body = json.dumps({"error": "PID registry operation failed"})
                        audit.error_code = "UNHANDLED_EXCEPTION"
                        audit.completed_at = datetime.utcnow()
                        db.session.commit()
                except SQLAlchemyError:
                    db.session.rollback()
                    logger.exception("Unable to finalize failed PID audit")
                logger.exception("Unhandled PID registry operation failure")
                return jsonify({"error": "PID registry operation failed"}), 500

        return wrapper

    return decorator


def minting_enabled(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("PID_MINTING_ENABLED", False):
            return jsonify({
                "error": "PID minting is temporarily disabled",
                "error_code": "PID_MINTING_DISABLED",
            }), 503
        return function(*args, **kwargs)

    return wrapper


def debug_routes_enabled(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_app.config.get("CORDRA_DEBUG_ROUTES_ENABLED", False):
            return jsonify({"error": "Not found"}), 404
        return function(*args, **kwargs)

    return wrapper


def _service_response(result):
    if not isinstance(result, dict):
        return jsonify({"error": "Invalid response from PID registry"}), 502
    if result.get("success"):
        return jsonify({
            "success": True,
            "message": result.get("message", "PID registry operation completed"),
            "id": result.get("id"),
        }), 200
    status = result.get("status_code")
    if not isinstance(status, int) or status < 400 or status > 499:
        status = 502
    logger.error("Cordra operation failed with status=%s", result.get("status_code"))
    return jsonify({
        "success": False,
        "error": "PID registry operation failed",
        "error_code": "UPSTREAM_PID_FAILURE",
    }), status

def log_api_request(func):
    """Decorator to log API requests with detailed information"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.info(f"Request {request_id} started - Endpoint: {request.endpoint}")
        logger.info(f"Request {request_id} params: {request.args}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Request {request_id} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request {request_id} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

@cordoi_bp.route("/push-apa-sample", methods=["POST"])
@jwt_required()
@admin_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("push_apa_sample", "APA_Handle_ID")
@debug_routes_enabled
@minting_enabled
def push_sample_apa_metadata():
    """
    Push sample APA metadata to Cordra.

    ---
    tags:
      - Cordra
    responses:
      200:
        description: Metadata successfully pushed to Cordra
      500:
        description: Internal server error during metadata push
    """
    try:
        # Sample metadata structure
        metadata = {
            "docid": "https://cordra.kenet.or.ke/#objects/20.500.14351/testdocid",
            "title": "Example DOCiD Metadata Push",
            "description": "This is a sample publication record pushed to Cordra via the API.",
            "doi": "10.1234/sample-doi",
            "owner": "john.doe",
            "user_id": 123,
            "resource_type_id": 1,
            "avatar": "https://example.org/avatar.jpg",
            "poster_url": "https://example.org/poster.png",
            "taxonomy_code": "AI.01.03",
            "orcid": "0000-0002-1825-0097",
            "ror": "https://ror.org/04aj4c181",
            "created_on": int(time.time())
        }

        return _service_response(push_apa_metadata(metadata))

    except Exception:
        logger.exception("Error in /push-apa-sample")
        return jsonify({"error": "PID registry operation failed"}), 500
   
@cordoi_bp.route("/assign-identifier/apa-handle", methods=["POST"])
@jwt_required()
@database_user_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("assign_apa_handle", "APA_Handle_ID")
@minting_enabled
def assign_identifier_apa_handle_route():
    """
    Assign an auto-generated identifier using the APA_Handle_ID schema.

    ---
    tags:
      - Cordra
    requestBody:
      required: false
      content:
        application/json:
          schema:
            type: object
            description: No body is required for this request.
    responses:
      200:
        description: Successfully generated the identifier.
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Identifier successfully assigned."
                id:
                  type: string
                  example: "20.500.14351/ddc54ef8865421e6a351"
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Internal server error: <details>"
    """
    try:
        return _service_response(assign_identifier_apa_handle())

    except Exception:
        logger.exception("APA Handle assignment failed")
        return jsonify({"error": "PID registry operation failed"}), 500

@cordoi_bp.route("/assign-doi/indigenous-knowledge", methods=["POST"])
@jwt_required()
@database_user_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("assign_indigenous_knowledge", "Indigenous Knowledge")
@minting_enabled
def assign_doi_indigenous_knowledge_route():
    """
    Assign a DOI to an Indigenous Knowledge example object.
    
    ---
    tags:
      - Cordra
    parameters:
      - name: doi
        in: body
        required: true
        schema:
          type: string
          description: The DOI to assign to the digital object.
      - name: name
        in: body
        required: true
        schema:
          type: string
          description: The name of the document.
      - name: description
        in: body
        required: true
        schema:
          type: string
          description: The description of the document.
      - name: description2
        in: body
        required: false
        schema:
          type: string
          description: An optional secondary description.
    responses:
      200:
        description: Successfully assigned the DOI.
      400:
        description: Missing or invalid parameters.
      500:
        description: Internal server error.
    """
    try:
        data = request.get_json(silent=True) or {}
        response = assign_doi_indigenous_knowledge(
            doi=data.get("doi"),
            name=data.get("name"),
            description=data.get("description"),
            description2=data.get("description2", "")
        )
        return _service_response(response)
    except Exception:
        logger.exception("Indigenous Knowledge PID assignment failed")
        return jsonify({"error": "PID registry operation failed"}), 500

@cordoi_bp.route("/assign-doi/container-id", methods=["POST"])
@jwt_required()
@database_user_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("assign_container_id", "Container iD")
@minting_enabled
def assign_doi_container_id_route():
    """
    Assign a DOI to a Container iD object.

    ---
    tags:
      - Cordra
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              title:
                type: string
                description: The title of the container.
                example: "Research Data Group"
              description:
                type: string
                description: Additional description of the container.
                example: "This is a group container for managing research data."
    responses:
      200:
        description: Successfully assigned the DOI.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "DOI successfully assigned."
                id:
                  type: string
                  example: "20.500.14351/bd431f38c26d03eaa38f"
      400:
        description: Missing or invalid parameters.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Missing required field: title"
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Internal server error: <details>"
    """
    try:
        data = request.get_json(silent=True) or {}

        # Validate required fields
        required_fields = ["title", "description"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Strip HTML tags from description
        description = data.get("description", "")
        # Remove HTML tags using regex
        clean_description = re.sub('<.*?>', '', description).strip()
        
        # Call the helper function to assign the DOI
        response = assign_doi_container_id(
            title=data.get("title"),
            description=clean_description
        )
        return _service_response(response)
    except Exception:
        logger.exception("Container iD assignment failed")
        return jsonify({"error": "PID registry operation failed"}), 500



@cordoi_bp.route("/assign-doi/patent", methods=["POST"])
@jwt_required()
@database_user_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("assign_patent", "Patent")
@minting_enabled
def assign_doi_patent_route():
    """
    Assign a DOI to a Patent object.

    ---
    tags:
      - Cordra
    parameters:
      - name: doi
        in: body
        required: true
        schema:
          type: string
          description: The DOI to assign to the digital object.
      - name: name
        in: body
        required: true
        schema:
          type: string
          description: The name of the patent.
      - name: description
        in: body
        required: true
        schema:
          type: string
          description: The description of the patent.
      - name: title
        in: body
        required: true
        schema:
          type: string
          description: The title of the patent.
      - name: inventor
        in: body
        required: true
        schema:
          type: string
          description: The name of the inventor.
      - name: assignee
        in: body
        required: true
        schema:
          type: string
          description: The name of the assignee.
      - name: date
        in: body
        required: true
        schema:
          type: string
          format: date
          description: The general date associated with the patent.
      - name: application_date
        in: body
        required: true
        schema:
          type: string
          format: date
          description: The application date of the patent.
      - name: grant_date
        in: body
        required: true
        schema:
          type: string
          format: date
          description: The grant date of the patent.
      - name: classification_code
        in: body
        required: true
        schema:
          type: string
          description: The classification code of the patent.
      - name: classification_date
        in: body
        required: false
        schema:
          type: string
          format: date
          description: The classification date of the patent (optional).
      - name: abstract
        in: body
        required: false
        schema:
          type: string
          description: An abstract of the patent.
      - name: owner
        in: body
        required: false
        schema:
          type: string
          description: The owner of the patent.
    responses:
      200:
        description: Successfully assigned the DOI.
      400:
        description: Missing or invalid parameters.
      500:
        description: Internal server error.
    """
    data = request.get_json(silent=True) or {}
    try:
        response = assign_doi_patent(
            doi=data["doi"],
            name=data["name"],
            description=data["description"],
            title=data["title"],
            inventor=data["inventor"],
            assignee=data["assignee"],
            date=data["date"],
            application_date=data["application_date"],
            grant_date=data["grant_date"],
            classification_code=data["classification_code"],
            classification_date=data.get("classification_date", ""),
            abstract=data.get("abstract", ""),
            owner=g.current_user.full_name or g.current_user.email
        )
        return _service_response(response)
    except KeyError as error:
        return jsonify({"error": f"Missing required parameter: {error.args[0]}"}), 400
    except Exception:
        logger.exception("Patent PID assignment failed")
        return jsonify({"error": "PID registry operation failed"}), 500

@cordoi_bp.route("/assign-doi/user", methods=["POST"])
@jwt_required()
@admin_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("assign_user", "User")
def assign_doi_user_route():
    """
    Assign a DOI to a User object.
    
    ---
    tags:
      - Cordra
    parameters:
      - name: username
        in: body
        required: true
        schema:
          type: string
          description: The username of the user.
      - name: email
        in: body
        required: true
        schema:
          type: string
          description: The email of the user.
      - name: role
        in: body
        required: true
        schema:
          type: string
          description: The role of the user.
      - name: metadata
        in: body
        required: false
        schema:
          type: object
          description: Additional metadata for the user.
    responses:
      200:
        description: Successfully assigned the DOI.
      400:
        description: Missing or invalid parameters.
      500:
        description: Internal server error.
    """
    return jsonify({
        "error": "User PID creation is disabled; use the account provisioning workflow",
        "error_code": "USER_PID_ENDPOINT_DISABLED",
    }), 410

@cordoi_bp.route("/deposit-metadata", methods=["POST"])
@jwt_required()
@admin_required
@limiter.limit(_minute_limit, key_func=_mint_rate_key)
@limiter.limit(_daily_limit, key_func=_mint_rate_key)
@audited_pid_write("deposit_sample_metadata", "Sample Resource")
@debug_routes_enabled
@minting_enabled
def deposit_metadata_route():
    """
    Deposit CODRA metadata
    ---
    tags:
      - Cordra
    responses:
      200:
        description: Get CODRA metadata response as JSON
        schema:
          type: array
          items:
            type: string
      400:
        description: Error depositing CODRA metadata (e.g., invalid request data)
      500:
        description: Internal server error
    """
    try:
        example_metadata = {
            "name": "Sample Resource",
            "description": "A sample resource to be stored in Cordra",
            "identifier": "10.1234/sample-resource",
            "type": "text",
            "date_created": "2024-10-01",
            "author": {
                "name": "John Doe",
                "affiliation": "Sample University"
            }
        }

        # Replace 'target_id' with the actual target ID if needed
        return _service_response(deposit_metadata(example_metadata, target_id="your_target_id"))
    except Exception:
        logger.exception("Sample metadata deposit failed")
        return jsonify({"error": "PID registry operation failed"}), 500

@cordoi_bp.route("/list-operations", methods=["GET"])
@jwt_required()
@pid_minter_required
def list_operations_route():
    """
    Retrieve a list of available operations from the Cordra API.

    ---
    tags:
      - Cordra
    responses:
      200:
        description: Successfully retrieved the list of operations
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                data:
                  type: array
                  items:
                    type: string
                    description: Operation ID
      500:
        description: Failed to retrieve the list of operations
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: false
                message:
                  type: string
                  example: "Failed to retrieve operations"
    """
    try:
        response = list_operations()
        if response.get("success"):
            return jsonify({
                "success": True,
                "data": response.get("data"),
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": response.get("message", "Failed to retrieve operations"),
            }), 500

    except Exception:
        logger.exception("Failed to list Cordra operations")
        return jsonify({"error": "Failed to list PID registry operations"}), 500
