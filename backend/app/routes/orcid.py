# app/routes/orcid.py
from flask import Blueprint, jsonify, request
import requests
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from app import db
from app.models import DocIdLookup
from app.service_crossref import get_crossref_doi
from sqlalchemy.sql import func
from habanero import Crossref
import urllib.parse

# ORCID API base URL (replace with the actual URL)
ORCID_API_URL = "https://pub.orcid.org/v3.0/"

orcid_bp = Blueprint("orcid", __name__, url_prefix="/api/v1/orcid")

@orcid_bp.route('/get-orcid/<path:orcid_id>', methods=['GET'])
# @jwt_required()
def get_researcher_profile(orcid_id):
    """
    Fetches a researcher's profile information from the ORCID API.

    ---
    tags:
      - ORCID
    parameters:
      - in: path
        name: orcid_id
        type: string
        required: true
        description: The ORCID iD of the researcher to retrieve profile for.
    responses:
      200:
        description: Successful retrieval of researcher profile
        content:
          application/json:
            schema:
              # Replace with actual schema based on ORCID API response structure
              type: object
              # ... (properties, additional schema details)
      400:
        description: Invalid ORCID iD format
      404:
        description: Researcher with specified ORCID iD not found
      4XX:
        description: Other potential ORCID API errors
      5XX:
        description: Internal server error
    """

    # Extract ORCID ID from full URL if provided
    if orcid_id.startswith('https://orcid.org/'):
        orcid_id = orcid_id.replace('https://orcid.org/', '')
    elif orcid_id.startswith('http://orcid.org/'):
        orcid_id = orcid_id.replace('http://orcid.org/', '')

    url = f"{ORCID_API_URL}{orcid_id}/person"
    # print(f"url={url}")

    headers = {
        "Accept": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for non-200 status codes
    except requests.exceptions.RequestException as e:
        # Handle potential request exceptions (e.g., network issues)
        return jsonify({'error': f"Error fetching ORCID data ({e})"}), 500
    except requests.exceptions.HTTPError as e:
        # Handle specific ORCID API errors (based on status code)
        if e.response.status_code == 400:
            return jsonify({'error': "Invalid ORCID ID format"}), 400
        elif e.response.status_code == 404:
            return jsonify({'error': "Researcher with specified ORCID ID not found"}), 404
        else:
            return jsonify({'error': f"ORCID API error ({e.response.status_code})"}), e.response.status_code

    return jsonify(response.json())
  
@orcid_bp.route('/search-orcid', methods=['GET'])
  
def search_orcid():
    """
    Searches for researchers by first name, last name, other names, and affiliations using the ORCID API.

    ---
    tags:
      - ORCID
    parameters:
      - in: query
        name: first_name
        type: string
        required: False
        description: The first name of the researcher to search for.
      - in: query
        name: last_name
        type: string
        required: False
        description: The last name of the researcher to search for.
      - in: query
        name: other_names
        type: string
        required: False
        description: A comma-separated list of other names (e.g., middle names, nicknames) of the researcher.
      - in: query
        name: affiliations
        type: string
        required: False
        description: A comma-separated list of affiliations (e.g., institutions, organizations) of the researcher.
    responses:
      200:
        description: Successful retrieval of researcher search results
        content:
          application/json:
            schema:
              # Replace with actual schema based on ORCID API response structure
              type: object
              # ... (properties, additional schema details)
      400:
        description: Bad request (e.g., missing required parameters)
      4XX:
        description: Other potential ORCID API errors (e.g., invalid query format)
      5XX:
        description: Internal server error
    """

    # Get parameters from the request
    first_name = request.args.get('first_name')
    last_name = request.args.get('last_name')
    other_names = request.args.get('other_names')
    affiliations = request.args.get('affiliations')

    # Construct the ORCID API search URL
    base_url = "https://pub.orcid.org/v3.0/expanded-search"
    query_parts = []
    if first_name:
        query_parts.append(f"given-names:{first_name}")
    if last_name:
        query_parts.append(f"family-name:{last_name}")
    if other_names:
        query_parts.append(f"given-names:{other_names}")
    if affiliations:
        query_parts.append(f"affiliation-org-name:{affiliations}")
    query = " AND ".join(query_parts)

    headers = {
        'Accept': 'application/json'
    }

    # Send the GET request to ORCID API
    response = requests.get(f"{base_url}?q={query}", headers=headers)

    # Return the response from ORCID API
    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Failed to retrieve data from ORCID"}), response.status_code