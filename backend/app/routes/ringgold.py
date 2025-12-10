# app/routes/ringgold.py
from flask import Blueprint, jsonify, request
import requests
import json
from urllib.parse import urlencode
from app.models import RinggoldInstitution

# Ringgold Identifier API
# Purpose: Identifies organizations for institutional affiliations (academic institutions,
#          research centers, hospitals, corporations)
# Format: Numeric identifier (e.g., Ringgold ID: 60025310)
# Use cases: Manuscript submission systems, research analytics, publisher workflows,
#            library consortium management, institutional affiliation tracking
# Note: Shares API infrastructure with ISNI but serves different purpose (institutions vs. creative contributors)
#
# HYBRID APPROACH:
# 1. First search local database (17,329 African institutions from Ringgold data export)
# 2. If local search fails or returns no results, fall back to Ringgold API
RINGGOLD_API_URL = "https://isni.ringgold.com/api/stable"

ringgold_bp = Blueprint("ringgold", __name__, url_prefix="/api/v1/ringgold")


def search_ringgold_api(query, offset=0, limit=10):
    """
    Helper function to search the Ringgold API.
    Returns (data, error, status_code) tuple.
    """
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
            return response.json(), None, 200
        else:
            return None, f"Failed to retrieve Ringgold data (status code: {response.status_code})", response.status_code

    except requests.exceptions.Timeout:
        return None, 'Request to Ringgold API timed out', 504
    except requests.exceptions.RequestException as e:
        return None, f'Error connecting to Ringgold API: {str(e)}', 500
    except (ValueError, json.JSONDecodeError):
        return None, "Failed to parse Ringgold API response", 500


@ringgold_bp.route('/get-by-isni/<path:isni_id>', methods=['GET'])
def get_by_isni_id(isni_id):
    """
    Fetches institutional affiliation details by ISNI ID.
    First checks local database, then falls back to Ringgold API.

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
                source:
                  type: string
                  description: Data source (local or api)
      404:
        description: Institution with specified ISNI ID not found
      5XX:
        description: Internal server error
    """
    # Clean the ISNI ID (remove spaces and special characters)
    clean_isni = ''.join(filter(str.isdigit, isni_id))

    # 1. Try local database first
    try:
        local_institution = RinggoldInstitution.get_by_isni(clean_isni)
        if local_institution:
            print(f"Found institution in local database for ISNI: {clean_isni}")
            result = local_institution.to_dict()
            result['source'] = 'local'
            return jsonify(result)
    except Exception as e:
        print(f"Local database lookup failed: {e}")

    # 2. Fall back to Ringgold API
    print(f"Making Ringgold API request for ISNI ID: {clean_isni}")
    url = f"{RINGGOLD_API_URL}/institution/{clean_isni}"

    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            data['source'] = 'api'
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
    Uses hybrid approach: local database first, then Ringgold API fallback.

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
        name: country
        type: string
        required: false
        description: Country name or ISO 2-letter code to filter results.
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
      - in: query
        name: source
        type: string
        required: false
        description: Force data source ('local' or 'api'). Default is hybrid (local first).
    responses:
      200:
        description: Successful retrieval of Ringgold institutional search results
        content:
          application/json:
            schema:
              type: object
              properties:
                total:
                  type: integer
                  description: Total number of results found
                offset:
                  type: integer
                  description: Current offset
                limit:
                  type: integer
                  description: Current limit
                source:
                  type: string
                  description: Data source used (local or api)
                institutions:
                  type: array
                  description: Array of matching institutions
      400:
        description: Missing or invalid query parameter
      5XX:
        description: Internal server error
    """
    query = request.args.get('q')
    country = request.args.get('country')
    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 10, type=int)
    force_source = request.args.get('source', '').lower()

    if not query:
        return jsonify({'error': 'Search query parameter (q) is required'}), 400

    # Limit max results to 100
    if limit > 100:
        limit = 100

    # 1. Try local database first (unless API is forced)
    if force_source != 'api':
        try:
            institutions, total = RinggoldInstitution.search(
                query=query,
                country=country,
                limit=limit,
                offset=offset
            )

            if institutions:
                print(f"Found {total} institutions in local database for query: {query}")
                return jsonify({
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                    "source": "local",
                    "institutions": [inst.to_dict() for inst in institutions]
                })
            elif force_source == 'local':
                # Local source was forced but no results found
                return jsonify({
                    "message": "No institutions found in local database",
                    "total": 0,
                    "source": "local",
                    "institutions": []
                }), 200

        except Exception as e:
            print(f"Local database search failed: {e}")
            if force_source == 'local':
                return jsonify({'error': f'Local database search failed: {str(e)}'}), 500

    # 2. Fall back to Ringgold API
    print(f"Falling back to Ringgold API for query: {query}")
    data, error, status_code = search_ringgold_api(query, offset, limit)

    if error:
        return jsonify({'error': error}), status_code

    # Check if results are found
    if data.get('total', 0) == 0:
        return jsonify({
            "message": "No institutions found for your query",
            "total": 0,
            "source": "api",
            "institutions": []
        }), 200

    # Filter by country if provided (API doesn't support country filter)
    if country and data.get('institutions'):
        country_upper = country.strip().upper()
        if len(country_upper) == 2:
            # Filter by country code
            data['institutions'] = [
                inst for inst in data['institutions']
                if inst.get('country_code', '').upper() == country_upper
            ]
        else:
            # Filter by country name (partial match)
            country_lower = country.strip().lower()
            data['institutions'] = [
                inst for inst in data['institutions']
                if country_lower in inst.get('country', '').lower()
            ]
        data['total'] = len(data['institutions'])

    data['source'] = 'api'
    return jsonify(data)


@ringgold_bp.route('/search-organization', methods=['GET'])
def search_organization():
    """
    Searches for a single institution and returns the first match.
    Uses hybrid approach: local database first, then Ringgold API fallback.

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
        description: Country name or ISO 2-letter code to filter results.
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
                source:
                  type: string
                  description: Data source (local or api)
      400:
        description: Missing required parameters
      404:
        description: No results found
      5XX:
        description: Internal server error
    """
    institution_name = request.args.get('name')
    country = request.args.get('country')

    if not institution_name:
        return jsonify({'error': 'Institution name parameter (name) is required'}), 400

    # 1. Try local database first
    try:
        institutions, total = RinggoldInstitution.search(
            query=institution_name,
            country=country,
            limit=1,
            offset=0
        )

        if institutions:
            print(f"Found institution in local database: {institutions[0].name}")
            result = institutions[0].to_dict()
            result['source'] = 'local'
            return jsonify(result)

    except Exception as e:
        print(f"Local database search failed: {e}")

    # 2. Fall back to Ringgold API
    print(f"Falling back to Ringgold API for institution: {institution_name}")

    # Normalize country code to uppercase for API filtering
    country_code = None
    if country:
        country_upper = country.strip().upper()
        if len(country_upper) == 2:
            country_code = country_upper

    data, error, status_code = search_ringgold_api(institution_name, offset=0, limit=20)

    if error:
        return jsonify({'error': error}), status_code

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
    elif country:
        # Filter by country name (partial match)
        country_lower = country.strip().lower()
        filtered_institutions = [
            inst for inst in institutions
            if country_lower in inst.get('country', '').lower()
        ]

        if not filtered_institutions:
            return jsonify({"error": f"No institutions found in country '{country}'"}), 404

        first_result = filtered_institutions[0]
    else:
        first_result = institutions[0]

    first_result['source'] = 'api'
    return jsonify(first_result)


@ringgold_bp.route('/stats', methods=['GET'])
def get_local_stats():
    """
    Get statistics about the local Ringgold institutions database.

    ---
    tags:
      - Ringgold
    responses:
      200:
        description: Local database statistics
        content:
          application/json:
            schema:
              type: object
              properties:
                total_institutions:
                  type: integer
                countries:
                  type: array
                  items:
                    type: object
                    properties:
                      country:
                        type: string
                      count:
                        type: integer
    """
    from app import db
    from sqlalchemy import func

    try:
        total = RinggoldInstitution.query.count()

        # Get country breakdown
        country_counts = db.session.query(
            RinggoldInstitution.country,
            func.count(RinggoldInstitution.id).label('count')
        ).group_by(RinggoldInstitution.country).order_by(
            func.count(RinggoldInstitution.id).desc()
        ).all()

        return jsonify({
            "total_institutions": total,
            "countries": [
                {"country": country, "count": count}
                for country, count in country_counts
            ]
        })

    except Exception as e:
        return jsonify({'error': f'Failed to get statistics: {str(e)}'}), 500
