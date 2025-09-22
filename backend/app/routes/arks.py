# app/routes/arks.py

from flask import Blueprint, jsonify, request
import requests
import logging

# https://arks.org
# https://ezid.cdlib.org/doc/apidoc.html#authentication

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define ARKS Blueprint
arks_bp = Blueprint("arks", __name__, url_prefix="/api/v1/arks")

# ARKS API Configuration
ARKS_CONFIG = {
    "API_URL": "https://example-arks.org/api/",
    "API_KEY": "api-key-here",  
}

@arks_bp.route("/create", methods=["POST"])
def create_ark():
    """
    Create a new ARK identifier.

    ---
    tags:
      - ARKS
    parameters:
      - name: target_url
        in: body
        required: true
        schema:
          type: string
          description: The target URL to associate with the ARK.
      - name: metadata
        in: body
        required: false
        schema:
          type: object
          description: Metadata for the ARK.
    responses:
      201:
        description: ARK created successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                ark:
                  type: string
                  description: The generated ARK identifier.
      400:
        description: Bad request, invalid parameters.
      500:
        description: Internal server error.
    """
    try:
        data = request.get_json()
        target_url = data.get("target_url")
        metadata = data.get("metadata", {})

        if not target_url:
            return jsonify({"error": "Missing required parameter: target_url"}), 400

        # Prepare request to ARKS API
        payload = {"target": target_url, "metadata": metadata}
        headers = {"Authorization": f"Bearer {ARKS_CONFIG['API_KEY']}"}

        response = requests.post(f"{ARKS_CONFIG['API_URL']}arks", json=payload, headers=headers)

        if response.status_code == 201:
            return jsonify(response.json()), 201
        else:
            logger.error(f"Failed to create ARK: {response.text}")
            return jsonify({"error": "Failed to create ARK"}), response.status_code

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@arks_bp.route("/resolve/<string:ark_id>", methods=["GET"])
def resolve_ark(ark_id):
    """
    Resolve an ARK identifier to its target URL or metadata.

    ---
    tags:
      - ARKS
    parameters:
      - name: ark_id
        in: path
        required: true
        schema:
          type: string
          description: The ARK identifier to resolve.
    responses:
      200:
        description: Successfully resolved the ARK.
      404:
        description: ARK not found.
      500:
        description: Internal server error.
    """
    try:
        headers = {"Authorization": f"Bearer {ARKS_CONFIG['API_KEY']}"}

        response = requests.get(f"{ARKS_CONFIG['API_URL']}arks/{ark_id}", headers=headers)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        elif response.status_code == 404:
            return jsonify({"error": "ARK not found"}), 404
        else:
            logger.error(f"Failed to resolve ARK: {response.text}")
            return jsonify({"error": "Failed to resolve ARK"}), response.status_code

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@arks_bp.route("/metadata/<string:ark_id>", methods=["GET"])
def get_ark_metadata(ark_id):
    """
    Retrieve metadata for an ARK identifier.

    ---
    tags:
      - ARKS
    parameters:
      - name: ark_id
        in: path
        required: true
        schema:
          type: string
          description: The ARK identifier to retrieve metadata for.
    responses:
      200:
        description: Successfully retrieved ARK metadata.
      404:
        description: Metadata not found for the ARK.
      500:
        description: Internal server error.
    """
    try:
        headers = {"Authorization": f"Bearer {ARKS_CONFIG['API_KEY']}"}

        response = requests.get(f"{ARKS_CONFIG['API_URL']}arks/{ark_id}/metadata", headers=headers)

        if response.status_code == 200:
            return jsonify(response.json()), 200
        elif response.status_code == 404:
            return jsonify({"error": "Metadata not found"}), 404
        else:
            logger.error(f"Failed to retrieve ARK metadata: {response.text}")
            return jsonify({"error": "Failed to retrieve metadata"}), response.status_code

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
