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
import re
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app import db
from app.models import (
    LocalContext, LocalContextType, PublicationLocalContext,
    LocalContextAuditLog, Publications
)
from app.service_codra import push_apa_metadata

# Canonical UUID format used by the LC Hub. Validate every external_id at the
# system boundary so arbitrary strings never reach Hub URLs, logs, or DB rows.
_UUID_RE = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def _normalize_uuid(value: Optional[str]) -> Optional[str]:
    """Lowercase + trim and validate as a canonical UUID. Returns None if invalid."""
    if not value or not isinstance(value, str):
        return None
    candidate = value.strip().lower()
    return candidate if _UUID_RE.match(candidate) else None


def _require_owner_or_403(publication_id: int) -> Tuple[Optional[Publications], Optional[Any]]:
    """Resolve the publication and verify the JWT identity owns it.

    Returns (publication, None) on success or (None, flask_response) on failure
    so callers can `return resp` directly.
    """
    publication = Publications.query.get(publication_id)
    if not publication:
        return None, (jsonify({"error": "Publication not found"}), 404)
    try:
        current_user_id = int(get_jwt_identity())
    except (TypeError, ValueError):
        return None, (jsonify({"error": "Authentication required"}), 401)
    if publication.user_id != current_user_id:
        return None, (jsonify({"error": "Access denied: you do not own this publication"}), 403)
    return publication, None

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
# Switched 2026-05-04 from sandbox to live Hub for LC certification demo (key expires 2026-05-30).
# Env-driven refactor (read from current_app.config) is deferred — see PLAN-live-hub-switch.md.
LOCAL_CONTEXTS_API_BASE_URL = "https://localcontextshub.org/api/v2"

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
            # Labels carry their body text in `label_text`; Notices use `default_text`.
            # Coalesce so Label resyncs don't blank out summary back to None.
            cached.summary = (
                hub_data.get('label_text')
                or hub_data.get('default_text')
                or hub_data.get('description')
                or hub_data.get('summary')
                or cached.summary
            )
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

    # Labels carry their body text in `label_text`; Notices use `default_text`.
    # Coalesce all known shapes so Label payloads don't land with summary=None.
    _summary = (
        hub_data.get('label_text')
        or hub_data.get('default_text')
        or hub_data.get('description')
        or hub_data.get('summary')
    )

    if context:
        # Update existing cache
        context.title = hub_data.get('title') or hub_data.get('name')
        context.summary = _summary
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
            summary=_summary,
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


# Simple in-process LRU for picker autocomplete. Stores the *unbounded* result so
# a cached limit=5 doesn't poison a later limit=20 for the same query.
_SEARCH_CACHE: Dict[str, Tuple[float, list]] = {}
_SEARCH_CACHE_TTL_SECONDS = 300
_SEARCH_RATE_BUCKET: Dict[str, list] = {}  # ip -> list of request timestamps
_SEARCH_RATE_LIMIT_PER_MINUTE = 20

_PRINTABLE_RE = re.compile(r'^[\x20-\x7e]+$')


def _search_rate_limit_check(ip: str) -> bool:
    """Returns True if the request is allowed, False if rate-limited."""
    import time
    now = time.monotonic()
    window = 60.0
    bucket = _SEARCH_RATE_BUCKET.setdefault(ip, [])
    # Drop entries older than the window.
    while bucket and now - bucket[0] > window:
        bucket.pop(0)
    if len(bucket) >= _SEARCH_RATE_LIMIT_PER_MINUTE:
        return False
    bucket.append(now)
    return True


@localcontexts_bp.route("/projects/search", methods=["GET"])
def search_projects():
    """
    Search the Local Contexts Hub by project title.

    Public endpoint backing the picker autocomplete. Forwards to Hub
    ``/projects/?title=<q>`` (confirmed available 2026-05-20). Rate-limited to
    20 requests / minute / IP to protect Hub quota.
    """
    import time
    q_raw = (request.args.get('q') or '').strip()
    try:
        limit = int(request.args.get('limit', '20'))
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    limit = max(1, min(limit, 20))

    if len(q_raw) < 3:
        return jsonify({"error": "q must be at least 3 characters"}), 400
    if not _PRINTABLE_RE.match(q_raw):
        return jsonify({"error": "q contains invalid characters"}), 400

    ip = request.headers.get('X-Forwarded-For', request.remote_addr or 'unknown').split(',')[0].strip()
    if not _search_rate_limit_check(ip):
        return jsonify({"error": "Rate limit exceeded — try again in a minute"}), 429

    cache_key = q_raw.lower()
    cached = _SEARCH_CACHE.get(cache_key)
    if cached and time.monotonic() - cached[0] < _SEARCH_CACHE_TTL_SECONDS:
        return jsonify({"results": cached[1][:limit]}), 200

    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        return jsonify({"error": "LC_API_KEY not configured"}), 503

    try:
        resp = requests.get(
            f"{LOCAL_CONTEXTS_API_BASE_URL}/projects/",
            params={"title": q_raw},
            headers={"x-api-key": api_key, "Accept": "application/json"},
            timeout=10,
        )
    except requests.RequestException as e:
        logger.warning(f"Hub search failed: {e}")
        return jsonify({"error": "Local Contexts Hub temporarily unavailable"}), 503

    if resp.status_code != 200:
        logger.warning(f"Hub search returned {resp.status_code}: {resp.text[:200]}")
        return jsonify({"error": f"Hub returned status {resp.status_code}"}), 502

    payload = resp.json()
    raw_results = payload.get('results', []) if isinstance(payload, dict) else (payload if isinstance(payload, list) else [])

    trimmed = []
    for r in raw_results:
        institutions = []
        for cb in r.get('created_by') or []:
            inst = cb.get('institution') or {}
            if inst.get('name'):
                institutions.append(inst['name'])
        trimmed.append({
            "unique_id": r.get('unique_id'),
            "title": r.get('title'),
            "project_type": r.get('project_type') or 'Other',
            "project_page": r.get('project_page'),
            "contributing_institutions": institutions,
        })

    _SEARCH_CACHE[cache_key] = (time.monotonic(), trimmed)
    return jsonify({"results": trimmed[:limit]}), 200


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

        # Flatten attachment + cached item into a single row per attachment so
        # the frontend can drive both diff (by external_id) and item-level
        # DELETE (by ctx_id, the attachment row PK) without extra round-trips.
        rows = []
        for a in attachments:
            lc = a.local_context
            rows.append({
                "ctx_id": a.id,
                "local_context_id": a.local_context_id,
                "external_id": lc.external_id if lc else None,
                "context_type": lc.context_type if lc else None,
                "project_external_id": a.project_external_id,
                "display_order": a.display_order,
                "attached_at": a.attached_at.isoformat() if a.attached_at else None,
                "title": lc.title if lc else None,
                "summary": lc.summary if lc else None,
                "community_name": lc.community_name if lc else None,
                "image_url": lc.image_url if lc else None,
                "source_url": lc.source_url if lc else None,
                "is_active": lc.is_active if lc else None,
            })

        return jsonify({
            "publication_id": publication_id,
            "total": len(rows),
            "local_contexts": rows,
        }), 200

    except Exception as e:
        logger.exception("Error listing publication contexts")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/publications/<int:publication_id>/contexts', methods=['POST'])
@jwt_required()
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

        publication, err = _require_owner_or_403(publication_id)
        if err:
            return err

        data = request.json
        external_id = data.get('external_id')
        context_type = data.get('context_type')
        source_url = data.get('source_url')
        display_order = data.get('display_order', 0)
        # user_id from payload is ignored — identity comes from the JWT.
        user_id = int(get_jwt_identity())

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

        # Item-level POST always writes project_external_id = NULL (the "legacy"
        # partial index). Use ON CONFLICT DO NOTHING targeted at that index so a
        # duplicate item-level attach does not raise, and so an existing
        # *project-level* attachment for the same item is not treated as a
        # collision (different partial index).
        stmt = pg_insert(PublicationLocalContext.__table__).values(
            publication_id=publication_id,
            local_context_id=context.id,
            project_external_id=None,
            display_order=display_order,
            attached_by=user_id,
        ).on_conflict_do_nothing(
            index_elements=['publication_id', 'local_context_id'],
            index_where=PublicationLocalContext.project_external_id.is_(None),
        ).returning(PublicationLocalContext.__table__.c.id)
        result = db.session.execute(stmt).fetchone()

        if result is None:
            existing = PublicationLocalContext.query.filter_by(
                publication_id=publication_id,
                local_context_id=context.id,
                project_external_id=None,
            ).first()
            db.session.commit()
            return jsonify({
                "error": "Context already attached to this publication",
                "attachment_id": existing.id if existing else None,
            }), 409

        attachment_id = result[0]

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
        attachment = PublicationLocalContext.query.get(attachment_id)

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
@jwt_required()
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
        publication, err = _require_owner_or_403(publication_id)
        if err:
            return err

        # ctx_id semantics: this is the publication_local_contexts row PK
        # (attachment-row), NOT local_contexts.id. Now that the same
        # local_context_id can appear under multiple projects, deleting by
        # local_context_id would be ambiguous.
        attachment = PublicationLocalContext.query.filter_by(
            id=context_id,
            publication_id=publication_id,
        ).first()

        if not attachment:
            return jsonify({"error": "Attachment not found"}), 404

        user_id = int(get_jwt_identity())
        external_id = attachment.local_context.external_id if attachment.local_context else None
        local_context_id = attachment.local_context_id
        project_external_id = attachment.project_external_id

        # Audit log per Section 11
        LocalContextAuditLog.log(
            action='DETACH',
            publication_id=publication_id,
            local_context_id=local_context_id,
            external_id=external_id,
            user_id=user_id,
            details={
                'removed_at': datetime.utcnow().isoformat(),
                'attachment_id': context_id,
                'project_external_id': project_external_id,
            },
            ip_address=request.remote_addr
        )

        db.session.delete(attachment)
        db.session.commit()

        logger.info(f"Detached attachment {context_id} (local_context {local_context_id}) from publication {publication_id}")

        return jsonify({
            "message": "Context detached successfully",
            "publication_id": publication_id,
            "attachment_id": context_id,
            "local_context_id": local_context_id,
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.exception("Error detaching context from publication")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Project-level Attachment Helpers and Endpoints (v1 researcher attachment path)
# ==============================================================================

def _classify_item(payload_kind: str) -> Optional[str]:
    """Map a project-payload kind ('tk_labels'/'bc_labels'/'notice') to LocalContextType."""
    return {
        'tk_labels': LocalContextType.TK_LABEL,
        'bc_labels': LocalContextType.BC_LABEL,
        'notice': LocalContextType.NOTICE,
    }.get(payload_kind)


def _fetch_hub_project_no_side_effects(external_id: str, timeout: int = 10) -> Tuple[bool, Dict[str, Any]]:
    """Plain GET against the Hub. Returns (success, payload_or_error).

    Deliberately does NOT use ``_make_request`` because that helper writes
    audit/inactive flags on 404 which would escape our project-level savepoint.
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        return False, {"error": "LC_API_KEY not configured"}
    try:
        resp = requests.get(
            f"{LOCAL_CONTEXTS_API_BASE_URL}/projects/{external_id}/",
            headers={"x-api-key": api_key, "Accept": "application/json"},
            timeout=timeout,
        )
    except requests.RequestException as e:
        return False, {"error": f"Hub request failed: {e}"}
    if resp.status_code == 200:
        return True, resp.json()
    if resp.status_code == 404:
        return False, {"error": "Project not found on Hub", "status": 404}
    return False, {"error": f"Hub returned status {resp.status_code}", "status": resp.status_code}


def attach_lc_project_to_publication(pub_id: int, external_id: str, user_id: int,
                                     ip_address: Optional[str] = None) -> Dict[str, Any]:
    """Atomically attach all labels + notices from one LC project to a publication.

    Idempotent on duplicate attaches (ON CONFLICT DO NOTHING against the
    non-NULL project partial unique index). Wrapped in a single savepoint per
    project so partial failures rollback cleanly; the outer caller commits the
    session once.
    """
    normalized = _normalize_uuid(external_id)
    if not normalized:
        return {"success": False, "error": "Invalid external_id format", "external_id": external_id}

    ok, project = _fetch_hub_project_no_side_effects(normalized)
    if not ok:
        return {"success": False, "error": project.get('error', 'Hub fetch failed'), "external_id": normalized}

    items: list = []
    for kind in ('tk_labels', 'bc_labels', 'notice'):
        for item in project.get(kind) or []:
            context_type = _classify_item(kind)
            if not context_type:
                continue
            unique_id = item.get('unique_id')
            if not unique_id:
                continue
            items.append((unique_id, context_type, item))

    attached_count = 0

    try:
        with db.session.begin_nested():
            for unique_id, context_type, item in items:
                # Labels carry their body text in `label_text`; Notices use `default_text`.
                # Coalesce so TK/BC labels don't land with summary=None.
                item_summary = (
                    item.get('label_text')
                    or item.get('default_text')
                    or item.get('description')
                )
                # Upsert LocalContext using PostgreSQL ON CONFLICT to avoid SELECT-then-INSERT races.
                lc_stmt = pg_insert(LocalContext.__table__).values(
                    external_id=unique_id,
                    context_type=context_type,
                    title=item.get('name') or item.get('title'),
                    summary=item_summary,
                    community_name=(item.get('community') or {}).get('name') if isinstance(item.get('community'), dict) else None,
                    image_url=item.get('img_url') or item.get('image_url'),
                    source_url=item.get('notice_page') or item.get('label_page'),
                    is_active=True,
                    cached_at=datetime.utcnow(),
                ).on_conflict_do_nothing(index_elements=['external_id']).returning(LocalContext.__table__.c.id)
                result = db.session.execute(lc_stmt).fetchone()
                if result is not None:
                    local_context_id = result[0]
                else:
                    existing = LocalContext.query.filter_by(external_id=unique_id).first()
                    local_context_id = existing.id if existing else None
                if not local_context_id:
                    continue

                # Insert attachment row idempotently against the non-NULL partial unique index.
                plc_stmt = pg_insert(PublicationLocalContext.__table__).values(
                    publication_id=pub_id,
                    local_context_id=local_context_id,
                    project_external_id=normalized,
                    display_order=attached_count,
                    attached_by=user_id,
                ).on_conflict_do_nothing(
                    index_elements=['publication_id', 'local_context_id', 'project_external_id'],
                    index_where=PublicationLocalContext.project_external_id.isnot(None),
                )
                db.session.execute(plc_stmt)
                attached_count += 1

            LocalContextAuditLog.log(
                action='PROJECT_ATTACH',
                publication_id=pub_id,
                local_context_id=None,
                external_id=normalized,
                user_id=user_id,
                details={
                    'item_count': attached_count,
                    'project_title': project.get('title'),
                    'project_page': project.get('project_page'),
                },
                ip_address=ip_address,
            )
    except Exception as e:
        logger.exception(f"attach_lc_project_to_publication failed for {normalized}")
        return {"success": False, "error": str(e), "external_id": normalized}

    return {
        "success": True,
        "external_id": normalized,
        "attached_count": attached_count,
        "project_title": project.get('title'),
    }


@localcontexts_bp.route('/publications/<int:publication_id>/projects', methods=['POST'])
@jwt_required()
def attach_project_to_publication(publication_id):
    """Atomically attach an entire LC project (all its labels + notices) to a publication."""
    publication, err = _require_owner_or_403(publication_id)
    if err:
        return err

    data = request.get_json(silent=True) or {}
    external_id = data.get('external_id')
    normalized = _normalize_uuid(external_id)
    if not normalized:
        return jsonify({"error": "Invalid external_id format (must be canonical UUID)"}), 400

    user_id = int(get_jwt_identity())

    # Clear pending objects before begin_nested() inside the helper — SQLAlchemy
    # flushes pending state into the savepoint, which would entangle unrelated work.
    db.session.expunge_all()

    result = attach_lc_project_to_publication(
        pub_id=publication_id,
        external_id=normalized,
        user_id=user_id,
        ip_address=request.remote_addr,
    )

    if not result.get('success'):
        db.session.rollback()
        status = 502 if 'Hub' in (result.get('error') or '') else 400
        return jsonify(result), status

    db.session.commit()
    return jsonify(result), 201


@localcontexts_bp.route('/publications/<int:publication_id>/projects/<string:external_id>', methods=['DELETE'])
@jwt_required()
def detach_project_from_publication(publication_id, external_id):
    """Atomically detach every attachment under one LC project from a publication."""
    publication, err = _require_owner_or_403(publication_id)
    if err:
        return err

    normalized = _normalize_uuid(external_id)
    if not normalized:
        return jsonify({"error": "Invalid external_id format (must be canonical UUID)"}), 400

    user_id = int(get_jwt_identity())

    rows = PublicationLocalContext.query.filter_by(
        publication_id=publication_id,
        project_external_id=normalized,
    ).all()
    removed = len(rows)

    if removed == 0:
        return jsonify({"success": True, "removed_count": 0, "external_id": normalized}), 200

    try:
        for row in rows:
            db.session.delete(row)
        LocalContextAuditLog.log(
            action='PROJECT_DETACH',
            publication_id=publication_id,
            local_context_id=None,
            external_id=normalized,
            user_id=user_id,
            details={'removed_count': removed},
            ip_address=request.remote_addr,
        )
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.exception("Error detaching project from publication")
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "success": True,
        "removed_count": removed,
        "external_id": normalized,
    }), 200


# ==============================================================================
# Display Aggregation Endpoint (public)
# ==============================================================================

def _hub_projects_multi(uuids: List[str], chunk_size: int = 20, timeout: int = 10) -> Tuple[bool, Dict[str, Dict[str, Any]]]:
    """Fetch multiple projects from the Hub. Returns (success, {uuid: payload}).

    Chunks at ``chunk_size`` to protect against URL-length and per-request Hub
    limits. ``success=False`` indicates the Hub call failed at least once — the
    caller is expected to fall back to cached items for unfetched UUIDs.
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        return False, {}
    out: Dict[str, Dict[str, Any]] = {}
    any_failure = False
    for i in range(0, len(uuids), chunk_size):
        batch = uuids[i:i + chunk_size]
        if not batch:
            continue
        joined = ",".join(batch)
        try:
            resp = requests.get(
                f"{LOCAL_CONTEXTS_API_BASE_URL}/projects/multi/{joined}/",
                headers={"x-api-key": api_key, "Accept": "application/json"},
                timeout=timeout,
            )
        except requests.RequestException:
            any_failure = True
            continue
        if resp.status_code != 200:
            any_failure = True
            continue
        payload = resp.json()
        # The Hub returns either a list or a {results: [...]} envelope.
        items = payload if isinstance(payload, list) else payload.get('results') or payload.get('projects') or []
        for proj in items:
            uid = proj.get('unique_id')
            if uid:
                out[uid] = proj
    return (not any_failure), out


def _project_shape_from_cache(uuid: str, attachments: List[PublicationLocalContext]) -> Dict[str, Any]:
    """Reconstruct a project-shaped object from cached LocalContext rows when the Hub is unreachable."""
    tk_labels, bc_labels, notice = [], [], []
    for a in attachments:
        lc = a.local_context
        if not lc:
            continue
        is_label = lc.context_type in (LocalContextType.TK_LABEL, LocalContextType.BC_LABEL)
        row = {
            "unique_id": lc.external_id,
            "name": lc.title,
            # Labels and Notices use different text-field names on the Hub.
            # Set both for symmetry so the frontend's `label_text || default_text`
            # works regardless of which client reads the synthetic row first.
            "default_text": lc.summary if not is_label else None,
            "label_text": lc.summary if is_label else None,
            "img_url": lc.image_url,
            "language": "en",
            "language_tag": "en",
            "translations": [],
        }
        if lc.context_type == LocalContextType.TK_LABEL:
            tk_labels.append(row)
        elif lc.context_type == LocalContextType.BC_LABEL:
            bc_labels.append(row)
        elif lc.context_type == LocalContextType.NOTICE:
            notice.append(row)
    return {
        "project_external_id": uuid,
        "title": "[Local Contexts Hub temporarily unavailable]",
        "project_page": f"https://localcontextshub.org/projects/{uuid}/",
        "contributing_institutions": [],
        "tk_labels": tk_labels,
        "bc_labels": bc_labels,
        "notice": notice,
        "_stale": True,
    }


@localcontexts_bp.route('/publications/<int:publication_id>/projects-display', methods=['GET'])
def projects_display(publication_id):
    """Return ``{projects, legacy}`` for the DOCiD detail page.

    Public — no JWT required. Hub API key stays server-side. One round-trip to
    Hub ``/projects/multi/`` regardless of project count (chunked at 20). Falls
    back to cached LocalContext rows for unreachable Hub.
    """
    publication = Publications.query.get(publication_id)
    if not publication:
        return jsonify({"error": "Publication not found"}), 404

    attachments = PublicationLocalContext.query.filter_by(
        publication_id=publication_id,
    ).all()

    projects_buckets: Dict[str, List[PublicationLocalContext]] = {}
    legacy_rows = []
    for a in attachments:
        if a.project_external_id:
            projects_buckets.setdefault(a.project_external_id, []).append(a)
        else:
            lc = a.local_context
            if lc:
                legacy_rows.append({
                    "ctx_id": a.id,
                    "external_id": lc.external_id,
                    "context_type": lc.context_type,
                    "title": lc.title,
                    "summary": lc.summary,
                    "image_url": lc.image_url,
                    "source_url": lc.source_url,
                    "community_name": lc.community_name,
                })

    uuids = list(projects_buckets.keys())
    hub_ok, hub_data = _hub_projects_multi(uuids) if uuids else (True, {})

    projects_out = []
    for uuid, atts in projects_buckets.items():
        hub_proj = hub_data.get(uuid)
        if hub_proj:
            projects_out.append({
                "project_external_id": uuid,
                "title": hub_proj.get('title'),
                "project_page": hub_proj.get('project_page'),
                "contributing_institutions": [
                    (cb.get('institution') or {}).get('name')
                    for cb in (hub_proj.get('created_by') or [])
                    if (cb.get('institution') or {}).get('name')
                ],
                "tk_labels": hub_proj.get('tk_labels') or [],
                "bc_labels": hub_proj.get('bc_labels') or [],
                "notice": hub_proj.get('notice') or [],
                "_stale": False,
            })
        else:
            projects_out.append(_project_shape_from_cache(uuid, atts))

    return jsonify({"projects": projects_out, "legacy": legacy_rows}), 200


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
