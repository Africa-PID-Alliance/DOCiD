# app/routes/ror.py
from flask import Blueprint, jsonify, request
import requests
import json
from app import db
from app.models import DocIdLookup
from app.service_crossref import get_crossref_doi
from sqlalchemy.sql import func
from habanero import Crossref
import urllib.parse
from urllib.parse import urlencode
# Replace with your desired ROR API base URL
ROR_API_URL = "https://api.ror.org/"

ror_bp = Blueprint("ror", __name__, url_prefix="/api/v1/ror")

@ror_bp.route('/get-ror-by-id/<path:ror_id>', methods=['GET'])
def get_ror_by_id(ror_id):
    """
    Fetches details of a research organization by ROR ID.
    Accepts either just the ROR ID (e.g., "02qv1aw94") or the full ROR URL (e.g., "https://ror.org/02qv1aw94").

    ---
    tags:
      - ROR
    parameters:
      - in: path
        name: ror_id
        type: string
        required: true
        description: The ROR ID or full ROR URL of the organization to retrieve details for.
    responses:
      200:
        description: Successful retrieval of ROR data
        content:
          application/json:
            schema:
              # Replace with actual schema details based on ROR API response structure
              type: object
              # ... (properties, additional schema details)
      404:
        description: Organization with specified ROR ID not found
        content:
          application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    description: Error message indicating organization not found
      5XX:
        description: Internal server error
        content:
          application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    description: Generic error message for server-side issues
    """
    
    # Extract the ROR ID from the full URL if a full URL is provided
    if ror_id.startswith('https://ror.org/'):
        # Extract just the ID part from the full URL
        extracted_id = ror_id.replace('https://ror.org/', '')
        print(f"Extracted ROR ID '{extracted_id}' from full URL '{ror_id}'")
        ror_id = extracted_id
    elif ror_id.startswith('http://ror.org/'):
        # Handle http version too
        extracted_id = ror_id.replace('http://ror.org/', '')
        print(f"Extracted ROR ID '{extracted_id}' from full URL '{ror_id}'")
        ror_id = extracted_id
    
    print(f"Making ROR API request for ID: {ror_id}")
    url = f"{ROR_API_URL}organizations/{ror_id}"
    response = requests.get(url)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({'error': f"Failed to retrieve ROR data (status code: {response.status_code})"}), response.status_code
 
@ror_bp.route('/search-organizations', methods=['GET'])
def search_organizations():
    """
    Fetches details of research organizations based on query parameters.

    ---
    tags:
      - ROR
    parameters:
      - in: query  # Adjust if parameter is in path (like 'ror_id')
        name: q
        type: string
        required: false  # Optional parameter
        description: Search query for organization names or identifiers.
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number of results (defaults to 1).
    responses:
        '200':
          description: Successful retrieval of ROR search results
          content:
            application/json:
              schema:
                type: object  # Replace with actual schema based on ROR API response structure
                properties:
                  id:  # Assuming 'id' property contains the ROR ID
                    type: string
                    description: The ROR ID of the organization
                  # ... (other properties)
        '4XX':
          description:
            - Invalid query parameter values
            - Other potential search-related errors
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    description: Error message indicating issue with the search request
        '5XX':
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
                    description: Generic error message for server-side issues
    """

    query_params = request.args
    
    param = query_params.get('q')
    page = query_params.get('page')

    # Encode the query parameter for safe inclusion in the URL
    encoded_params = urlencode({
        'query': param,
        'page': page,
    })
    
    url = f"https://api.ror.org/organizations?query={encoded_params}"
    
    response = requests.get(url)
     
    if response.status_code == 200:
        try:
            data = response.json()
            
            # Check if results are found
            if 'errors' in data:
               return data
            else:
            
              # Check if results are found
              if data['number_of_results'] == 0:
                return jsonify({"message": "No organizations found for your query"}), 204
              
              # Extract organization information (modify based on your needs)
              organizations = []
              for org in data.get('items', []):
                
                ror_id = org.get('id')
                id = ror_id.split("/")[-1]
                
                organizations.append({
                  "id": id,
                  "name": org.get('name'),
                  "status": org.get('status'),
                  "wikipedia_url": org.get('wikipedia_url'),
                  "country": org.get('country'),
                  # Add other relevant fields as needed
                })
                
              return jsonify({"organizations": organizations})
 
        except (ValueError, json.JSONDecodeError):
            # Handle potential JSON parsing errors
            return jsonify({'error': "Failed to parse ROR API response"}), 500
    else:
        return jsonify({'error': f"Failed to retrieve ROR data (status code: {response.status_code})"}), response.status_code
      
      
@ror_bp.route('/search-organization', methods=['GET'])
def search_organization():
    """
    Fetches details of research organization based on query parameters.
    Uses ROR's advanced query syntax to properly filter by name and country.

    ---
    tags:
      - ROR
    parameters:
      - in: query
        name: name
        type: string
        required: true
        description: Organization name to search for.
      - in: query
        name: country
        type: string
        required: false
        description: Country name to filter results (must match ROR's controlled vocabulary).
      - in: query
        name: page
        type: integer
        default: 1
        description: Page number of results (defaults to 1).
    responses:
        '200':
          description: Successful retrieval of ROR search results
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                    description: The ROR ID of the organization
        '400':
          description: Missing required parameters
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
        '404':
          description: No results found
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
        '5XX':
          description: Internal server error
          content:
            application/json:
              schema:
                type: object
                properties:
                  error:
                    type: string
    """

    query_params = request.args

    organization_name = query_params.get('name')
    country_name = query_params.get('country')
    page = query_params.get('page', '1')

    if not organization_name:
        return jsonify({'error': 'Organization name parameter (name) is required'}), 400

    # Normalize country name to title case (ROR uses proper case like "Kenya", "South Africa")
    if country_name:
        country_name = country_name.strip().title()

    # Use simple query for fuzzy matching (better for name variations)
    # Then filter results by country in the backend
    params = {
        'query': organization_name,
        'page': page
    }

    encoded_params = urlencode(params)
    url = f"https://api.ror.org/organizations?{encoded_params}"

    print(f"ROR API Request URL: {url}")

    response = requests.get(url)

    if response.status_code == 200:
        try:
            data = response.json()

            # Check if results are found
            if 'errors' in data:
               return data
            else:

              # Filter results by country if provided
              if data and 'items' in data and len(data['items']) > 0:
                  items = data['items']

                  # If country is specified, filter results to match that country
                  if country_name:
                      filtered_items = []
                      for item in items:
                          locations = item.get('locations', [])
                          if locations and locations[0].get('geonames_details'):
                              item_country = locations[0]['geonames_details'].get('country_name')
                              if item_country and item_country.lower() == country_name.lower():
                                  filtered_items.append(item)

                      if not filtered_items:
                          return jsonify({"error": "No results found"}), 404

                      first_result = filtered_items[0]
                  else:
                      first_result = items[0]
                  
                  ror_id = first_result.get('id')
                  id = ror_id.split("/")[-1]
 
                  organization = []
                   
                  # Extract the primary name (ror_display type)
                  name = None
                  names = first_result.get('names', [])
                  for name_obj in names:
                      if 'ror_display' in name_obj.get('types', []):
                          name = name_obj.get('value')
                          break
                  if not name and names:  # Fallback to first name if no ror_display
                      name = names[0].get('value')
                  
                  # Extract country from locations
                  country = None
                  locations = first_result.get('locations', [])
                  if locations and locations[0].get('geonames_details'):
                      country = locations[0]['geonames_details'].get('country_name')
                  
                  # Extract Wikipedia URL from links
                  wikipedia_url = None
                  links = first_result.get('links', [])
                  for link in links:
                      if link.get('type') == 'wikipedia':
                          wikipedia_url = link.get('value')
                          break
                  
                  organization.append({
                      "id": id,
                      "name": name,
                      "status": first_result.get('status'),
                      "wikipedia_url": wikipedia_url,
                      "country": country,
                    })
                    
                  return jsonify(organization)
              else:
                  return jsonify({"error": "No results found"}), 404
 
        except (ValueError, json.JSONDecodeError):
            # Handle potential JSON parsing errors
            return jsonify({'error': "Failed to parse ROR API response"}), 500
    else:
        return jsonify({'error': f"Failed to retrieve ROR data (status code: {response.status_code})"}), response.status_code
      
      