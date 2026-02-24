"""
RRID (Research Resource Identifier) API Endpoints
Search and resolve RRID resources via the SciCrunch service layer.
"""

import logging
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import DocidRrid
from app.service_scicrunch import search_rrid_resources, resolve_rrid, validate_rrid

# Module-level logger
logger = logging.getLogger(__name__)

# Blueprint object
rrid_bp = Blueprint('rrid', __name__, url_prefix='/api/v1/rrid')


@rrid_bp.route('/search', methods=['GET'])
@jwt_required()
def search_resources():
    """
    Search SciCrunch for RRID resources by keyword and optional type filter.
    ---
    tags:
      - RRID
    security:
      - Bearer: []
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Keyword search query
        example: flow cytometry
      - name: type
        in: query
        type: string
        required: false
        description: Resource type filter (core_facility, software, antibody, cell_line). Defaults to core_facility.
        example: software
    responses:
      200:
        description: Search results as a flat JSON array
        schema:
          type: array
          items:
            type: object
            properties:
              scicrunch_id:
                type: string
              name:
                type: string
              description:
                type: string
              url:
                type: string
              types:
                type: array
              rrid:
                type: string
      400:
        description: Missing or invalid parameter
      401:
        description: Unauthorized — JWT token required
      502:
        description: SciCrunch service unavailable
    """
    keyword_query = request.args.get('q', '').strip()
    if not keyword_query:
        return jsonify({'error': 'Missing required parameter: q'}), 400

    resource_type_filter = request.args.get('type')

    search_results, search_error = search_rrid_resources(keyword_query, resource_type_filter)

    if search_error is not None:
        error_message = search_error.get('error', '')
        if error_message.startswith('Invalid resource type'):
            return jsonify({'error': f"Invalid resource type: {resource_type_filter}"}), 400
        return jsonify({'error': 'Search service unavailable'}), 502

    return jsonify(search_results), 200


@rrid_bp.route('/resolve', methods=['GET'])
@jwt_required()
def resolve_rrid_endpoint():
    """
    Resolve an RRID to canonical metadata via the SciCrunch resolver.
    ---
    tags:
      - RRID
    security:
      - Bearer: []
    parameters:
      - name: rrid
        in: query
        type: string
        required: true
        description: RRID to resolve (e.g. RRID:SCR_012345)
        example: RRID:SCR_012345
      - name: entity_type
        in: query
        type: string
        required: false
        description: Entity type for cache context (publication or organization). Must be paired with entity_id.
        example: publication
      - name: entity_id
        in: query
        type: integer
        required: false
        description: Entity primary key for cache context. Must be paired with entity_type.
        example: 42
    responses:
      200:
        description: Flattened canonical metadata including last_resolved_at and stale fields
        schema:
          type: object
          properties:
            name:
              type: string
            rrid:
              type: string
            description:
              type: string
            url:
              type: string
            resource_type:
              type: string
            properCitation:
              type: string
            mentions:
              type: integer
            last_resolved_at:
              type: string
            stale:
              type: boolean
      400:
        description: Missing or invalid parameter
      401:
        description: Unauthorized — JWT token required
      404:
        description: RRID not found
      502:
        description: SciCrunch service unavailable
    """
    rrid_param = request.args.get('rrid', '').strip()
    if not rrid_param:
        return jsonify({'error': 'Missing required parameter: rrid'}), 400

    entity_type = request.args.get('entity_type')
    entity_id_raw = request.args.get('entity_id')

    # Partial entity context check — both or neither
    if bool(entity_type) != bool(entity_id_raw):
        return jsonify({'error': 'Both entity_type and entity_id are required when either is provided'}), 400

    # Entity type allowlist check
    if entity_type and entity_type not in DocidRrid.ALLOWED_ENTITY_TYPES:
        return jsonify({'error': f"Invalid entity_type: {entity_type}"}), 400

    # entity_id type conversion
    entity_id = None
    if entity_id_raw is not None:
        try:
            entity_id = int(entity_id_raw)
        except ValueError:
            return jsonify({'error': 'Invalid entity_id: must be an integer'}), 400

    resolved_result, resolve_error = resolve_rrid(rrid_param, entity_type, entity_id)

    if resolve_error is not None:
        error_message = resolve_error.get('error', '')
        resolve_detail = resolve_error.get('detail', '').lower()

        if error_message == 'Invalid RRID format':
            return jsonify({'error': 'Invalid RRID format'}), 400
        if 'not found' in resolve_detail or 'could not resolve' in resolve_detail:
            return jsonify({'error': f"RRID not found: {rrid_param}"}), 404
        return jsonify({'error': 'Search service unavailable'}), 502

    # Flatten nested service response into a single-level response
    canonical_metadata = resolved_result['resolved']
    flat_response = {
        **canonical_metadata,
        'last_resolved_at': resolved_result.get('last_resolved_at'),
        'stale': resolved_result.get('stale', False),
    }
    return jsonify(flat_response), 200


@rrid_bp.route('/attach', methods=['POST'])
@jwt_required()
def attach_rrid():
    """
    Attach an RRID to a publication or organization entity.
    ---
    tags:
      - RRID
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - rrid
            - entity_type
            - entity_id
          properties:
            rrid:
              type: string
              description: RRID to attach (e.g. RRID:SCR_012345)
              example: RRID:SCR_012345
            entity_type:
              type: string
              description: Entity type (publication or organization)
              example: publication
            entity_id:
              type: integer
              description: Entity primary key
              example: 42
    responses:
      201:
        description: RRID attached successfully — returns serialized DocidRrid row
        schema:
          type: object
          properties:
            id:
              type: integer
            entity_type:
              type: string
            entity_id:
              type: integer
            rrid:
              type: string
            rrid_name:
              type: string
            rrid_description:
              type: string
            rrid_resource_type:
              type: string
            rrid_url:
              type: string
            resolved_json:
              type: object
            last_resolved_at:
              type: string
            created_at:
              type: string
      400:
        description: Missing or invalid parameter
      401:
        description: Unauthorized — JWT token required
      404:
        description: RRID not found in SciCrunch
      409:
        description: RRID already attached to this entity
      502:
        description: SciCrunch service unavailable
    """
    request_body = request.get_json(silent=True) or {}

    rrid_value = request_body.get('rrid', '').strip() if request_body.get('rrid') else ''
    entity_type = request_body.get('entity_type', '').strip() if request_body.get('entity_type') else ''
    entity_id_raw = request_body.get('entity_id')

    # Validate all three fields are present
    if not rrid_value:
        return jsonify({'error': 'Missing required field: rrid'}), 400
    if not entity_type:
        return jsonify({'error': 'Missing required field: entity_type'}), 400
    if entity_id_raw is None:
        return jsonify({'error': 'Missing required field: entity_id'}), 400

    # Validate entity_type against allowed types
    if entity_type not in DocidRrid.ALLOWED_ENTITY_TYPES:
        return jsonify({'error': f"Invalid entity_type: {entity_type}. Must be one of: {', '.join(sorted(DocidRrid.ALLOWED_ENTITY_TYPES))}"}), 400

    # Validate entity_id is numeric
    try:
        entity_id = int(entity_id_raw)
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid entity_id: must be an integer'}), 400

    # Validate RRID format
    normalized_rrid, validation_error = validate_rrid(rrid_value)
    if validation_error is not None:
        return jsonify({'error': 'Invalid RRID format'}), 400

    # Resolve via SciCrunch — fresh resolve without entity context (no cache lookup)
    resolved_result, resolve_error = resolve_rrid(normalized_rrid)

    if resolve_error is not None:
        error_message = resolve_error.get('error', '')
        resolve_detail = resolve_error.get('detail', '').lower()

        if error_message == 'Invalid RRID format':
            return jsonify({'error': 'Invalid RRID format'}), 400
        if 'not found' in resolve_detail or 'could not resolve' in resolve_detail:
            return jsonify({'error': f"RRID not found: {normalized_rrid}"}), 404
        return jsonify({'error': 'RRID resolution service unavailable'}), 502

    # Extract canonical fields from resolved result
    resolved_metadata = resolved_result['resolved']

    new_rrid_record = DocidRrid(
        entity_type=entity_type,
        entity_id=entity_id,
        rrid=normalized_rrid,
        rrid_name=resolved_metadata.get('name'),
        rrid_description=resolved_metadata.get('description'),
        rrid_resource_type=resolved_metadata.get('resource_type'),
        rrid_url=resolved_metadata.get('url'),
        resolved_json=resolved_metadata,
        last_resolved_at=datetime.utcnow(),
    )

    try:
        db.session.add(new_rrid_record)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'error': f"{normalized_rrid} is already attached to this {entity_type}"}), 409

    logger.info(
        "Attached RRID %s to %s:%d (record id=%d)",
        normalized_rrid,
        entity_type,
        entity_id,
        new_rrid_record.id,
    )

    return jsonify(new_rrid_record.serialize()), 201


@rrid_bp.route('/entity', methods=['GET'])
@jwt_required()
def list_entity_rrids():
    """
    List all RRIDs attached to a specific entity.
    ---
    tags:
      - RRID
    security:
      - Bearer: []
    parameters:
      - name: entity_type
        in: query
        type: string
        required: true
        description: Entity type (publication or organization)
        example: publication
      - name: entity_id
        in: query
        type: integer
        required: true
        description: Entity primary key
        example: 42
    responses:
      200:
        description: Flat JSON array of serialized DocidRrid rows (empty array if none attached)
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              entity_type:
                type: string
              entity_id:
                type: integer
              rrid:
                type: string
              rrid_name:
                type: string
              rrid_description:
                type: string
              rrid_resource_type:
                type: string
              rrid_url:
                type: string
              resolved_json:
                type: object
              last_resolved_at:
                type: string
              created_at:
                type: string
      400:
        description: Missing or invalid parameter
      401:
        description: Unauthorized — JWT token required
    """
    entity_type = request.args.get('entity_type', '').strip()
    entity_id_raw = request.args.get('entity_id', '').strip()

    if not entity_type:
        return jsonify({'error': 'Missing required parameter: entity_type'}), 400
    if not entity_id_raw:
        return jsonify({'error': 'Missing required parameter: entity_id'}), 400

    # Validate entity_type against allowed types
    if entity_type not in DocidRrid.ALLOWED_ENTITY_TYPES:
        return jsonify({'error': f"Invalid entity_type: {entity_type}. Must be one of: {', '.join(sorted(DocidRrid.ALLOWED_ENTITY_TYPES))}"}), 400

    # Validate entity_id is numeric
    try:
        entity_id = int(entity_id_raw)
    except ValueError:
        return jsonify({'error': 'Invalid entity_id: must be an integer'}), 400

    rrid_records = DocidRrid.get_rrids_for_entity(entity_type, entity_id)

    return jsonify([record.serialize() for record in rrid_records]), 200


@rrid_bp.route('/<int:rrid_id>', methods=['DELETE'])
@jwt_required()
def detach_rrid(rrid_id):
    """
    Detach (delete) an RRID record by its primary key.
    ---
    tags:
      - RRID
    security:
      - Bearer: []
    parameters:
      - name: rrid_id
        in: path
        type: integer
        required: true
        description: Primary key of the DocidRrid record to delete
        example: 123
    responses:
      200:
        description: RRID detached successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: RRID detached successfully
      401:
        description: Unauthorized — JWT token required
      404:
        description: RRID record not found
    """
    rrid_record = DocidRrid.query.get(rrid_id)

    if rrid_record is None:
        return jsonify({'error': 'RRID record not found'}), 404

    db.session.delete(rrid_record)
    db.session.commit()

    logger.info("Detached RRID record id=%d", rrid_id)

    return jsonify({'message': 'RRID detached successfully'}), 200
