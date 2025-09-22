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

# Local Contexts API base URL (using sandbox for version 2)
LOCAL_CONTEXTS_API_BASE_URL = "https://sandbox.localcontextshub.org/api/v2"

def _make_request(path: str, params: dict = None, method: str = "GET", data: dict = None):
    """
    Make a request to the Local Contexts API
    
    Args:
        path: API path to call (without base URL)
        params: URL parameters for the request
        method: HTTP method (GET, POST, etc.)
        data: Request body data (for POST)
        
    Returns:
        Tuple of (status_code, json_response)
    """
    api_key = current_app.config.get("LC_API_KEY")
    if not api_key:
        raise RuntimeError("Local Contexts API key not configured (LC_API_KEY)")
    
    url = f"{LOCAL_CONTEXTS_API_BASE_URL}{path}"
    headers = {"x-api-key": api_key, "Accept": "application/json"}
    
    if method == "POST":
        headers["Content-Type"] = "application/json"
    
    logger.info(f"Calling Local Contexts {url} with method={method}, params={params}")
    
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, params=params or {})
        elif method == "POST":
            resp = requests.post(url, headers=headers, params=params or {}, json=data)
        else:
            return 400, {"error": f"Unsupported HTTP method: {method}"}
        
        try:
            response_data = resp.json()
        except ValueError:
            response_data = {"error": "Invalid JSON response", "text": resp.text}
        
        return resp.status_code, response_data
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return 500, {"error": str(e)}


def store_in_cordra(data: Dict[str, Any], source_type: str, source_id: str) -> Dict[str, Any]:
    """
    Store data from Local Contexts in Cordra
    
    Args:
        data: Data to store
        source_type: Type of Local Contexts resource (e.g., "community", "label")
        source_id: ID of the resource from Local Contexts
        
    Returns:
        Dict containing response from Cordra
    """
    try:
        # Prepare metadata for Cordra
        metadata = {
            "local_contexts_data": data,
            "local_contexts_source_type": source_type,
            "local_contexts_source_id": source_id,
            "api_version": "v2"
        }
        
        # Push data to Cordra
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


# Routes
@localcontexts_bp.route('/health', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "responses": {
        200: {"description": "Health check successful."}
    }
})
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "Local Contexts API integration is running"
    })


# ------------------------------------------------------------------------------
# Get Project by ID
# ------------------------------------------------------------------------------
@localcontexts_bp.route("/projects/<string:project_id>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "project_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the Local Contexts project."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Project retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Project not found."},
        500: {"description": "Internal server error."}
    }
})
def get_project(project_id):
    """
    Retrieve a specific Local Contexts project by its ID.
    """
    try:
        status, payload = _make_request(f"/projects/{project_id}")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project", project_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching Project")
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------------------
# Get Label by ID
# ------------------------------------------------------------------------------
@localcontexts_bp.route("/labels/<string:label_id>", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "label_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the Local Contexts label."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Label retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Label not found."},
        500: {"description": "Internal server error."}
    }
})
def get_label(label_id):
    """
    Retrieve a specific Local Contexts label by its ID.
    """
    try:
        status, payload = _make_request(f"/labels/{label_id}")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "label", label_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching Label")
        return jsonify({"error": str(e)}), 500


# ------------------------------------------------------------------------------
# List/Search Projects
# ------------------------------------------------------------------------------
@localcontexts_bp.route("/projects", methods=["GET"])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "communityId",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter projects by community ID."
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Page number for pagination."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "List of projects retrieved."},
        500: {"description": "Internal server error."}
    }
})
def list_projects():
    """
    List or search Local Contexts projects.
    """
    try:
        params = request.args.to_dict()
        store_param = params.pop('store', 'false') if 'store' in params else 'false'
        
        status, payload = _make_request("/projects", params=params)
        
        # Option to store in Cordra
        store = store_param.lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            query_str = "&".join([f"{k}={v}" for k, v in params.items()])
            cordra_response = store_in_cordra(payload, "projects_list", f"query_{query_str}")
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error listing Projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/notice-types', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Notice types retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        500: {"description": "Internal server error."}
    }
})
def get_notice_types():
    """Get all notice types from Local Contexts"""
    try:
        status, payload = _make_request("/notice-types")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "notice_types", "all")
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching notice types")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/label-types', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Label types retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        500: {"description": "Internal server error."}
    }
})
def get_label_types():
    """Get all label types from Local Contexts"""
    try:
        status, payload = _make_request("/label-types")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "label_types", "all")
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching label types")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/communities', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "name",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter communities by name."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Communities retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        500: {"description": "Internal server error."}
    }
})
def get_communities():
    """Get communities from Local Contexts"""
    try:
        params = request.args.to_dict()
        store_param = params.pop('store', 'false') if 'store' in params else 'false'
        
        status, payload = _make_request("/communities", params=params)
        
        # Option to store in Cordra
        store = store_param.lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "communities", "all")
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching communities")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/communities/<community_id>', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "community_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the community."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Community retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Community not found."},
        500: {"description": "Internal server error."}
    }
})
def get_community(community_id):
    """Get a specific community by ID"""
    try:
        status, payload = _make_request(f"/communities/{community_id}")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "community", community_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching community")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/communities/<community_id>/notices', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "community_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the community."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Community notices retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Community not found."},
        500: {"description": "Internal server error."}
    }
})
def get_community_notices(community_id):
    """Get notices for a specific community"""
    try:
        status, payload = _make_request(f"/communities/{community_id}/notices")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "community_notices", community_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching community notices")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/communities/<community_id>/labels', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "community_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the community."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Community labels retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Community not found."},
        500: {"description": "Internal server error."}
    }
})
def get_community_labels(community_id):
    """Get labels for a specific community"""
    try:
        status, payload = _make_request(f"/communities/{community_id}/labels")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "community_labels", community_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching community labels")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/researcher-notices/<notice_id>', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "notice_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the researcher notice."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Researcher notice retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Notice not found."},
        500: {"description": "Internal server error."}
    }
})
def get_research_notice(notice_id):
    """Get a specific research notice"""
    try:
        status, payload = _make_request(f"/researcher-notices/{notice_id}")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "researcher_notice", notice_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching researcher notice")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/projects/<project_id>/labels', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "project_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the project."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Project labels retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Project not found."},
        500: {"description": "Internal server error."}
    }
})
def get_project_labels(project_id):
    """Get labels for a specific project"""
    try:
        status, payload = _make_request(f"/projects/{project_id}/labels")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project_labels", project_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project labels")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/projects/<project_id>/notices', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "project_id",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The ID of the project."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Project notices retrieved successfully."},
        401: {"description": "Unauthorized or missing API key."},
        404: {"description": "Project not found."},
        500: {"description": "Internal server error."}
    }
})
def get_project_notices(project_id):
    """Get notices for a specific project"""
    try:
        status, payload = _make_request(f"/projects/{project_id}/notices")
        
        # Option to store in Cordra
        store = request.args.get('store', 'false').lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project_notices", project_id)
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error fetching project notices")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/projects/search', methods=['GET'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "q",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Search query."
        },
        {
            "name": "store",
            "in": "query",
            "type": "boolean",
            "required": False,
            "description": "Whether to store the result in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Search results retrieved successfully."},
        400: {"description": "Missing search query."},
        401: {"description": "Unauthorized or missing API key."},
        500: {"description": "Internal server error."}
    }
})
def search_projects():
    """Search for projects"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Missing search query. Please provide a 'q' parameter."}), 400
        
        params = request.args.to_dict()
        store_param = params.pop('store', 'false') if 'store' in params else 'false'
        
        status, payload = _make_request("/projects", params={"search": query})
        
        # Option to store in Cordra
        store = store_param.lower() == 'true'
        if store and status == 200 and 'error' not in payload:
            cordra_response = store_in_cordra(payload, "project_search", f"query_{query}")
            payload["cordra_storage"] = cordra_response
        
        return jsonify(payload), status
    except Exception as e:
        logger.exception("Error searching projects")
        return jsonify({"error": str(e)}), 500


@localcontexts_bp.route('/store', methods=['POST'])
@swag_from({
    "tags": ["LocalContexts"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "schema": {
                "type": "object",
                "required": ["source_type", "source_id", "data"],
                "properties": {
                    "source_type": {
                        "type": "string",
                        "description": "Type of data being stored (e.g., custom_data)."
                    },
                    "source_id": {
                        "type": "string",
                        "description": "Identifier for the data."
                    },
                    "data": {
                        "type": "object",
                        "description": "Data to store in Cordra."
                    }
                }
            },
            "required": True,
            "description": "Data to store in Cordra."
        }
    ],
    "responses": {
        200: {"description": "Data stored successfully."},
        400: {"description": "Invalid request format."},
        500: {"description": "Internal server error."}
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
                "error": "Missing required fields. Please provide 'source_type', 'source_id', and 'data'."
            }), 400
        
        response = store_in_cordra(local_contexts_data, source_type, source_id)
        return jsonify(response)
    
    except Exception as e:
        logger.exception("Error in store_custom_data endpoint")
        return jsonify({"error": str(e)}), 500

 