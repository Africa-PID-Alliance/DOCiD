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
"""

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional, Union
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
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


def _make_request(path: str, params: dict = None, method: str = "GET", data: dict = None, timeout: int = 30):
    """
    Make a request to the Local Contexts API v2

    Args:
        path: API path to call (should include trailing slash for v2)
        params: URL parameters for the request
        method: HTTP method (GET, POST, etc.)
        data: Request body data (for POST)
        timeout: Request timeout in seconds

    Returns:
        Tuple of (status_code, json_response)
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key or api_key == "xxx":
        return 401, {"error": "Local Contexts API key not configured. Set LC_API_KEY in .env"}

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
            return 400, {"error": f"Unsupported HTTP method: {method}"}

        # Handle response
        if resp.status_code == 200:
            try:
                return 200, resp.json()
            except ValueError:
                return 200, {"raw_response": resp.text}
        elif resp.status_code == 401:
            return 401, {"error": "Invalid API key", "detail": "Check your LC_API_KEY configuration"}
        elif resp.status_code == 404:
            return 404, {"error": "Resource not found", "path": path}
        else:
            try:
                error_data = resp.json()
            except ValueError:
                error_data = {"text": resp.text}
            return resp.status_code, {"error": f"API returned {resp.status_code}", "details": error_data}

    except requests.exceptions.Timeout:
        logger.error(f"Request timeout for {url}")
        return 504, {"error": "Request timeout", "url": url}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Connection error: {str(e)}")
        return 503, {"error": "Connection error", "details": str(e)}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 500, {"error": str(e)}


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
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Health check and API status",
    "responses": {
        200: {"description": "Health check successful with API configuration status"}
    }
})
def health_check():
    """Health check endpoint with configuration status"""
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
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Get API schema and available endpoints from Local Contexts",
    "responses": {
        200: {"description": "API schema retrieved successfully"},
        503: {"description": "Could not connect to Local Contexts API"}
    }
})
def get_api_info():
    """
    Fetch the API discovery endpoint from Local Contexts.
    This returns the available endpoints and their structure.
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
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "List all public Local Contexts projects",
    "parameters": [
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra"
        }
    ],
    "responses": {
        200: {"description": "List of projects retrieved"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "Internal server error"}
    }
})
def list_projects():
    """List all public Local Contexts projects"""
    try:
        status, payload = _make_request("/projects/")

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "projects_list", "all")
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error listing projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/<string:project_id>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Get a specific project by its unique ID",
    "description": "Returns full project details including embedded labels and notices",
    "parameters": [
        {
            "name": "project_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The unique ID of the Local Contexts project"
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra"
        }
    ],
    "responses": {
        200: {"description": "Project retrieved successfully with labels and notices"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "Project not found"},
        500: {"description": "Internal server error"}
    }
})
def get_project(project_id):
    """
    Retrieve a specific Local Contexts project by its unique ID.
    The response includes embedded labels and notices for the project.
    """
    try:
        # v2 API requires trailing slash
        status, payload = _make_request(f"/projects/{project_id}/")

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project", project_id)
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/multi/<string:project_ids>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Get multiple projects by their unique IDs",
    "parameters": [
        {
            "name": "project_ids",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Comma-separated list of project unique IDs (e.g., 'abc123,def456')"
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra"
        }
    ],
    "responses": {
        200: {"description": "Multiple projects retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
        404: {"description": "One or more projects not found"},
        500: {"description": "Internal server error"}
    }
})
def get_multi_projects(project_ids):
    """
    Retrieve multiple Local Contexts projects in a single request.
    Pass comma-separated project IDs.
    """
    try:
        status, payload = _make_request(f"/projects/multi/{project_ids}/")

        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "multi_projects", project_ids)
            payload["cordra_storage"] = cordra_response

        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching multiple projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route("/projects/multi/date-modified/<string:project_ids>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Get modification dates for multiple projects",
    "parameters": [
        {
            "name": "project_ids",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "Comma-separated list of project unique IDs"
        }
    ],
    "responses": {
        200: {"description": "Modification dates retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "Internal server error"}
    }
})
def get_multi_projects_date_modified(project_ids):
    """
    Get the date_modified for multiple projects.
    Useful for cache invalidation.
    """
    try:
        status, payload = _make_request(f"/projects/multi/date_modified/{project_ids}/")
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project modification dates")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Notices Endpoints (v2 Supported)
# ==============================================================================

@localcontexts_bp.route('/notices/open-to-collaborate', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Get the Open to Collaborate notice information",
    "description": "Returns details about the Open to Collaborate notice that researchers can use",
    "responses": {
        200: {"description": "Open to Collaborate notice retrieved successfully"},
        401: {"description": "Invalid or missing API key"},
        500: {"description": "Internal server error"}
    }
})
def get_open_to_collaborate_notice():
    """Get the Open to Collaborate notice from Local Contexts"""
    try:
        status, payload = _make_request("/notices/open_to_collaborate/")
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching Open to Collaborate notice")
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# Deprecated/Placeholder Endpoints
# These endpoints were in the original implementation but are NOT available
# in the LocalContexts API v2. They are kept for backwards compatibility
# but return informative error messages.
# ==============================================================================

@localcontexts_bp.route('/notice-types', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "summary": "[NOT AVAILABLE IN v2] List notice types",
    "deprecated": True,
    "responses": {
        501: {"description": "Endpoint not available in LocalContexts API v2"}
    }
})
def get_notice_types():
    """
    DEPRECATED: This endpoint is not available in LocalContexts API v2.
    Notice types are embedded within project responses.
    """
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": "Notice types are embedded within project responses. Use /projects/<id> instead.",
        "documentation": "https://github.com/localcontexts/localcontextshub/wiki/API-Documentation",
        "available_notices": [
            "TK Notice",
            "BC Notice",
            "Attribution Incomplete Notice",
            "Open to Collaborate Notice"
        ]
    }), 501


@localcontexts_bp.route('/label-types', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "summary": "[NOT AVAILABLE IN v2] List label types",
    "deprecated": True,
    "responses": {
        501: {"description": "Endpoint not available in LocalContexts API v2"}
    }
})
def get_label_types():
    """
    DEPRECATED: This endpoint is not available in LocalContexts API v2.
    Label types are embedded within project responses.
    """
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": "Label information is embedded within project responses. Use /projects/<id> instead.",
        "documentation": "https://github.com/localcontexts/localcontextshub/wiki/API-Documentation",
        "label_categories": {
            "TK Labels": "Traditional Knowledge Labels - community-specific",
            "BC Labels": "Biocultural Labels - community-specific"
        }
    }), 501


@localcontexts_bp.route('/communities', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "summary": "[NOT AVAILABLE IN v2] List communities",
    "deprecated": True,
    "responses": {
        501: {"description": "Endpoint not available in LocalContexts API v2"}
    }
})
def get_communities():
    """
    DEPRECATED: This endpoint is not available in LocalContexts API v2.
    Community information is embedded within project responses.
    """
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": "Community information is embedded within project responses. Use /projects/<id> instead.",
        "suggestion": "Ask the LocalContexts team about community listing endpoints"
    }), 501


@localcontexts_bp.route('/communities/<community_id>', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "summary": "[NOT AVAILABLE IN v2] Get community by ID",
    "deprecated": True,
    "responses": {
        501: {"description": "Endpoint not available in LocalContexts API v2"}
    }
})
def get_community(community_id):
    """DEPRECATED: Not available in LocalContexts API v2"""
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "requested_id": community_id
    }), 501


@localcontexts_bp.route('/communities/<community_id>/notices', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_community_notices(community_id):
    """DEPRECATED: Not available in LocalContexts API v2"""
    return jsonify({"error": "Endpoint not available in LocalContexts API v2"}), 501


@localcontexts_bp.route('/communities/<community_id>/labels', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_community_labels(community_id):
    """DEPRECATED: Not available in LocalContexts API v2"""
    return jsonify({"error": "Endpoint not available in LocalContexts API v2"}), 501


@localcontexts_bp.route("/labels/<string:label_id>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "summary": "[NOT AVAILABLE IN v2] Get label by ID",
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_label(label_id):
    """DEPRECATED: Labels are embedded in project responses, not fetchable individually"""
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": "Labels are embedded in project responses. Use /projects/<id> to get project with labels.",
        "requested_label_id": label_id
    }), 501


@localcontexts_bp.route('/researcher-notices/<notice_id>', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_research_notice(notice_id):
    """DEPRECATED: Not available in LocalContexts API v2"""
    return jsonify({"error": "Endpoint not available in LocalContexts API v2"}), 501


@localcontexts_bp.route('/projects/<project_id>/labels', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_project_labels(project_id):
    """DEPRECATED: Labels are embedded in the project response"""
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": f"Use /projects/{project_id} instead - labels are embedded in the project response"
    }), 501


@localcontexts_bp.route('/projects/<project_id>/notices', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Not available in v2"}}
})
def get_project_notices(project_id):
    """DEPRECATED: Notices are embedded in the project response"""
    return jsonify({
        "error": "Endpoint not available in LocalContexts API v2",
        "message": f"Use /projects/{project_id} instead - notices are embedded in the project response"
    }), 501


@localcontexts_bp.route('/projects/search', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts - Deprecated"],
    "deprecated": True,
    "responses": {501: {"description": "Search not available in v2"}}
})
def search_projects():
    """DEPRECATED: Search is not available in LocalContexts API v2"""
    query = request.args.get('q', '')
    return jsonify({
        "error": "Search endpoint not available in LocalContexts API v2",
        "query": query,
        "suggestion": "Use /projects to list all projects"
    }), 501


# ==============================================================================
# Cordra Storage Endpoint
# ==============================================================================

@localcontexts_bp.route('/store', methods=['POST'])
@swag_from({
    "tags": ["LocalContexts"],
    "summary": "Store Local Contexts data in Cordra",
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "schema": {
                "type": "object",
                "required": ["source_type", "source_id", "data"],
                "properties": {
                    "source_type": {"type": "string", "description": "Type of data (e.g., project, label)"},
                    "source_id": {"type": "string", "description": "Identifier for the data"},
                    "data": {"type": "object", "description": "Data to store"}
                }
            }
        }
    ],
    "responses": {
        200: {"description": "Data stored successfully"},
        400: {"description": "Invalid request format"},
        500: {"description": "Internal server error"}
    }
})
def store_custom_data():
    """Store custom Local Contexts data in Cordra"""
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
