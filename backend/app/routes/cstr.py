# CSTR (China Science and Technology Resource Identification Platform)
# Registration Service: mint and register metadata-rich identifiers for new resources.
# Resolution Service: look up and retrieve metadata by identifier or keywords.
# Association Services: link resources (papers ↔ authors, data ↔ publications) into a navigable graph.

# Analytics: offer usage statistics such as registration and resolution counts
# app/routes/cstr.py 

import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/cstr.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create a Blueprint for CSTR routes
cstr_bp = Blueprint('cstr', __name__, url_prefix='/api/v1/cstr')

# CSTR API base URL (v3)
BASE_URL = "https://www.cstr.cn/openapi/v3"


def _make_request(path: str, params: dict = None, method: str = "GET", data: dict = None):
    """
    Internal helper to make a request to the CSTR API.
    """
    client_id = current_app.config.get("CSTR_CLIENT_ID")
    secret = current_app.config.get("CSTR_SECRET")
    if not client_id or not secret:
        raise RuntimeError("CSTR credentials not configured (CSTR_CLIENT_ID/CSTR_SECRET)")

    url = f"{BASE_URL}{path}"
    headers = {
        "clientId": client_id,
        "secret": secret,
        "app_name": current_app.config.get("CSTR_APP_NAME", "DOCIDClient"),
        "Accept": "application/json"
    }
    if method == "POST":
        headers["Content-Type"] = "application/json"

    logger.info(f"Calling CSTR {url} method={method} params={params}")
    resp = requests.request(method, url, headers=headers, params=params or {}, json=data)
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, {"error": "Invalid JSON response", "text": resp.text}

# --- Health Check ---
@cstr_bp.route('/health', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "responses": { 
        200: {"description": "CSTR integration is healthy."},
        500: {"description": "Internal server error."}
    }
})
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "message": "CSTR API integration is running"
    })

# --- 1. REGISTRATION SERVICE ---

# --- Register new identifiers ---
@cstr_bp.route('/register', methods=['POST'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "res_name",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Template type (e.g. v3_scientific_data, v3_article_data, etc.)"
        },
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "prefix": {"type": "string"},
                    "metadatas": {"type": "array", "items": {"type": "object"}}
                },
                "required": ["prefix", "metadatas"]
            }
        }
    ],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Batch registration submitted"},
        400: {"description": "Client or validation error"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"}
    }
})
def register():
    """Mint & register up to 100 new CSTR IDs in a batch."""
    res_name = request.args.get('res_name')
    status, payload = _make_request(
        '/api/register',
        params={"res_name": res_name},
        method='POST',
        data=request.get_json()
    )
    return jsonify(payload), status

# --- Update existing metadata ---
@cstr_bp.route('/update', methods=['POST'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "res_name",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Template type (same as register)"
        },
        {"$ref": "#/parameters/body"}
    ],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Batch update submitted"},
        400: {"description": "Client or validation error"},
        401: {"description": "Authentication failed"},
        500: {"description": "Internal server error"}
    }
})
def update():
    """Batch-modify metadata for existing CSTR IDs."""
    res_name = request.args.get('res_name')
    status, payload = _make_request(
        '/api/update',
        params={"res_name": res_name},
        method='POST',
        data=request.get_json()
    )
    return jsonify(payload), status

# --- Poll batch task status ---
@cstr_bp.route('/task', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "task_id",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "ID of the batch register/update task"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Batch task status retrieved"},
        404: {"description": "Task not found"},
        500: {"description": "Internal server error"}
    }
})
def batch_status():
    """Check the asynchronous result of a prior register/update call."""
    task_id = request.args.get('task_id')
    status, payload = _make_request(
        '/md/task/detail',
        params={"task_id": task_id}
    )
    return jsonify(payload), status

# --- 2. RESOLUTION SERVICE ---

# --- Fetch single record metadata ---
@cstr_bp.route('/detail', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "identifier",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "CSTR identifier to retrieve"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Metadata object retrieved"},
        404: {"description": "Identifier not found"},
        500: {"description": "Internal server error"}
    }
})
def get_detail():
    """Retrieve full Metadata object for a given CSTR ID."""
    identifier = request.args.get('identifier')
    status, payload = _make_request(
        '/portal/api/detail',
        params={"identifier": identifier}
    )
    return jsonify(payload), status

# --- Search for records by keywords ---
@cstr_bp.route('/search', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "query",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Search keywords"
        },
        {
            "name": "page",
            "in": "query",
            "type": "integer",
            "required": False,
            "default": 1,
            "description": "Page number"
        },
        {
            "name": "page_size",
            "in": "query",
            "type": "integer",
            "required": False,
            "default": 10,
            "description": "Results per page"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Search results retrieved"},
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"}
    }
})
def search():
    """Search for CSTR resources by keywords."""
    query = request.args.get('query')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))
    
    status, payload = _make_request(
        '/portal/api/search',
        params={
            "query": query,
            "page": page,
            "page_size": page_size
        }
    )
    return jsonify(payload), status

# --- 3. ASSOCIATION SERVICES ---

# --- Get related resources ---
@cstr_bp.route('/related', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "identifier",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "CSTR identifier to find related resources for"
        },
        {
            "name": "relation_type",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by specific relation type (e.g., 'cites', 'isPartOf')"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Related resources retrieved"},
        404: {"description": "Identifier not found"},
        500: {"description": "Internal server error"}
    }
})
def get_related():
    """Retrieve resources related to a given CSTR ID."""
    identifier = request.args.get('identifier')
    relation_type = request.args.get('relation_type')
    
    params = {"identifier": identifier}
    if relation_type:
        params["relation_type"] = relation_type
    
    status, payload = _make_request(
        '/portal/api/related',
        params=params
    )
    return jsonify(payload), status

# --- Create relationships between resources ---
@cstr_bp.route('/relate', methods=['POST'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "body",
            "in": "body",
            "required": True,
            "schema": {
                "type": "object",
                "properties": {
                    "source_id": {"type": "string"},
                    "target_id": {"type": "string"},
                    "relation_type": {"type": "string"}
                },
                "required": ["source_id", "target_id", "relation_type"]
            }
        }
    ],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Relationship created"},
        400: {"description": "Invalid parameters"},
        404: {"description": "One or both identifiers not found"},
        500: {"description": "Internal server error"}
    }
})
def create_relation():
    """Create relationship between two CSTR resources."""
    data = request.get_json()
    status, payload = _make_request(
        '/api/relate',
        method='POST',
        data=data
    )
    return jsonify(payload), status

# --- 4. ANALYTICS SERVICES ---

# --- Get usage statistics ---
@cstr_bp.route('/stats', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "identifier",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Optional CSTR identifier to get stats for"
        },
        {
            "name": "prefix",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Optional prefix to get aggregated stats for"
        },
        {
            "name": "start_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Start date for stats (YYYY-MM-DD)"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "End date for stats (YYYY-MM-DD)"
        },
        {
            "name": "stat_type",
            "in": "query",
            "type": "string",
            "required": False,
            "default": "all",
            "description": "Type of statistics to retrieve (registrations, resolutions, all)"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Statistics retrieved"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"}
    }
})
def get_stats():
    """Retrieve usage statistics for CSTR identifiers or prefixes."""
    identifier = request.args.get('identifier')
    prefix = request.args.get('prefix')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    stat_type = request.args.get('stat_type', 'all')
    
    params = {}
    if identifier:
        params["identifier"] = identifier
    if prefix:
        params["prefix"] = prefix
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    params["stat_type"] = stat_type
    
    status, payload = _make_request(
        '/portal/api/stats',
        params=params
    )
    return jsonify(payload), status

# --- Get monthly registration counts ---
@cstr_bp.route('/stats/monthly', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "prefix",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Optional prefix to filter by"
        },
        {
            "name": "year",
            "in": "query",
            "type": "integer",
            "required": False,
            "description": "Year to retrieve stats for"
        }
    ],
    "produces": ["application/json"],
    "responses": {
        200: {"description": "Monthly statistics retrieved"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"}
    }
})
def get_monthly_stats():
    """Retrieve monthly registration counts."""
    prefix = request.args.get('prefix')
    year = request.args.get('year')
    
    params = {}
    if prefix:
        params["prefix"] = prefix
    if year:
        params["year"] = year
    
    status, payload = _make_request(
        '/portal/api/stats/monthly',
        params=params
    )
    return jsonify(payload), status

# --- Get bulk metadata export ---
@cstr_bp.route('/export', methods=['GET'])
@swag_from({
    "tags": ["CSTR"],
    "parameters": [
        {
            "name": "prefix",
            "in": "query",
            "type": "string",
            "required": True,
            "description": "Prefix to export metadata for"
        },
        {
            "name": "format",
            "in": "query",
            "type": "string",
            "required": False,
            "default": "json",
            "description": "Export format (json, xml, csv)"
        },
        {
            "name": "start_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by registration date (YYYY-MM-DD)"
        },
        {
            "name": "end_date",
            "in": "query",
            "type": "string",
            "required": False,
            "description": "Filter by registration date (YYYY-MM-DD)"
        }
    ],
    "produces": ["application/json", "application/xml", "text/csv"],
    "responses": {
        200: {"description": "Export generated successfully"},
        400: {"description": "Invalid parameters"},
        500: {"description": "Internal server error"}
    }
})
def export_metadata():
    """Export bulk metadata for a specific prefix."""
    prefix = request.args.get('prefix')
    format = request.args.get('format', 'json')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    params = {"prefix": prefix, "format": format}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    
    status, payload = _make_request(
        '/portal/api/export',
        params=params
    )
    return jsonify(payload), status