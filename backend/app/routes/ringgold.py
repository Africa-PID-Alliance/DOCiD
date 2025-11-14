# app/routes/ringgold.py
from flask import Blueprint, jsonify, request
import requests
import json
from urllib.parse import urlencode

# Ringgold API base URL (same infrastructure as ISNI)
RINGGOLD_API_URL = "https://isni.ringgold.com/api/stable"

ringgold_bp = Blueprint("ringgold", __name__, url_prefix="/api/v1/ringgold")


@ringgold_bp.route('/get-by-isni/<path:isni_id>', methods=['GET'])
def get_by_isni_id(isni_id):
    """
    Fetches details of an organization by ISNI ID from the Ringgold database.

    Note: Ringgold and ISNI have merged their databases. This endpoint fetches
    organization data using the ISNI identifier.

    ---
    tags:
      - Ringgold
    parameters:
      - in: path
        name: isni_id
        type: string
        required: true
        description: The ISNI ID of the organization to retrieve details for.
    responses:
      200:
        description: Successful retrieval of organization data
        content:
          application/json:
            schema:
              type: object
              properties:
                isni:
                  type: string
                  description: The ISNI identifier
                name:
                  type: string
                  description: Organization name
                locality:
                  type: string
                  description: City or locality
                admin_area_level_1_short:
                  type: string
                  description: State/province/region (short form)
                country_code:
                  type: string
                  description: ISO country code
      404:
        description: Organization with specified ISNI ID not found
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

    # Clean the ISNI ID (remove spaces and special characters)
    clean_isni = ''.join(filter(str.isdigit, isni_id))

    print(f"Making Ringgold API request for ISNI ID: {clean_isni}")
    url = f"{RINGGOLD_API_URL}/institution/{clean_isni}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            return jsonify(data)
        elif response.status_code == 404:
            return jsonify({'error': f"Organization with ISNI ID '{clean_isni}' not found"}), 404
        else:
            return jsonify({'error': f"Failed to retrieve organization data (status code: {response.status_code})"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request to Ringgold/ISNI API timed out'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error connecting to Ringgold/ISNI API: {str(e)}'}), 500


@ringgold_bp.route('/search', methods=['GET'])
def search_organizations():
    """
    Searches for organizations in the Ringgold database based on query parameters.

    ---
    tags:
      - Ringgold
    parameters:
      - in: query
        name: q
        type: string
        required: true
        description: Search query for organization names.
      - in: query
        name: offset
        type: integer
        default: 0
        description: Offset for pagination (defaults to 0).
      - in: query
        name: limit
        type: integer
        default: 10
        description: Maximum number of results to return (defaults to 10, max 100).
    responses:
      200:
        description: Successful retrieval of Ringgold search results
        content:
          application/json:
            schema:
              type: object
              properties:
                search_total_count:
                  type: integer
                  description: Total number of results found
                offset:
                  type: integer
                  description: Current offset
                limit:
                  type: integer
                  description: Current limit
                institutions:
                  type: array
                  description: Array of matching organizations
                  items:
                    type: object
                    properties:
                      ringgold_id:
                        type: integer
                      name:
                        type: string
                      locality:
                        type: string
                      admin_area_level_1:
                        type: string
                      country_code:
                        type: string
                      ISNI:
                        type: string
      400:
        description: Missing or invalid query parameter
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
      5XX:
        description: Internal server error
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
    """

    query = request.args.get('q')
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({'error': 'Search query parameter (q) is required'}), 400

    # Limit max results to 100
    if limit > 100:
        limit = 100

    params = {
        'q': query,
        'offset': offset,
        'limit': limit
    }

    encoded_params = urlencode(params)
    url = f"{RINGGOLD_API_URL}/search?{encoded_params}"

    print(f"Ringgold API Request URL: {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Check if results are found
            if data.get('total', 0) == 0:
                return jsonify({
                    "message": "No organizations found for your query",
                    "total": 0,
                    "institutions": []
                }), 200

            return jsonify(data)

        else:
            return jsonify({'error': f"Failed to retrieve Ringgold data (status code: {response.status_code})"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request to Ringgold API timed out'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error connecting to Ringgold API: {str(e)}'}), 500
    except (ValueError, json.JSONDecodeError):
        return jsonify({'error': "Failed to parse Ringgold API response"}), 500


@ringgold_bp.route('/search-organization', methods=['GET'])
def search_organization():
    """
    Searches for a single organization and returns the first match.
    Useful for autocomplete or quick lookups.

    ---
    tags:
      - Ringgold
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
        description: Country code to filter results (ISO 2-letter code, e.g., "US", "GB", "KE").
    responses:
      200:
        description: Successful retrieval of organization
        content:
          application/json:
            schema:
              type: object
              properties:
                ringgold_id:
                  type: integer
                name:
                  type: string
                locality:
                  type: string
                admin_area_level_1:
                  type: string
                country_code:
                  type: string
                ISNI:
                  type: string
      400:
        description: Missing required parameters
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
      404:
        description: No results found
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
      5XX:
        description: Internal server error
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
    """

    organization_name = request.args.get('name')
    country_code = request.args.get('country')

    if not organization_name:
        return jsonify({'error': 'Organization name parameter (name) is required'}), 400

    # Normalize country code to uppercase
    if country_code:
        country_code = country_code.strip().upper()

    params = {
        'q': organization_name,
        'offset': 0,
        'limit': 20  # Get more results to filter by country
    }

    encoded_params = urlencode(params)
    url = f"{RINGGOLD_API_URL}/search?{encoded_params}"

    print(f"Ringgold API Request URL: {url}")

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            institutions = data.get('institutions', [])

            if not institutions:
                return jsonify({"error": "No results found"}), 404

            # Filter by country if provided
            if country_code:
                filtered_institutions = [
                    inst for inst in institutions
                    if inst.get('country_code', '').upper() == country_code
                ]

                if not filtered_institutions:
                    return jsonify({"error": f"No organizations found in country '{country_code}'"}), 404

                first_result = filtered_institutions[0]
            else:
                first_result = institutions[0]

            return jsonify(first_result)

        else:
            return jsonify({'error': f"Failed to retrieve Ringgold data (status code: {response.status_code})"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request to Ringgold API timed out'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error connecting to Ringgold API: {str(e)}'}), 500
    except (ValueError, json.JSONDecodeError):
        return jsonify({'error': "Failed to parse Ringgold API response"}), 500
