# app/routes/national_id.py
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from app import db
from app.models import NationalIdResearcher
from sqlalchemy import or_
import logging

logger = logging.getLogger(__name__)

national_id_bp = Blueprint("national_id", __name__, url_prefix="/api/v1/national-id")


@national_id_bp.route('/researchers', methods=['POST'])
@jwt_required()
def register_researcher():
    """
    Register a new researcher by National ID / Passport Number.
    If the researcher already exists (same national_id_number + country), returns the existing record.

    ---
    tags:
      - National ID Researchers
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - name
            - national_id_number
            - country
          properties:
            name:
              type: string
              description: Full name of the researcher
            national_id_number:
              type: string
              description: National ID or Passport number
            country:
              type: string
              description: Country that issued the ID
    responses:
      201:
        description: Researcher registered successfully
      200:
        description: Researcher already exists, returning existing record
      400:
        description: Missing required fields
      500:
        description: Internal server error
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'}), 400

    name = (data.get('name') or '').strip()
    national_id_number = (data.get('national_id_number') or '').strip()
    country = (data.get('country') or '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400
    if not national_id_number:
        return jsonify({'error': 'National ID Number is required'}), 400
    if not country:
        return jsonify({'error': 'Country is required'}), 400

    try:
        # Check if researcher already exists (upsert logic)
        existing_researcher = NationalIdResearcher.query.filter_by(
            national_id_number=national_id_number,
            country=country
        ).first()

        if existing_researcher:
            # Update name if it changed
            if existing_researcher.name != name:
                existing_researcher.name = name
                db.session.commit()
            return jsonify(existing_researcher.to_dict()), 200

        new_researcher = NationalIdResearcher(
            name=name,
            national_id_number=national_id_number,
            country=country
        )
        db.session.add(new_researcher)
        db.session.commit()

        logger.info(f"Registered new National ID researcher: {name} ({national_id_number}, {country})")
        return jsonify(new_researcher.to_dict()), 201

    except Exception as exception:
        db.session.rollback()
        logger.error(f"Error registering researcher: {exception}")
        return jsonify({'error': 'Failed to register researcher'}), 500


@national_id_bp.route('/researchers/<int:researcher_id>', methods=['GET'])
def get_researcher_by_id(researcher_id):
    """
    Get a researcher by database ID.

    ---
    tags:
      - National ID Researchers
    parameters:
      - in: path
        name: researcher_id
        type: integer
        required: true
        description: The database ID of the researcher
    responses:
      200:
        description: Researcher found
      404:
        description: Researcher not found
    """
    researcher = NationalIdResearcher.query.get(researcher_id)
    if not researcher:
        return jsonify({'error': 'Researcher not found'}), 404

    return jsonify(researcher.to_dict()), 200


@national_id_bp.route('/researchers/lookup/<path:national_id_number>', methods=['GET'])
def lookup_by_national_id(national_id_number):
    """
    Lookup researchers by National ID / Passport Number.
    Optionally filter by country.

    ---
    tags:
      - National ID Researchers
    parameters:
      - in: path
        name: national_id_number
        type: string
        required: true
        description: The National ID or Passport number to look up
      - in: query
        name: country
        type: string
        required: false
        description: Filter by country
    responses:
      200:
        description: Lookup results
    """
    national_id_number = national_id_number.strip()
    country = request.args.get('country', '').strip()

    query = NationalIdResearcher.query.filter_by(national_id_number=national_id_number)
    if country:
        query = query.filter_by(country=country)

    researchers = query.all()
    return jsonify({
        'results': [researcher.to_dict() for researcher in researchers],
        'total': len(researchers)
    }), 200


@national_id_bp.route('/researchers/search', methods=['GET'])
def search_researchers():
    """
    Search researchers by name, National ID number, or country.

    ---
    tags:
      - National ID Researchers
    parameters:
      - in: query
        name: q
        type: string
        required: false
        description: Search query (matches name or national ID number)
      - in: query
        name: country
        type: string
        required: false
        description: Filter by country
      - in: query
        name: page
        type: integer
        required: false
        description: Page number (default 1)
      - in: query
        name: per_page
        type: integer
        required: false
        description: Results per page (default 20, max 100)
    responses:
      200:
        description: Search results
    """
    search_query = request.args.get('q', '').strip()
    country = request.args.get('country', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    query = NationalIdResearcher.query

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                NationalIdResearcher.name.ilike(search_pattern),
                NationalIdResearcher.national_id_number.ilike(search_pattern)
            )
        )

    if country:
        query = query.filter(NationalIdResearcher.country.ilike(f"%{country}%"))

    query = query.order_by(NationalIdResearcher.name.asc())

    paginated_results = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'results': [researcher.to_dict() for researcher in paginated_results.items],
        'total': paginated_results.total,
        'page': paginated_results.page,
        'per_page': paginated_results.per_page,
        'pages': paginated_results.pages
    }), 200
