"""
DSpace Legacy (6.x) API Routes

API endpoints for integrating with DSpace 6.x and earlier versions.
These endpoints use the older DSpace REST API structure.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, DSpaceMapping, ResourceTypes, UserAccount
from app.service_dspace_legacy import DSpaceLegacyClient, DSpaceLegacyMetadataMapper
from datetime import datetime
import os

dspace_legacy_bp = Blueprint('dspace_legacy', __name__, url_prefix='/api/v1/dspace-legacy')

# Configuration from environment
DSPACE_LEGACY_URL = os.environ.get('DSPACE_LEGACY_URL', 'http://localhost:8080')
DSPACE_LEGACY_EMAIL = os.environ.get('DSPACE_LEGACY_EMAIL', '')
DSPACE_LEGACY_PASSWORD = os.environ.get('DSPACE_LEGACY_PASSWORD', '')


def get_dspace_legacy_client():
    """Get configured DSpace Legacy client"""
    return DSpaceLegacyClient(
        base_url=DSPACE_LEGACY_URL,
        email=DSPACE_LEGACY_EMAIL,
        password=DSPACE_LEGACY_PASSWORD
    )


@dspace_legacy_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """
    Get DSpace Legacy configuration and connection status

    Returns current DSpace Legacy server configuration and tests connection.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    responses:
      200:
        description: Configuration retrieved successfully
        schema:
          type: object
          properties:
            dspace_url:
              type: string
              example: http://dspace.example.org
            version:
              type: string
              example: "6.x"
            is_configured:
              type: boolean
            connection_status:
              type: string
              example: connected
    """
    client = get_dspace_legacy_client()

    # Test connection
    is_connected = client.test_connection()

    return jsonify({
        'dspace_url': DSPACE_LEGACY_URL,
        'version': '6.x',
        'is_configured': bool(DSPACE_LEGACY_URL),
        'connection_status': 'connected' if is_connected else 'disconnected'
    }), 200


@dspace_legacy_bp.route('/test-auth', methods=['GET'])
@jwt_required()
def test_authentication():
    """
    Test DSpace Legacy authentication

    Tests authentication with configured credentials.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    responses:
      200:
        description: Authentication test result
        schema:
          type: object
          properties:
            authenticated:
              type: boolean
            message:
              type: string
    """
    client = get_dspace_legacy_client()
    auth_success = client.authenticate()

    if auth_success:
        client.logout()
        return jsonify({
            'authenticated': True,
            'message': 'Authentication successful'
        }), 200
    else:
        return jsonify({
            'authenticated': False,
            'message': 'Authentication failed'
        }), 200


@dspace_legacy_bp.route('/items', methods=['GET'])
@jwt_required()
def list_items():
    """
    List items from DSpace Legacy repository

    Retrieves items with pagination support.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 20
        description: Number of items per page
      - name: offset
        in: query
        type: integer
        default: 0
        description: Offset for pagination
    responses:
      200:
        description: List of items retrieved successfully
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              name:
                type: string
              handle:
                type: string
              type:
                type: string
      500:
        description: Failed to fetch items
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    client = get_dspace_legacy_client()
    client.authenticate()

    items = client.get_items(limit=limit, offset=offset)
    client.logout()

    if items is None:
        return jsonify({'error': 'Failed to fetch items from DSpace Legacy'}), 500

    return jsonify(items), 200


@dspace_legacy_bp.route('/items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    """
    Get single item by ID

    Retrieves full item details including metadata.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: DSpace item ID (numeric, not UUID)
        example: 12345
    responses:
      200:
        description: Item retrieved successfully
      404:
        description: Item not found
    """
    client = get_dspace_legacy_client()
    client.authenticate()

    item = client.get_item(item_id)
    client.logout()

    if item is None:
        return jsonify({'error': f'Item {item_id} not found'}), 404

    return jsonify(item), 200


@dspace_legacy_bp.route('/handle/<path:handle>', methods=['GET'])
@jwt_required()
def get_by_handle(handle):
    """
    Get item by handle

    Finds and retrieves item using its handle.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: handle
        in: path
        type: string
        required: true
        description: Item handle (e.g., 123456789/1)
        example: "123456789/1"
    responses:
      200:
        description: Item retrieved successfully
      404:
        description: Item not found
    """
    client = get_dspace_legacy_client()
    client.authenticate()

    item = client.find_item_by_handle(handle)
    client.logout()

    if item is None:
        return jsonify({'error': f'Item with handle {handle} not found'}), 404

    return jsonify(item), 200


@dspace_legacy_bp.route('/preview/item/<int:item_id>', methods=['GET'])
@jwt_required()
def preview_item(item_id):
    """
    Preview item metadata mapping

    Shows how DSpace Legacy metadata will be mapped to DOCiD format without importing.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: DSpace item ID to preview
        example: 12345
    responses:
      200:
        description: Preview generated successfully
        schema:
          type: object
          properties:
            dspace_item_id:
              type: integer
            dspace_handle:
              type: string
            mapped_data:
              type: object
      404:
        description: Item not found
    """
    current_user_id = get_jwt_identity()

    client = get_dspace_legacy_client()
    client.authenticate()

    # Get item
    dspace_item = client.get_item(item_id)
    client.logout()

    if not dspace_item:
        return jsonify({'error': f'Item {item_id} not found in DSpace Legacy'}), 404

    # Map metadata
    mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(dspace_item, current_user_id)

    return jsonify({
        'dspace_item_id': item_id,
        'dspace_handle': dspace_item.get('handle'),
        'raw_metadata': dspace_item.get('metadata'),
        'mapped_data': mapped_data
    }), 200


@dspace_legacy_bp.route('/sync/item/<int:item_id>', methods=['POST'])
@jwt_required()
def sync_single_item(item_id):
    """
    Sync single DSpace Legacy item to DOCiD

    Imports a DSpace Legacy item and creates corresponding publication in DOCiD.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: item_id
        in: path
        type: integer
        required: true
        description: DSpace item ID to sync
        example: 12345
    responses:
      201:
        description: Item synced successfully
        schema:
          type: object
          properties:
            message:
              type: string
            publication_id:
              type: integer
            dspace_item_id:
              type: integer
            docid:
              type: string
      400:
        description: Item already synced or validation error
      404:
        description: Item not found
      500:
        description: Sync failed
    """
    current_user_id = get_jwt_identity()

    # Check if already synced
    existing = DSpaceMapping.query.filter_by(
        dspace_handle=f"legacy-item-{item_id}"
    ).first()

    if existing:
        return jsonify({
            'error': 'Item already synced',
            'publication_id': existing.publication_id
        }), 400

    # Get DSpace item
    client = get_dspace_legacy_client()
    client.authenticate()
    dspace_item = client.get_item(item_id)

    if not dspace_item:
        client.logout()
        return jsonify({'error': f'Item {item_id} not found in DSpace Legacy'}), 404

    # Map metadata
    mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(dspace_item, current_user_id)
    metadata_hash = client.calculate_metadata_hash(dspace_item.get('metadata', []))
    client.logout()

    try:
        # Get resource type
        resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
        resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
        resource_type_id = resource_type.id if resource_type else 1

        # Generate DOCiD
        handle = dspace_item.get('handle', f'legacy/{item_id}')
        document_docid = f"20.500.DSPACE-LEGACY/{item_id}"

        # Create publication
        publication = Publications(
            user_id=current_user_id,
            document_title=mapped_data['publication']['document_title'],
            document_description=mapped_data['publication'].get('document_description', ''),
            resource_type_id=resource_type_id,
            doi='',
            document_docid=document_docid,
            owner='DSpace Legacy Repository',
        )

        db.session.add(publication)
        db.session.flush()

        # Create mapping
        mapping = DSpaceMapping(
            dspace_handle=handle,
            dspace_uuid=f"legacy-item-{item_id}",  # Legacy uses IDs not UUIDs
            dspace_url=DSPACE_LEGACY_URL,
            publication_id=publication.id,
            sync_status='synced',
            dspace_metadata_hash=metadata_hash
        )

        db.session.add(mapping)
        db.session.commit()

        return jsonify({
            'message': 'Item synced successfully',
            'publication_id': publication.id,
            'dspace_item_id': item_id,
            'docid': document_docid
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Sync failed: {str(e)}'}), 500


@dspace_legacy_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
def batch_sync():
    """
    Batch sync multiple items from DSpace Legacy

    Syncs multiple items in one operation with pagination.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            limit:
              type: integer
              default: 10
              description: Number of items to sync
            offset:
              type: integer
              default: 0
              description: Offset for pagination
            skip_existing:
              type: boolean
              default: true
              description: Skip items already synced
    responses:
      200:
        description: Batch sync completed
        schema:
          type: object
          properties:
            message:
              type: string
            total_items:
              type: integer
            synced:
              type: integer
            already_existed:
              type: integer
            errors:
              type: integer
    """
    current_user_id = get_jwt_identity()
    data = request.get_json()

    limit = data.get('limit', 10)
    offset = data.get('offset', 0)
    skip_existing = data.get('skip_existing', True)

    # Get items
    client = get_dspace_legacy_client()
    client.authenticate()
    items = client.get_items(limit=limit, offset=offset)

    if not items:
        client.logout()
        return jsonify({'error': 'Failed to fetch items'}), 500

    results = {
        'total_items': len(items),
        'synced': 0,
        'already_existed': 0,
        'errors': 0,
        'details': []
    }

    for item_summary in items:
        item_id = item_summary.get('id')
        handle = item_summary.get('handle', f'legacy/{item_id}')

        # Check if already synced
        if skip_existing:
            existing = DSpaceMapping.query.filter_by(dspace_handle=handle).first()
            if existing:
                results['already_existed'] += 1
                results['details'].append({
                    'item_id': item_id,
                    'handle': handle,
                    'status': 'already_existed'
                })
                continue

        try:
            # Get full item
            full_item = client.get_item(item_id)
            if not full_item:
                results['errors'] += 1
                continue

            # Map metadata
            mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(full_item, current_user_id)
            metadata_hash = client.calculate_metadata_hash(full_item.get('metadata', []))

            # Get resource type
            resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
            resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
            resource_type_id = resource_type.id if resource_type else 1

            # Create publication
            document_docid = f"20.500.DSPACE-LEGACY/{item_id}"
            publication = Publications(
                user_id=current_user_id,
                document_title=mapped_data['publication']['document_title'],
                document_description=mapped_data['publication'].get('document_description', ''),
                resource_type_id=resource_type_id,
                doi='',
                document_docid=document_docid,
                owner='DSpace Legacy Repository',
            )

            db.session.add(publication)
            db.session.flush()

            # Create mapping
            mapping = DSpaceMapping(
                dspace_handle=handle,
                dspace_uuid=f"legacy-item-{item_id}",
                dspace_url=DSPACE_LEGACY_URL,
                publication_id=publication.id,
                sync_status='synced',
                dspace_metadata_hash=metadata_hash
            )

            db.session.add(mapping)
            db.session.commit()

            results['synced'] += 1
            results['details'].append({
                'item_id': item_id,
                'handle': handle,
                'status': 'synced',
                'publication_id': publication.id
            })

        except Exception as e:
            db.session.rollback()
            results['errors'] += 1
            results['details'].append({
                'item_id': item_id,
                'handle': handle,
                'status': 'error',
                'error': str(e)
            })

    client.logout()

    return jsonify({
        'message': 'Batch sync completed',
        **results
    }), 200


@dspace_legacy_bp.route('/collections', methods=['GET'])
@jwt_required()
def list_collections():
    """
    List collections from DSpace Legacy

    Retrieves all collections from the repository.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: limit
        in: query
        type: integer
        default: 100
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Collections retrieved successfully
    """
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)

    client = get_dspace_legacy_client()
    client.authenticate()

    collections = client.get_collections(limit=limit, offset=offset)
    client.logout()

    if collections is None:
        return jsonify({'error': 'Failed to fetch collections'}), 500

    return jsonify(collections), 200


@dspace_legacy_bp.route('/collections/<int:collection_id>/items', methods=['GET'])
@jwt_required()
def get_collection_items(collection_id):
    """
    Get items from a specific collection

    Retrieves all items belonging to a collection.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: collection_id
        in: path
        type: integer
        required: true
      - name: limit
        in: query
        type: integer
        default: 20
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Collection items retrieved successfully
    """
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    client = get_dspace_legacy_client()
    client.authenticate()

    items = client.get_collection_items(collection_id, limit=limit, offset=offset)
    client.logout()

    if items is None:
        return jsonify({'error': 'Failed to fetch collection items'}), 500

    return jsonify(items), 200


@dspace_legacy_bp.route('/search', methods=['GET'])
@jwt_required()
def search_items():
    """
    Search for items in DSpace Legacy

    Performs text search across item metadata.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    parameters:
      - name: query
        in: query
        type: string
        required: true
        description: Search query
      - name: limit
        in: query
        type: integer
        default: 20
      - name: offset
        in: query
        type: integer
        default: 0
    responses:
      200:
        description: Search completed successfully
      400:
        description: Missing query parameter
    """
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Query parameter required'}), 400

    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)

    client = get_dspace_legacy_client()
    client.authenticate()

    items = client.search_items(query, limit=limit, offset=offset)
    client.logout()

    if items is None:
        return jsonify({'error': 'Search failed'}), 500

    return jsonify({'items': items, 'query': query}), 200


@dspace_legacy_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Get DSpace Legacy integration statistics

    Returns sync statistics and status information.
    ---
    tags:
      - DSpace Legacy Integration
    security:
      - Bearer: []
    responses:
      200:
        description: Statistics retrieved successfully
    """
    # Count synced items from Legacy
    total_synced = DSpaceMapping.query.filter(
        DSpaceMapping.dspace_url == DSPACE_LEGACY_URL
    ).count()

    # Get last sync time
    last_mapping = DSpaceMapping.query.filter(
        DSpaceMapping.dspace_url == DSPACE_LEGACY_URL
    ).order_by(DSpaceMapping.last_synced.desc()).first()

    last_sync = last_mapping.last_synced.isoformat() if last_mapping else None

    return jsonify({
        'total_synced': total_synced,
        'last_sync': last_sync,
        'dspace_url': DSPACE_LEGACY_URL,
        'version': '6.x'
    }), 200
