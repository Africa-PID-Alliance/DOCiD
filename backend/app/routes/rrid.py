"""
RRID (Research Resource Identifier) API Endpoints
Search and resolve RRID resources via the SciCrunch service layer.
"""

import logging

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.models import DocidRrid
from app.service_scicrunch import search_rrid_resources, resolve_rrid

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
