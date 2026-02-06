"""
Local Contexts Hub API v2 Integration

This module provides endpoints for interacting with the Local Contexts Hub API.
Local Contexts supports Indigenous communities with tools to manage intellectual
property and cultural heritage rights through Labels and Notices.

API Documentation: https://github.com/localcontexts/localcontextshub/wiki/API-Documentation

Available v2 Endpoints:
- /projects/ - List all public projects
- /projects/<unique_id>/ - Get project details (includes labels & notices)
- /projects/multi/<id1>,<id2>/ - Get multiple projects
- /projects/multi/date_modified/<id1>,<id2>/ - Get date modified for multiple projects
- /notices/open_to_collaborate/ - Get Open to Collaborate notice info

Per DocID_Local_Contexts_Tech_Documentation.md:
- DocID stores references + cached metadata only
- All authoritative label data remains external
- Integration must survive API unavailability (fallback to cache)
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from flask import Blueprint, request, jsonify, current_app
from app import db
from app.models import (
    LocalContext, LocalContextType, PublicationLocalContext,
    LocalContextAuditLog, Publications
)
from app.service_codra import push_apa_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/localcontexts.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a Blueprint for Local Contexts routes
localcontexts_bp = Blueprint('localcontexts', __name__, url_prefix='/api/v1/localcontexts')

# Local Contexts API base URL - v2 with trailing slash handling
LOCAL_CONTEXTS_API_BASE_URL = "https://sandbox.localcontextshub.org/api/v2"

# Cache TTL settings per DocID_Local_Contexts_Tech_Documentation.md
CACHE_TTL_DAYS = 30  # Cached labels expire after 30 days
RESYNC_TIMEOUT_SECONDS = 10  # Blocking resync timeout before falling back to stale data


def is_cache_stale(cached_at: datetime) -> bool:
    """Check if cached data is older than CACHE_TTL_DAYS."""
    if not cached_at:
        return True
    from datetime import timedelta
    return datetime.utcnow() - cached_at > timedelta(days=CACHE_TTL_DAYS)


def _resync_stale_cache(cached: 'LocalContext', timeout: int = RESYNC_TIMEOUT_SECONDS) -> tuple:
    """
    Attempt to resync stale cache with blocking request.

    Returns:
        Tuple of (success: bool, updated_cached: LocalContext or None)
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        logger.warning(f"Cannot resync {cached.external_id}: API key not configured")
        return False, None

    # Determine the endpoint based on context type
    path = f"/projects/{cached.external_id}/"
    url = f"{LOCAL_CONTEXTS_API_BASE_URL}{path}"
    headers = {"x-api-key": api_key, "Accept": "application/json"}

    try:
        logger.info(f"Resync stale cache for {cached.external_id} (timeout={timeout}s)")
        resp = requests.get(url, headers=headers, timeout=timeout)

        if resp.status_code == 200:
            hub_data = resp.json()
            cached.title = hub_data.get('title') or hub_data.get('name') or cached.title
            cached.summary = hub_data.get('description') or hub_data.get('summary') or cached.summary
            cached.community_name = (
                hub_data.get('community', {}).get('name')
                if isinstance(hub_data.get('community'), dict)
                else hub_data.get('community_name') or cached.community_name
            )
            cached.cached_at = datetime.utcnow()
            cached.last_sync_attempt = datetime.utcnow()
            cached.sync_error = None
            db.session.commit()
            logger.info(f"Successfully resynced cache for {cached.external_id}")
            return True, cached
        elif resp.status_code == 404:
            cached.is_active = False
            cached.last_sync_attempt = datetime.utcnow()
            cached.sync_error = "Resource not found (404) during resync"
            db.session.commit()
            logger.warning(f"Resource {cached.external_id} not found during resync")
            return False, None
        else:
            cached.last_sync_attempt = datetime.utcnow()
            cached.sync_error = f"Resync failed: HTTP {resp.status_code}"
            db.session.commit()
            return False, None

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.warning(f"Resync timeout/connection error for {cached.external_id}: {e}")
        cached.last_sync_attempt = datetime.utcnow()
        cached.sync_error = f"Resync failed: {type(e).__name__}"
        db.session.commit()
        return False, None
    except Exception as e:
        logger.error(f"Unexpected error during resync for {cached.external_id}: {e}")
        return False, None


def _make_request(path: str, params: dict = None, method: str = "GET", data: dict = None, timeout: int = 30, external_id: str = None):
    """
    Make a request to the Local Contexts API v2 with cache fallback.

    Per Section 10: If Hub is unreachable, use cached metadata.

    Args:
        path: API path to call (should include trailing slash for v2)
        params: URL parameters for the request
        method: HTTP method (GET, POST, etc.)
        data: Request body data (for POST)
        timeout: Request timeout in seconds
        external_id: Optional external ID for cache lookup on failure

    Returns:
        Tuple of (status_code, json_response, from_cache)
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        # Try cache before returning error
        if external_id:
            cached = LocalContext.get_by_external_id(external_id)
            if cached and cached.is_active:
                response = _cached_to_response(cached)
                if is_cache_stale(cached.cached_at):
                    response['_cache_stale'] = True
                    response['_cache_note'] = f"Data is stale (>{CACHE_TTL_DAYS} days old). API key not configured for resync."
                logger.info(f"API key not configured, using cached data for {external_id}")
                return 200, response, True
        return 401, {"error": "Local Contexts API key not configured. Set LC_API_KEY in .env"}, False

    # Ensure path has trailing slash for v2 API
    if not path.endswith('/'):
        path = path + '/'

    url = f"{LOCAL_CONTEXTS_API_BASE_URL}{path}"
    headers = {
        "x-api-key": api_key,
        "Accept": "application/json"
    }

    if method == "POST":
        headers["Content-Type"] = "application/json"

    logger.info(f"LocalContexts API v2: {method} {url} params={params}")

    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params or {}, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, headers=headers, params=params or {}, json=data, timeout=timeout)
        else:
            return 400, {"error": f"Unsupported HTTP method: {method}"}, False

        # Handle response
        if resp.status_code == 200:
            try:
                return 200, resp.json(), False
            except ValueError:
                return 200, {"raw_response": resp.text}, False
        elif resp.status_code == 401:
            return 401, {"error": "Invalid API key", "detail": "Check your LC_API_KEY configuration"}, False
        elif resp.status_code == 404:
            # Mark as inactive if we have cached data
            if external_id:
                cached = LocalContext.get_by_external_id(external_id)
                if cached:
                    cached.is_active = False
                    cached.last_sync_attempt = datetime.utcnow()
                    cached.sync_error = "Resource not found (404)"
                    db.session.commit()
                    LocalContextAuditLog.log(
                        action='MARK_INACTIVE',
                        external_id=external_id,
                        local_context_id=cached.id,
                        details={'reason': 'API returned 404'}
                    )
                    db.session.commit()
            return 404, {"error": "Resource not found", "path": path}, False
        else:
            try:
                error_data = resp.json()
            except ValueError:
                error_data = {"text": resp.text}
            return resp.status_code, {"error": f"API returned {resp.status_code}", "details": error_data}, False

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        # FALLBACK TO CACHE per Section 10
        logger.warning(f"Hub unreachable ({type(e).__name__}), checking cache for {external_id}")
        if external_id:
            cached = LocalContext.get_by_external_id(external_id)
            if cached and cached.is_active:
                response = _cached_to_response(cached)
                if is_cache_stale(cached.cached_at):
                    response['_cache_stale'] = True
                    response['_cache_note'] = f"Data is stale (>{CACHE_TTL_DAYS} days old). Hub unreachable for resync."
                logger.info(f"Using cached data for {external_id} (Hub unreachable)")
                return 200, response, True

        if isinstance(e, requests.exceptions.Timeout):
            logger.error(f"Request timeout for {url}")
            return 504, {"error": "Request timeout", "url": url, "fallback": "No cached data available"}, False
        else:
            logger.error(f"Connection error: {str(e)}")
            return 503, {"error": "Connection error", "details": str(e), "fallback": "No cached data available"}, False

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 500, {"error": str(e)}, False


def _cached_to_response(cached: LocalContext) -> dict:
    """Convert cached LocalContext to API-like response"""
    return {
        "external_id": cached.external_id,
        "context_type": cached.context_type,
        "title": cached.title,
        "summary": cached.summary,
        "community_name": cached.community_name,
        "source_url": cached.source_url,
        "image_url": cached.image_url,
        "cached_at": cached.cached_at.isoformat() if cached.cached_at else None,
        "_from_cache": True,
        "_cache_note": "Data served from local cache (Hub may be unreachable)"
    }


def _cache_context_from_hub(external_id: str, context_type: str, hub_data: dict) -> LocalContext:
    """
    Cache or update Local Contexts data from Hub response.

    Per Section 6: Only store verbatim summaries, never modify content.
    """
    context = LocalContext.get_by_external_id(external_id)

    if context:
        # Update existing cache
        context.title = hub_data.get('title') or hub_data.get('name')
        context.summary = hub_data.get('description') or hub_data.get('summary')
        context.community_name = hub_data.get('community', {}).get('name') if isinstance(hub_data.get('community'), dict) else hub_data.get('community_name')
        context.source_url = hub_data.get('source_url') or hub_data.get('url')
        context.image_url = hub_data.get('image_url') or hub_data.get('img_url')
        context.cached_at = datetime.utcnow()
        context.last_sync_attempt = datetime.utcnow()
        context.sync_error = None
        context.is_active = True
    else:
        # Create new cache entry
        context = LocalContext(
            external_id=external_id,
            context_type=context_type,
            title=hub_data.get('title') or hub_data.get('name'),
            summary=hub_data.get('description') or hub_data.get('summary'),
            community_name=hub_data.get('community', {}).get('name') if isinstance(hub_data.get('community'), dict) else hub_data.get('community_name'),
            source_url=hub_data.get('source_url') or hub_data.get('url'),
            image_url=hub_data.get('image_url') or hub_data.get('img_url'),
            cached_at=datetime.utcnow(),
            last_sync_attempt=datetime.utcnow(),
            is_active=True
        )
        db.session.add(context)

    db.session.commit()
    return context


def store_in_cordra(data: Dict[str, Any], source_type: str, source_id: str) -> Dict[str, Any]:
    """
    Store data from Local Contexts in Cordra

    Args:
        data: Data to store
        source_type: Type of Local Contexts resource (e.g., "project", "label")
        source_id: ID of the resource from Local Contexts

    Returns:
        Dict containing response from Cordra
    """
    try:
        metadata = {
            "local_contexts_data": data,
            "local_contexts_source_type": source_type,
            "local_contexts_source_id": source_id,
            "api_version": "v2"
        }

        response = push_apa_metadata(metadata)

        if response.get("success", False):
            logger.info(f"Successfully stored {source_type} {source_id} in Cordra")
            return {
                "success": True,
                "message": f"Successfully stored {source_type} {source_id} in Cordra",
                "cordra_id": response.get("id")
            }
        else:
            logger.error(f"Failed to store {source_type} {source_id} in Cordra: {response}")
            return {
                "success": False,
                "message": f"Failed to store in Cordra: {response.get('message', 'Unknown error')}",
                "error_details": response
            }

    except Exception as e:
        logger.exception(f"Exception while storing {source_type} {source_id} in Cordra")
        return {
            "success": False,
            "message": f"Exception while storing in Cordra: {str(e)}"
        }


# ==============================================================================
# API Discovery & Health
# ==============================================================================

@localcontexts_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check and API status
    ---
    tags:
      - LocalContexts
    responses:
      200:
        description: Health check successful with API configuration status
    """
    api_key = current_app.config.get("LC_API_KEY", "")
    is_configured = bool(api_key and api_key != "xxx")

    return jsonify({
        "status": "ok",
        "message": "Local Contexts API v2 integration is running",
        "api_version": "v2",
        "base_url": LOCAL_CONTEXTS_API_BASE_URL,
        "api_key_configured": is_configured,
        "environment": "sandbox" if "sandbox" in LOCAL_CONTEXTS_API_BASE_URL else "production"
    })


@localcontexts_bp.route('/api-info', methods=['GET'])
def get_api_info():
    """
    Get API schema and available endpoints from Local Contexts
    ---
    tags:
      - LocalContexts
    responses:
      200:
        description: API schema retrieved successfully
      503:
        description: Could not connect to Local Contexts API
    """
    try:
        # Call the API root to get available endpoints
        resp = requests.get(
            f"{LOCAL_CONTEXTS_API_BASE_URL}/",
            headers={"Accept": "application/json"},
            timeout=10
        )

        if resp.status_code == 200:
            return jsonify({
                "local_contexts_api": resp.json(),
                "our_endpoints": {
                    "health": "/api/v1/localcontexts/health",
                    "api_info": "/api/v1/localcontexts/api-info",
                    "projects_list": "/api/v1/localcontexts/projects",
                    "project_detail": "/api/v1/localcontexts/projects/<unique_id>",
                    "multi_projects": "/api/v1/localcontexts/projects/multi/<id1,id2,...>",
                    "open_to_collaborate": "/api/v1/localcontexts/notices/open-to-collaborate"
                }
            }), 200
        else:
            return jsonify({"error": f"API returned {resp.status_code}"}), resp.status_code

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 503


# ==============================================================================
# Projects Endpoints (v2 Supported)
# ==============================================================================

@localcontexts_bp.route("/projects", methods=["GET"])
def list_projects():
    """
    List all public Local Contexts projects
    ---
    tags:
      - LocalContexts
    parameters:
      - name: store
        in: query
        type: boolean
        required: false
        description: Whether to store the result in Cordra
    responses:
      200:
        description: List of projects retrieved
      401:
        description: Invalid or missing API key
      500:
        description: Internal server error
    """
    try:
        status, payload, from_cache = _make_request("/projects/")

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "projects_list", "all")
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error listing projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/<string:project_id>", methods=["GET"])
def get_project(project_id):
    """
    Get a specific project by its unique ID
    ---
    tags:
      - LocalContexts
    description: Returns full project details including embedded labels and notices
    parameters:
      - name: project_id
        in: path
        type: string
        required: true
        description: The unique ID of the Local Contexts project
      - name: store
        in: query
        type: boolean
        required: false
        description: Whether to store the result in Cordra
    responses:
      200:
        description: Project retrieved successfully with labels and notices
      401:
        description: Invalid or missing API key
      404:
        description: Project not found
      500:
        description: Internal server error
    """
    try:
        # v2 API requires trailing slash
        status, payload, from_cache = _make_request(f"/projects/{project_id}/", external_id=project_id)

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project", project_id)
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/multi/<string:project_ids>", methods=["GET"])
def get_multi_projects(project_ids):
    """
    Get multiple projects by their unique IDs
    ---
    tags:
      - LocalContexts
    parameters:
      - name: project_ids
        in: path
        type: string
        required: true
        description: "Comma-separated list of project unique IDs (e.g., 'abc123,def456')"
      - name: store
        in: query
        type: boolean
        required: false
        description: Whether to store the result in Cordra
    responses:
      200:
        description: Multiple projects retrieved successfully
      401:
        description: Invalid or missing API key
      404:
        description: One or more projects not found
      500:
        description: Internal server error
    """
    try:
        status, payload, from_cache = _make_request(f"/projects/multi/{project_ids}/")

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "multi_projects", project_ids)
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching multiple projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/multi/date-modified/<string:project_ids>", methods=["GET"])
def get_multi_projects_date_modified(project_ids):
    """
    Get modification dates for multiple projects
    ---
    tags:
      - LocalContexts
    parameters:
      - name: project_ids
        in: path
        type: string
        required: true
        description: Comma-separated list of project unique IDs
    responses:
      200:
        description: Modification dates retrieved successfully
      401:
        description: Invalid or missing API key
      500:
        description: Internal server error
    """
    try:
        status, payload, from_cache = _make_request(f"/projects/multi/date_modified/{project_ids}/")
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project modification dates")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Notices Endpoints (v2 Supported)
# ==============================================================================

@localcontexts_bp.route('/notices/open-to-collaborate', methods=['GET'])
def get_open_to_collaborate_notice():
    """
    Get the Open to Collaborate notice information
    ---
    tags:
      - LocalContexts
    description: Returns details about the Open to Collaborate notice that researchers can use
    responses:
      200:
        description: Open to Collaborate notice retrieved successfully
      401:
        description: Invalid or missing API key
      500:
        description: Internal server error
    """
    try:
        status, payload, from_cache = _make_request("/notices/open_to_collaborate/")
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching Open to Collaborate notice")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Cordra Storage Endpoint
# ==============================================================================

@localcontexts_bp.route('/store', methods=['POST'])
def store_custom_data():
    """
    Store Local Contexts data in Cordra
    ---
    tags:
      - LocalContexts
    parameters:
      - name: body
        in: body
        schema:
          type: object
          required:
            - source_type
            - source_id
            - data
          properties:
            source_type:
              type: string
              description: "Type of data (e.g., project, label)"
            source_id:
              type: string
              description: Identifier for the data
            data:
              type: object
              description: Data to store
    responses:
      200:
        description: Data stored successfully
      400:
        description: Invalid request format
      500:
        description: Internal server error
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        data = request.json
        source_type = data.get('source_type')
        source_id = data.get('source_id')
        local_contexts_data = data.get('data')

        if not source_type or not source_id or not local_contexts_data:
            return jsonify({
                "error": "Missing required fields",
                "required": ["source_type", "source_id", "data"]
            }), 400

        response = store_in_cordra(local_contexts_data, source_type, source_id)
        return jsonify(response)

    except Exception as e:
        logger.exception("Error in store_custom_data endpoint")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Publication-Context Attachment Endpoints (Per Section 7)
# ==============================================================================

@localcontexts_bp.route('/publications/<int:publication_id>/contexts', methods=['GET'])
def list_publication_contexts(publication_id):
    """
    List Local Contexts attached to a publication
    ---
    tags:
      - LocalContexts
    description: "Per Section 7.2: Get all Local Contexts labels/notices attached to a document"
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The publication ID
    responses:
      200:
        description: List of attached Local Contexts
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({"error": "Publication not found"}), 404

        attachments = PublicationLocalContext.query.filter_by(
            publication_id=publication_id
        ).order_by(PublicationLocalContext.display_order).all()

        return jsonify({
            "publication_id": publication_id,
            "total": len(attachments),
            "local_contexts": [a.serialize() for a in attachments]
        }), 200

    except Exception as e:
        logger.exception("Error listing publication contexts")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/publications/<int:publication_id>/contexts', methods=['POST'])
def attach_context_to_publication(publication_id):
    """
    Attach a Local Context to a publication
    ---
    tags:
      - LocalContexts
    description: "Per Section 7.1: Attach Local Context label/notice to a document"
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The publication ID
      - name: body
        in: body
        schema:
          type: object
          required:
            - external_id
            - context_type
          properties:
            external_id:
              type: string
              description: "Local Contexts external ID (e.g., LC-TK-12345)"
            context_type:
              type: string
              enum:
                - TK_LABEL
                - BC_LABEL
                - NOTICE
              description: Type of context
            source_url:
              type: string
              description: URL to the authoritative source
            display_order:
              type: integer
              description: Display order (default 0)
            user_id:
              type: integer
              description: User performing the action
    responses:
      201:
        description: Context attached successfully
      400:
        description: Invalid request or context type
      404:
        description: Publication not found
      409:
        description: Context already attached
      500:
        description: Internal server error
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({"error": "Publication not found"}), 404

        data = request.json
        external_id = data.get('external_id')
        context_type = data.get('context_type')
        source_url = data.get('source_url')
        display_order = data.get('display_order', 0)
        user_id = data.get('user_id')

        if not external_id or not context_type:
            return jsonify({
                "error": "Missing required fields",
                "required": ["external_id", "context_type"]
            }), 400

        # Validate context type per Section 6
        if not LocalContextType.is_valid(context_type):
            return jsonify({
                "error": f"Invalid context_type: {context_type}",
                "valid_types": LocalContextType.VALID_TYPES
            }), 400

        # Get or create cached context
        context, created = LocalContext.get_or_create(
            external_id=external_id,
            context_type=context_type,
            source_url=source_url
        )

        if created:
            db.session.flush()  # Get ID for the new context

        # Check if already attached
        existing = PublicationLocalContext.query.filter_by(
            publication_id=publication_id,
            local_context_id=context.id
        ).first()

        if existing:
            return jsonify({
                "error": "Context already attached to this publication",
                "attachment_id": existing.id
            }), 409

        # Create attachment
        attachment = PublicationLocalContext(
            publication_id=publication_id,
            local_context_id=context.id,
            display_order=display_order,
            attached_by=user_id
        )
        db.session.add(attachment)

        # Audit log per Section 11
        LocalContextAuditLog.log(
            action='ATTACH',
            publication_id=publication_id,
            local_context_id=context.id,
            external_id=external_id,
            user_id=user_id,
            details={
                'context_type': context_type,
                'source_url': source_url
            },
            ip_address=request.remote_addr
        )

        db.session.commit()

        logger.info(f"Attached Local Context {external_id} to publication {publication_id}")

        return jsonify({
            "message": "Context attached successfully",
            "attachment": attachment.serialize()
        }), 201

    except ValueError as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        logger.exception("Error attaching context to publication")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/publications/<int:publication_id>/contexts/<int:context_id>', methods=['DELETE'])
def detach_context_from_publication(publication_id, context_id):
    """
    Detach a Local Context from a publication
    ---
    tags:
      - LocalContexts
    description: Remove the association between a publication and a Local Context
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The publication ID
      - name: context_id
        in: path
        type: integer
        required: true
        description: The local_context_id to detach
      - name: user_id
        in: query
        type: integer
        required: false
        description: User performing the action (for audit)
    responses:
      200:
        description: Context detached successfully
      404:
        description: Attachment not found
      500:
        description: Internal server error
    """
    try:
        attachment = PublicationLocalContext.query.filter_by(
            publication_id=publication_id,
            local_context_id=context_id
        ).first()

        if not attachment:
            return jsonify({"error": "Attachment not found"}), 404

        user_id = request.args.get('user_id', type=int)
        external_id = attachment.local_context.external_id if attachment.local_context else None

        # Audit log per Section 11
        LocalContextAuditLog.log(
            action='DETACH',
            publication_id=publication_id,
            local_context_id=context_id,
            external_id=external_id,
            user_id=user_id,
            details={'removed_at': datetime.utcnow().isoformat()},
            ip_address=request.remote_addr
        )

        db.session.delete(attachment)
        db.session.commit()

        logger.info(f"Detached Local Context {context_id} from publication {publication_id}")

        return jsonify({
            "message": "Context detached successfully",
            "publication_id": publication_id,
            "local_context_id": context_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error detaching context from publication")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Cache Management Endpoints
# ==============================================================================

@localcontexts_bp.route('/cache/<string:external_id>', methods=['GET'])
def get_cached_context(external_id):
    """
    Get cached Local Context by external ID
    ---
    tags:
      - LocalContexts
    parameters:
      - name: external_id
        in: path
        type: string
        required: true
        description: The Local Contexts external ID
    responses:
      200:
        description: Cached context found
      404:
        description: Not in cache
    """
    try:
        cached = LocalContext.get_by_external_id(external_id)
        if not cached:
            return jsonify({"error": "Not found in cache"}), 404

        # Check for stale cache and trigger blocking resync
        response_data = cached.serialize()
        if is_cache_stale(cached.cached_at):
            logger.info(f"Cache stale for {external_id}, attempting blocking resync")
            success, updated = _resync_stale_cache(cached, timeout=RESYNC_TIMEOUT_SECONDS)

            if success and updated:
                response_data = updated.serialize()
                response_data['_resynced'] = True
            else:
                # Serve stale data with warning header
                response_data['_cache_stale'] = True
                response_data['_cache_note'] = f"Data is stale (>{CACHE_TTL_DAYS} days old). Resync failed or timed out."
                response = jsonify(response_data)
                response.headers['X-Cache-Stale'] = 'true'
                return response, 200

        return jsonify(response_data), 200
    except Exception as e:
        logger.exception("Error getting cached context")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/cache/<string:external_id>/sync', methods=['POST'])
def sync_cached_context(external_id):
    """
    Sync cached context with Local Contexts Hub
    ---
    tags:
      - LocalContexts
    description: Fetch fresh data from Hub and update local cache
    parameters:
      - name: external_id
        in: path
        type: string
        required: true
        description: The Local Contexts external ID
    responses:
      200:
        description: Cache synced successfully
      404:
        description: Context not found on Hub
      500:
        description: Internal server error
    """
    try:
        # Fetch from Hub
        status, payload, from_cache = _make_request(f"/projects/{external_id}/", external_id=external_id)

        if status != 200:
            return jsonify(payload), status

        # Update cache
        cached = LocalContext.get_by_external_id(external_id)
        context_type = cached.context_type if cached else LocalContextType.NOTICE

        context = _cache_context_from_hub(external_id, context_type, payload)

        # Audit log
        LocalContextAuditLog.log(
            action='SYNC',
            external_id=external_id,
            local_context_id=context.id,
            details={'synced_from': 'hub', 'status': 'success'}
        )
        db.session.commit()

        return jsonify({
            "message": "Cache synced successfully",
            "context": context.serialize()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error syncing cached context")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/audit-log', methods=['GET'])
def get_audit_log():
    """
    Get audit log for Local Contexts operations
    ---
    tags:
      - LocalContexts
    parameters:
      - name: publication_id
        in: query
        type: integer
        required: false
        description: Filter by publication ID
      - name: external_id
        in: query
        type: string
        required: false
        description: Filter by external ID
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Maximum number of entries to return
    responses:
      200:
        description: Audit log entries
    """
    try:
        query = LocalContextAuditLog.query

        publication_id = request.args.get('publication_id', type=int)
        external_id = request.args.get('external_id')
        limit = request.args.get('limit', 50, type=int)

        if publication_id:
            query = query.filter_by(publication_id=publication_id)
        if external_id:
            query = query.filter_by(external_id=external_id)

        entries = query.order_by(LocalContextAuditLog.created_at.desc()).limit(limit).all()

        return jsonify({
            "total": len(entries),
            "entries": [e.serialize() for e in entries]
        }), 200

    except Exception as e:
        logger.exception("Error getting audit log")
        return jsonify({"error": str(e)}), 500
