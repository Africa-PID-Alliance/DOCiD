# app/routes/ringgold.py
from flask import Blueprint, jsonify, request
import requests
import json
from urllib.parse import urlencode

# Ringgold Identifier API
# Purpose: Identifies organizations for institutional affiliations (academic institutions,
#          research centers, hospitals, corporations)
# Format: Numeric identifier (e.g., Ringgold ID: 60025310)
# Use cases: Manuscript submission systems, research analytics, publisher workflows,
#            library consortium management, institutional affiliation tracking
# Note: Shares API infrastructure with ISNI but serves different purpose (institutions vs. creative contributors)
RINGGOLD_API_URL = "https://isni.ringgold.com/api/stable"

ringgold_bp = Blueprint("ringgold", __name__, url_prefix="/api/v1/ringgold")


@ringgold_bp.route('/get-by-isni/<path:isni_id>', methods=['GET'])
def get_by_isni_id(isni_id):
    """
    Fetches institutional affiliation details by ISNI ID from the Ringgold database.
    Ringgold identifies organizations for institutional affiliations (universities,
    research centers, hospitals, corporations).

    Note: Ringgold shares API infrastructure with ISNI but serves different purposes:
    - Ringgold: Institutional identification and affiliation tracking
    - ISNI: Creative contributor identification (authors, researchers, artists)

    ---
    tags:
      - Ringgold
    parameters:
      - in: path
        name: isni_id
        type: string
        required: true
        description: The ISNI ID of the institution to retrieve Ringgold details for.
    responses:
      200:
        description: Successful retrieval of institutional affiliation data
        content:
          application/json:
            schema:
              type: object
              properties:
                isni:
                  type: string
                  description: The ISNI identifier
                ringgold_id:
                  type: integer
                  description: Numeric Ringgold identifier for the institution
                name:
                  type: string
                  description: Institution name
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
        description: Institution with specified ISNI ID not found
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message indicating institution not found
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
            return jsonify({'error': f"Institution with ISNI ID '{clean_isni}' not found"}), 404
        else:
            return jsonify({'error': f"Failed to retrieve institutional data (status code: {response.status_code})"}), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request to Ringgold/ISNI API timed out'}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f'Error connecting to Ringgold/ISNI API: {str(e)}'}), 500


@ringgold_bp.route('/search', methods=['GET'])
def search_organizations():
    """
    Searches for institutions in the Ringgold database for affiliation tracking.
    Ringgold identifies organizations at the institutional level (universities,
    research centers, hospitals, corporations) - used for manuscript submissions,
    research analytics, and institutional affiliation management.

    ---
    tags:
      - Ringgold
    parameters:
      - in: query
        name: q
        type: string
        required: true
        description: Search query for institution names (universities, research centers, etc.).
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
        description: Successful retrieval of Ringgold institutional search results
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
                  description: Array of matching institutions
                  items:
                    type: object
                    properties:
                      ringgold_id:
                        type: integer
                        description: Numeric Ringgold identifier
                      name:
                        type: string
                        description: Institution name
                      locality:
                        type: string
                      admin_area_level_1:
                        type: string
                      country_code:
                        type: string
                      ISNI:
                        type: string
                        description: Associated ISNI identifier
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
                    "message": "No institutions found for your query",
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
    Searches for a single institution and returns the first match.
    Useful for autocomplete, institutional affiliation lookups, or quick institution identification.
    Targets organizations at the institutional level (universities, research centers, hospitals, corporations).

    ---
    tags:
      - Ringgold
    parameters:
      - in: query
        name: name
        type: string
        required: true
        description: Institution name to search for (e.g., "Harvard University", "Mayo Clinic").
      - in: query
        name: country
        type: string
        required: false
        description: Country code to filter results (ISO 2-letter code, e.g., "US", "GB", "KE").
    responses:
      200:
        description: Successful retrieval of institution
        content:
          application/json:
            schema:
              type: object
              properties:
                ringgold_id:
                  type: integer
                  description: Numeric Ringgold identifier for institutional affiliation
                name:
                  type: string
                  description: Institution name
                locality:
                  type: string
                admin_area_level_1:
                  type: string
                country_code:
                  type: string
                ISNI:
                  type: string
                  description: Associated ISNI identifier
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

    institution_name = request.args.get('name')
    country_code = request.args.get('country')

    if not institution_name:
        return jsonify({'error': 'Institution name parameter (name) is required'}), 400

    # Normalize country code to uppercase
    if country_code:
        country_code = country_code.strip().upper()

    params = {
        'q': institution_name,
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
                    return jsonify({"error": f"No institutions found in country '{country_code}'"}), 404

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
