# app/routes/cordra.py
from flask import Blueprint, jsonify, request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import json
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
import re
from typing import Dict, Tuple, Optional, Union
import requests
from datetime import datetime
import time
from app import cache
from app.service_codra import deposit_metadata,  list_operations ,assign_doi_indigenous_knowledge,assign_doi_container_id,assign_doi_patent,assign_doi_user,assign_identifier_apa_handle
from app.service_codra import push_apa_metadata

# Configure logging with more detail
logger = logging.getLogger("cordoi_api_logger")
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("logs/cordoi_api.log", maxBytes=1000000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Blueprint definition
cordoi_bp = Blueprint("cordoi", __name__, url_prefix="/api/v1/cordoi")

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

        response = push_apa_metadata(metadata)
        return jsonify(response), 200 if response.get("success") else 400

    except Exception as e:
        logger.error(f"Error in /push-apa-sample: {str(e)}", exc_info=True)
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500
   
@cordoi_bp.route("/assign-identifier/apa-handle", methods=["POST"])
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
        response = assign_identifier_apa_handle()
        
        if response.get("success"):
            return jsonify(response), 200
        else:
            return jsonify(response), 500

    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@cordoi_bp.route("/assign-doi/indigenous-knowledge", methods=["POST"])
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
        data = request.get_json()
        response = assign_doi_indigenous_knowledge(
            doi=data.get("doi"),
            name=data.get("name"),
            description=data.get("description"),
            description2=data.get("description2", "")
        )
        return jsonify(response), 200 if response.get("success") else 400
    except Exception as e:
        return jsonify({"error": f"Failed to assign DOI: {str(e)}"}), 500

@cordoi_bp.route("/assign-doi/container-id", methods=["POST"])
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
        data = request.get_json()

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
        return jsonify(response), 200
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500



@cordoi_bp.route("/assign-doi/patent", methods=["POST"])
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
    data = request.get_json()
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
            owner=data.get("owner", "")
        )
        return jsonify(response), 200 if response.get("success") else 400
    except KeyError as e:
        return jsonify({"error": f"Missing required parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@cordoi_bp.route("/assign-doi/user", methods=["POST"])
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
    data = request.get_json()
    response =  assign_doi_user(
        username=data.get("username"),
        password=data.get("password"),
        email=data.get("email"),
        role=data.get("role"),
        metadata=data.get("metadata", {})
    )
    return jsonify(response)

@cordoi_bp.route("/deposit-metadata", methods=["GET"])
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
        response = deposit_metadata(example_metadata, target_id="your_target_id")
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Failed to deposit CODRA metadata: {str(e)}"}), 500

@cordoi_bp.route("/list-operations", methods=["GET"])
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

    except Exception as e:
        return jsonify({
            "error": f"Failed to list operations: {str(e)}"
        }), 500

