"""
DSpace Legacy (6.x) API Routes

API endpoints for integrating with DSpace 6.x and earlier versions.
These endpoints use the older DSpace REST API structure.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, DSpaceMapping, ResourceTypes, PublicationCreators, CreatorsRoles
from app.service_dspace_legacy import DSpaceLegacyClient, DSpaceLegacyMetadataMapper
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

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


def _save_legacy_creators(publication_id, creators_data, author_role_id=None):
    """Save creators for a legacy DSpace publication."""
    if not creators_data:
        return

    if author_role_id is None:
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

    if author_role_id is None:
        return

    for creator_data in creators_data:
        full_name = creator_data.get('creator_name', '')
        name_parts = full_name.split(',', 1) if ',' in full_name else full_name.rsplit(' ', 1)

        if len(name_parts) == 2:
            family_name = name_parts[0].strip()
            given_name = name_parts[1].strip()
        else:
            family_name = full_name.strip()
            given_name = ''

        identifier_value = creator_data.get('orcid_id', '') or ''
        identifier_type_value = 'orcid' if identifier_value else ''

        db.session.add(PublicationCreators(
            publication_id=publication_id,
            family_name=family_name,
            given_name=given_name,
            identifier=identifier_value,
            identifier_type=identifier_type_value,
            role_id=author_role_id
        ))


def _extract_legacy_doi(metadata_list):
    """Extract actual DOI from DSpace 6.x metadata list format."""
    if not metadata_list:
        return None
    for entry in metadata_list:
        key = entry.get('key', '')
        value = (entry.get('value') or '').strip()
        if key in ('dc.identifier.doi', 'dc.identifier') and value and '10.' in value:
            if value.startswith('https://doi.org/'):
                return value[len('https://doi.org/'):]
            if value.startswith('http://doi.org/'):
                return value[len('http://doi.org/'):]
            if value.startswith('doi:'):
                return value[4:]
            if value.startswith('10.'):
                return value
    return None


def _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi):
    """Apply mapped DSpace legacy metadata to a Publication object."""
    publication.document_title = mapped_data['publication']['document_title']
    publication.document_description = mapped_data['publication'].get('document_description', '')
    publication.resource_type_id = resource_type_id
    publication.doi = doi
    publication.document_docid = handle if handle else f"LegacyItem:{item_id}"
    publication.handle_url = f"{DSPACE_LEGACY_URL}/handle/{handle}" if handle else None
    publication.owner = 'DSpace Legacy Repository'


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
    Sync single DSpace Legacy item to DOCiD.
    Supports update_existing to update metadata on re-import.
    Extracts actual DOI from metadata (no longer leaves doi empty).
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
      - name: update_existing
        in: query
        type: boolean
        default: false
        description: If true, update metadata for already-synced items
    responses:
      201:
        description: Item synced successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            status:
              type: string
              enum: [created, updated, skipped, unchanged, error]
            publication_id:
              type: integer
            docid:
              type: string
            handle:
              type: string
      200:
        description: Item already synced (skipped, unchanged, or updated)
      404:
        description: Item not found
      500:
        description: Sync failed
    """
    current_user_id = get_jwt_identity()
    update_existing = request.args.get('update_existing', 'false').lower() == 'true'

    # Use handle or legacy-item-{id} as the mapping key
    legacy_uuid = f"legacy-item-{item_id}"

    # Check if already synced
    existing_mapping = DSpaceMapping.query.filter_by(dspace_uuid=legacy_uuid).first()

    if existing_mapping and not update_existing:
        return jsonify({
            'success': True,
            'status': 'skipped',
            'publication_id': existing_mapping.publication_id,
            'docid': existing_mapping.publication.document_docid,
            'handle': existing_mapping.dspace_handle
        }), 200

    # Get DSpace item
    client = get_dspace_legacy_client()
    client.authenticate()
    dspace_item = client.get_item(item_id)

    if not dspace_item:
        client.logout()
        return jsonify({'success': False, 'status': 'error', 'error': f'Item {item_id} not found'}), 404

    metadata_list = dspace_item.get('metadata', [])
    new_metadata_hash = client.calculate_metadata_hash(metadata_list)
    mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(dspace_item, current_user_id)
    doi = _extract_legacy_doi(metadata_list)
    client.logout()

    try:
        handle = dspace_item.get('handle', f'legacy/{item_id}')

        # Resolve resource type
        resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
        resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
        resource_type_id = resource_type.id if resource_type else 1

        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

        if existing_mapping and update_existing:
            # Check if metadata changed
            if existing_mapping.dspace_metadata_hash == new_metadata_hash:
                return jsonify({
                    'success': True,
                    'status': 'unchanged',
                    'publication_id': existing_mapping.publication_id,
                    'docid': existing_mapping.publication.document_docid,
                    'handle': handle
                }), 200

            # Update existing
            publication = existing_mapping.publication
            publication.user_id = current_user_id
            _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)

            PublicationCreators.query.filter_by(publication_id=publication.id).delete()
            _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)

            existing_mapping.dspace_metadata_hash = new_metadata_hash
            existing_mapping.sync_status = 'synced'
            existing_mapping.error_message = None

            db.session.commit()
            record_status = 'updated'
        else:
            # Create new
            publication = Publications(user_id=current_user_id)
            _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)

            db.session.add(publication)
            db.session.flush()

            _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)

            mapping = DSpaceMapping(
                dspace_handle=handle,
                dspace_uuid=legacy_uuid,
                dspace_url=DSPACE_LEGACY_URL,
                publication_id=publication.id,
                sync_status='synced',
                dspace_metadata_hash=new_metadata_hash
            )
            db.session.add(mapping)
            db.session.commit()
            record_status = 'created'

        logger.info(f"Legacy item {item_id} {record_status} as publication {publication.id}")

        return jsonify({
            'success': True,
            'status': record_status,
            'publication_id': publication.id,
            'docid': publication.document_docid,
            'handle': handle
        }), 201 if record_status == 'created' else 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing legacy item {item_id}: {str(e)}")
        return jsonify({'success': False, 'status': 'error', 'error': str(e)}), 500


@dspace_legacy_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
def batch_sync():
    """
    Batch sync DSpace Legacy items to DOCiD.
    Prefetches existing mappings. Uses per-item savepoints.
    Reuses single authenticated client for entire batch.
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
              description: Number of items to sync (max 200)
            offset:
              type: integer
              default: 0
              description: Offset for pagination
            update_existing:
              type: boolean
              default: false
              description: Update metadata for already-synced items
    responses:
      200:
        description: Batch sync completed
        schema:
          type: object
          properties:
            total:
              type: integer
            created:
              type: integer
            updated:
              type: integer
            unchanged:
              type: integer
            skipped:
              type: integer
            errors:
              type: integer
            items:
              type: array
    """
    current_user_id = get_jwt_identity()
    data = request.get_json() or {}

    limit = min(data.get('limit', 10), 200)
    offset = max(data.get('offset', 0), 0)
    update_existing = data.get('update_existing', False)

    # Single authenticated client for entire batch
    client = get_dspace_legacy_client()
    client.authenticate()
    items = client.get_items(limit=limit, offset=offset)

    if not items:
        client.logout()
        return jsonify({'error': 'Failed to fetch items'}), 500

    # --- Prefetch existing mappings ---
    incoming_legacy_uuids = [f"legacy-item-{item.get('id')}" for item in items if item.get('id')]
    existing_mappings_map = {}
    if incoming_legacy_uuids:
        existing_mappings = DSpaceMapping.query.filter(
            DSpaceMapping.dspace_uuid.in_(incoming_legacy_uuids)
        ).all()
        existing_mappings_map = {m.dspace_uuid: m for m in existing_mappings}

    # --- Cache resource types and author role ---
    resource_type_cache = {rt.resource_type: rt.id for rt in ResourceTypes.query.all()}
    author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
    author_role_id = author_role.role_id if author_role else None

    results = {
        'total': len(items),
        'created': 0,
        'updated': 0,
        'unchanged': 0,
        'skipped': 0,
        'errors': 0,
        'items': []
    }

    for item_summary in items:
        item_id = item_summary.get('id')
        handle = item_summary.get('handle', f'legacy/{item_id}')
        legacy_uuid = f"legacy-item-{item_id}"

        try:
            savepoint = db.session.begin_nested()

            existing_mapping = existing_mappings_map.get(legacy_uuid)

            if existing_mapping and not update_existing:
                savepoint.rollback()
                results['skipped'] += 1
                results['items'].append({
                    'item_id': item_id, 'handle': handle,
                    'status': 'skipped',
                    'publication_id': existing_mapping.publication_id,
                    'docid': existing_mapping.publication.document_docid
                })
                continue

            # Get full item
            full_item = client.get_item(item_id)
            if not full_item:
                savepoint.rollback()
                results['errors'] += 1
                results['items'].append({
                    'item_id': item_id, 'handle': handle,
                    'status': 'error', 'error': 'failed_to_fetch'
                })
                continue

            metadata_list = full_item.get('metadata', [])
            new_metadata_hash = client.calculate_metadata_hash(metadata_list)
            mapped_data = DSpaceLegacyMetadataMapper.dspace_to_docid(full_item, current_user_id)
            doi = _extract_legacy_doi(metadata_list)
            resource_type_id = resource_type_cache.get(
                mapped_data['publication'].get('resource_type', 'Text'), 1
            )

            if existing_mapping and update_existing:
                # Check if metadata changed
                if existing_mapping.dspace_metadata_hash == new_metadata_hash:
                    savepoint.rollback()
                    results['unchanged'] += 1
                    results['items'].append({
                        'item_id': item_id, 'handle': handle,
                        'status': 'unchanged',
                        'publication_id': existing_mapping.publication_id,
                        'docid': existing_mapping.publication.document_docid
                    })
                    continue

                # Update
                publication = existing_mapping.publication
                publication.user_id = current_user_id
                _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)
                PublicationCreators.query.filter_by(publication_id=publication.id).delete()
                _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)
                existing_mapping.dspace_metadata_hash = new_metadata_hash
                existing_mapping.sync_status = 'synced'
                existing_mapping.error_message = None

                savepoint.commit()
                results['updated'] += 1
                results['items'].append({
                    'item_id': item_id, 'handle': handle,
                    'status': 'updated',
                    'publication_id': publication.id,
                    'docid': publication.document_docid
                })
            else:
                # Create new
                publication = Publications(user_id=current_user_id)
                _apply_legacy_data_to_publication(publication, mapped_data, resource_type_id, handle, item_id, doi)

                db.session.add(publication)
                db.session.flush()

                _save_legacy_creators(publication.id, mapped_data.get('creators', []), author_role_id)

                mapping = DSpaceMapping(
                    dspace_handle=handle,
                    dspace_uuid=legacy_uuid,
                    dspace_url=DSPACE_LEGACY_URL,
                    publication_id=publication.id,
                    sync_status='synced',
                    dspace_metadata_hash=new_metadata_hash
                )
                db.session.add(mapping)

                savepoint.commit()
                results['created'] += 1
                results['items'].append({
                    'item_id': item_id, 'handle': handle,
                    'status': 'created',
                    'publication_id': publication.id,
                    'docid': publication.document_docid
                })

        except Exception as e:
            db.session.rollback()
            results['errors'] += 1
            results['items'].append({
                'item_id': item_id, 'handle': handle,
                'status': 'error', 'error': str(e)
            })

    # Single final commit + logout
    db.session.commit()
    client.logout()

    logger.info(
        f"Legacy batch sync: {results['created']} created, {results['updated']} updated, "
        f"{results['unchanged']} unchanged, {results['skipped']} skipped, {results['errors']} errors"
    )

    return jsonify(results), 200


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
    ).order_by(DSpaceMapping.last_sync_at.desc()).first()

    last_sync = last_mapping.last_sync_at.isoformat() if last_mapping and last_mapping.last_sync_at else None

    return jsonify({
        'total_synced': total_synced,
        'last_sync': last_sync,
        'dspace_url': DSPACE_LEGACY_URL,
        'version': '6.x'
    }), 200
