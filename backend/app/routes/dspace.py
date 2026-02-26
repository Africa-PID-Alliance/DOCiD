"""
DSpace Integration API Endpoints (DSpace 7/8/9)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, DSpaceMapping, ResourceTypes, PublicationCreators, CreatorsRoles
from app.service_dspace import DSpaceClient, DSpaceMetadataMapper
import os
import logging

logger = logging.getLogger(__name__)

dspace_bp = Blueprint('dspace', __name__, url_prefix='/api/v1/dspace')

# DSpace configuration
DSPACE_BASE_URL = os.getenv('DSPACE_BASE_URL', 'https://demo.dspace.org/server')
DSPACE_UI_BASE_URL = os.getenv('DSPACE_UI_BASE_URL', '')  # e.g. https://demo.dspace.org
DSPACE_USERNAME = os.getenv('DSPACE_USERNAME', 'dspacedemo+admin@gmail.com')
DSPACE_PASSWORD = os.getenv('DSPACE_PASSWORD', 'dspace')


def _get_dspace_ui_base_url():
    """Get UI base URL from config, falling back to stripping /server from API URL."""
    if DSPACE_UI_BASE_URL:
        return DSPACE_UI_BASE_URL.rstrip('/')
    return DSPACE_BASE_URL.replace('/server', '').rstrip('/')


def get_dspace_client():
    """Create and authenticate DSpace client"""
    client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)
    client.authenticate()
    return client


def save_publication_creators(publication_id, creators_data, author_role_id=None):
    """
    Save creators to publication_creators table.
    Accepts pre-resolved author_role_id to avoid per-creator DB lookups.
    """
    if not creators_data:
        return

    if author_role_id is None:
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

    if author_role_id is None:
        return

    creators = []
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

        creators.append(PublicationCreators(
            publication_id=publication_id,
            family_name=family_name,
            given_name=given_name,
            identifier=identifier_value,
            identifier_type=identifier_type_value,
            role_id=author_role_id
        ))

    if creators:
        db.session.bulk_save_objects(creators)


def _parse_doi_from_string(value):
    """
    Extract a clean DOI (10.xxxx/yyyy) from a messy string.
    Handles real-world university metadata formats:
      'doi: 10.3389/fped.2019.00008.'
      'DOI: http://dx.doi.org/10.20961/carakatani.v38i1.57446'
      'https://doi.org/10.1007/s40204-021-00164-5'
      '. https://doi.org/10.1371/journal.pone.0248281'
      'doi.org/10.1007/s42250-022-00553-8'
      'DOI:  10.1080/23311932.2021.1917834'
    """
    if not value or '10.' not in value:
        return None
    import re
    match = re.search(r'(10\.\d{4,9}/[^\s]+)', value)
    if match:
        return match.group(1).rstrip('.,;:)')
    return None


def _extract_doi_from_metadata(metadata):
    """
    Extract actual DOI from DSpace metadata.
    DSpace stores DOI in various fields; handle is NOT a DOI.
    Checks dc.identifier.doi, dc.identifier.other, and dcterms.identifier.
    """
    if not metadata:
        return None

    doi_fields = ['dc.identifier.doi', 'dc.identifier.other', 'dcterms.identifier']
    for field in doi_fields:
        values = metadata.get(field, [])
        for val in values:
            raw_value = (val.get('value') or '').strip()
            doi = _parse_doi_from_string(raw_value)
            if doi:
                return doi
    return None


def _build_handle_url(handle):
    """Build full resolvable URL for a DSpace handle."""
    if not handle:
        return None
    return f"{_get_dspace_ui_base_url()}/handle/{handle}"


def _apply_dspace_data_to_publication(publication, mapped_data, resource_type_id, handle, uuid, doi):
    """Apply mapped DSpace metadata to a Publication object."""
    publication.document_title = mapped_data['publication']['document_title']
    publication.document_description = mapped_data['publication'].get('document_description', '')
    publication.resource_type_id = resource_type_id
    publication.doi = doi
    publication.document_docid = handle if handle else f"DSpaceUUID:{uuid}"
    publication.handle_url = _build_handle_url(handle)
    publication.owner = 'DSpace Repository'


@dspace_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """
    Get DSpace integration configuration

    Returns the current DSpace server configuration and connection status
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    responses:
      200:
        description: DSpace configuration retrieved successfully
        schema:
          type: object
          properties:
            dspace_url:
              type: string
              description: DSpace server base URL
              example: https://demo.dspace.org/server
            configured:
              type: boolean
              description: Whether DSpace credentials are configured
              example: true
            status:
              type: string
              description: Connection status
              example: connected
      401:
        description: Unauthorized - Invalid or missing JWT token
    """
    return jsonify({
        'dspace_url': DSPACE_BASE_URL,
        'configured': bool(DSPACE_USERNAME and DSPACE_PASSWORD),
        'status': 'connected'
    })


@dspace_bp.route('/items', methods=['GET'])
@jwt_required()
def get_dspace_items():
    """
    Get items from DSpace repository

    Fetches a paginated list of items from the configured DSpace repository
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 0
        description: Page number (0-indexed)
        example: 0
      - name: size
        in: query
        type: integer
        default: 20
        description: Number of items per page
        example: 20
    responses:
      200:
        description: Items retrieved successfully
        schema:
          type: object
          properties:
            _embedded:
              type: object
              properties:
                items:
                  type: array
                  description: Array of DSpace items
                  items:
                    type: object
                    properties:
                      uuid:
                        type: string
                        description: Item UUID
                      handle:
                        type: string
                        description: Item handle
                      name:
                        type: string
                        description: Item name/title
            page:
              type: object
              description: Pagination information
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Failed to fetch items from DSpace
    """
    try:
        page = request.args.get('page', 0, type=int)
        size = request.args.get('size', 20, type=int)

        client = get_dspace_client()
        items_data = client.get_items(page=page, size=size)

        if not items_data:
            return jsonify({'error': 'Failed to fetch items from DSpace'}), 500

        return jsonify(items_data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/sync/item/<uuid>', methods=['POST'])
@jwt_required()
def sync_single_item(uuid):
    """
    Sync single DSpace item to DOCiD publications table.
    Supports update_existing to update metadata on re-import.
    Extracts actual DOI from metadata (handle is NOT used as DOI).
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    parameters:
      - name: uuid
        in: path
        type: string
        required: true
        description: DSpace item UUID to sync
        example: 017138d0-9ced-4c49-9be1-5eebe816c528
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
        description: Item not found in DSpace
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Server error during sync operation
    """
    try:
        current_user_id = get_jwt_identity()
        update_existing = request.args.get('update_existing', 'false').lower() == 'true'

        # Get DSpace item
        client = get_dspace_client()
        dspace_item = client.get_item(uuid)

        if not dspace_item:
            return jsonify({'success': False, 'status': 'error', 'error': f'Item {uuid} not found in DSpace'}), 404

        handle = dspace_item.get('handle')
        metadata = dspace_item.get('metadata', {})
        new_metadata_hash = client.calculate_metadata_hash(metadata)

        # Check if already synced
        existing_mapping = DSpaceMapping.query.filter_by(dspace_uuid=uuid).first()

        if existing_mapping and not update_existing:
            return jsonify({
                'success': True,
                'status': 'skipped',
                'publication_id': existing_mapping.publication_id,
                'docid': existing_mapping.publication.document_docid,
                'handle': handle
            }), 200

        # Transform metadata
        mapped_data = DSpaceMetadataMapper.dspace_to_docid(dspace_item, current_user_id)
        doi = _extract_doi_from_metadata(metadata)

        # Resolve resource type
        resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
        resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
        resource_type_id = resource_type.id if resource_type else 1

        # Resolve author role once
        author_role = CreatorsRoles.query.filter_by(role_name='Author').first()
        author_role_id = author_role.role_id if author_role else None

        if existing_mapping and update_existing:
            # Check if metadata actually changed
            if existing_mapping.dspace_metadata_hash == new_metadata_hash:
                return jsonify({
                    'success': True,
                    'status': 'unchanged',
                    'publication_id': existing_mapping.publication_id,
                    'docid': existing_mapping.publication.document_docid,
                    'handle': handle
                }), 200

            # Update existing publication
            publication = existing_mapping.publication
            _apply_dspace_data_to_publication(publication, mapped_data, resource_type_id, handle, uuid, doi)

            # Replace creators
            PublicationCreators.query.filter_by(publication_id=publication.id).delete()
            save_publication_creators(publication.id, mapped_data.get('creators', []), author_role_id)

            # Update mapping
            existing_mapping.dspace_metadata_hash = new_metadata_hash
            existing_mapping.sync_status = 'synced'
            existing_mapping.error_message = None

            db.session.commit()
            record_status = 'updated'
        else:
            # Create new publication
            publication = Publications(user_id=current_user_id)
            _apply_dspace_data_to_publication(publication, mapped_data, resource_type_id, handle, uuid, doi)

            db.session.add(publication)
            db.session.flush()

            save_publication_creators(publication.id, mapped_data.get('creators', []), author_role_id)

            # Create mapping
            mapping = DSpaceMapping(
                dspace_handle=handle,
                dspace_uuid=uuid,
                dspace_url=DSPACE_BASE_URL,
                publication_id=publication.id,
                sync_status='synced',
                dspace_metadata_hash=new_metadata_hash
            )
            db.session.add(mapping)
            db.session.commit()
            record_status = 'created'

        logger.info(f"DSpace item {uuid} {record_status} as publication {publication.id}")

        return jsonify({
            'success': True,
            'status': record_status,
            'publication_id': publication.id,
            'docid': publication.document_docid,
            'handle': handle
        }), 201 if record_status == 'created' else 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error syncing DSpace item {uuid}: {str(e)}")
        return jsonify({'success': False, 'status': 'error', 'error': str(e)}), 500


@dspace_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
def sync_batch():
    """
    Batch sync DSpace items to DOCiD.
    Prefetches existing mappings to avoid N+1. Uses per-item savepoints.
    Supports update_existing and incremental skip via metadata hash.
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: false
        schema:
          type: object
          properties:
            page:
              type: integer
              default: 0
              description: Page number to fetch from DSpace
            size:
              type: integer
              default: 50
              description: Number of items to sync (max 200)
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
      401:
        description: Unauthorized
      500:
        description: Server error
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        page = data.get('page', 0)
        size = min(data.get('size', 50), 200)
        update_existing = data.get('update_existing', False)

        # Get items from DSpace
        client = get_dspace_client()
        items_data = client.get_items(page=page, size=size)
        items = items_data.get('_embedded', {}).get('items', [])

        # --- Prefetch existing mappings to avoid N+1 ---
        incoming_uuids = [item.get('uuid') for item in items if item.get('uuid')]
        existing_mappings_map = {}
        if incoming_uuids:
            existing_mappings = DSpaceMapping.query.filter(
                DSpaceMapping.dspace_uuid.in_(incoming_uuids)
            ).all()
            existing_mappings_map = {m.dspace_uuid: m for m in existing_mappings}

        # --- Cache resource types and author role once ---
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

        for item in items:
            item_uuid = item.get('uuid')
            handle = item.get('handle')

            try:
                savepoint = db.session.begin_nested()

                existing_mapping = existing_mappings_map.get(item_uuid)

                if existing_mapping and not update_existing:
                    savepoint.rollback()
                    results['skipped'] += 1
                    results['items'].append({
                        'uuid': item_uuid,
                        'handle': handle,
                        'status': 'skipped',
                        'publication_id': existing_mapping.publication_id,
                        'docid': existing_mapping.publication.document_docid
                    })
                    continue

                # Get full item data
                full_item = client.get_item(item_uuid)
                if not full_item:
                    savepoint.rollback()
                    results['errors'] += 1
                    results['items'].append({
                        'uuid': item_uuid, 'handle': handle,
                        'status': 'error', 'error': 'failed_to_fetch'
                    })
                    continue

                metadata = full_item.get('metadata', {})
                new_metadata_hash = client.calculate_metadata_hash(metadata)
                mapped_data = DSpaceMetadataMapper.dspace_to_docid(full_item, current_user_id)
                doi = _extract_doi_from_metadata(metadata)
                resource_type_id = resource_type_cache.get(
                    mapped_data['publication'].get('resource_type', 'Text'), 1
                )

                if existing_mapping and update_existing:
                    # Check if metadata changed
                    if existing_mapping.dspace_metadata_hash == new_metadata_hash:
                        savepoint.rollback()
                        results['unchanged'] += 1
                        results['items'].append({
                            'uuid': item_uuid, 'handle': handle,
                            'status': 'unchanged',
                            'publication_id': existing_mapping.publication_id,
                            'docid': existing_mapping.publication.document_docid
                        })
                        continue

                    # Update
                    publication = existing_mapping.publication
                    _apply_dspace_data_to_publication(publication, mapped_data, resource_type_id, handle, item_uuid, doi)
                    PublicationCreators.query.filter_by(publication_id=publication.id).delete()
                    save_publication_creators(publication.id, mapped_data.get('creators', []), author_role_id)
                    existing_mapping.dspace_metadata_hash = new_metadata_hash
                    existing_mapping.sync_status = 'synced'
                    existing_mapping.error_message = None

                    savepoint.commit()
                    results['updated'] += 1
                    results['items'].append({
                        'uuid': item_uuid, 'handle': handle,
                        'status': 'updated',
                        'publication_id': publication.id,
                        'docid': publication.document_docid
                    })
                else:
                    # Create new
                    publication = Publications(user_id=current_user_id)
                    _apply_dspace_data_to_publication(publication, mapped_data, resource_type_id, handle, item_uuid, doi)

                    db.session.add(publication)
                    db.session.flush()

                    save_publication_creators(publication.id, mapped_data.get('creators', []), author_role_id)

                    mapping = DSpaceMapping(
                        dspace_handle=handle,
                        dspace_uuid=item_uuid,
                        dspace_url=DSPACE_BASE_URL,
                        publication_id=publication.id,
                        sync_status='synced',
                        dspace_metadata_hash=new_metadata_hash
                    )
                    db.session.add(mapping)

                    savepoint.commit()
                    results['created'] += 1
                    results['items'].append({
                        'uuid': item_uuid, 'handle': handle,
                        'status': 'created',
                        'publication_id': publication.id,
                        'docid': publication.document_docid
                    })

            except Exception as e:
                db.session.rollback()
                results['errors'] += 1
                results['items'].append({
                    'uuid': item_uuid, 'handle': handle,
                    'status': 'error', 'error': str(e)
                })

        # Single final commit
        db.session.commit()

        logger.info(
            f"DSpace batch sync: {results['created']} created, {results['updated']} updated, "
            f"{results['unchanged']} unchanged, {results['skipped']} skipped, {results['errors']} errors"
        )

        return jsonify(results), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in DSpace batch sync: {str(e)}")
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/mappings', methods=['GET'])
@jwt_required()
def get_mappings():
    """Get all DSpace-DOCiD mappings"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        mappings_query = DSpaceMapping.query.order_by(DSpaceMapping.created_at.desc())
        mappings_paginated = mappings_query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            'mappings': [m.to_dict() for m in mappings_paginated.items],
            'total': mappings_paginated.total,
            'page': page,
            'per_page': per_page,
            'pages': mappings_paginated.pages
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/mappings/<path:handle>', methods=['GET'])
@jwt_required()
def get_mapping_by_handle(handle):
    """Get mapping by DSpace handle"""
    try:
        mapping = DSpaceMapping.query.filter_by(dspace_handle=handle).first()

        if not mapping:
            return jsonify({'error': 'Mapping not found'}), 404

        return jsonify(mapping.to_dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Get DSpace integration statistics

    Returns statistics about synced items from DSpace to DOCiD
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            total_synced:
              type: integer
              description: Total number of synced items
              example: 100
            synced:
              type: integer
              description: Number of successfully synced items
              example: 95
            errors:
              type: integer
              description: Number of items with sync errors
              example: 5
            pending:
              type: integer
              description: Number of items pending sync
              example: 0
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Server error while fetching statistics
    """
    try:
        total_mappings = DSpaceMapping.query.count()
        synced = DSpaceMapping.query.filter_by(sync_status='synced').count()
        errors = DSpaceMapping.query.filter_by(sync_status='error').count()

        return jsonify({
            'total_synced': total_mappings,
            'synced': synced,
            'errors': errors,
            'pending': total_mappings - synced - errors
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/sync/delete/<int:publication_id>', methods=['DELETE'])
@jwt_required()
def delete_synced_item(publication_id):
    """
    Delete a synced DSpace item and its mapping

    Removes a publication record that was synced from DSpace along with its mapping.
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: Publication ID to delete
    responses:
      200:
        description: Item deleted successfully
      404:
        description: Publication or mapping not found
      401:
        description: Unauthorized
      500:
        description: Server error during deletion
    """
    try:
        # Find the mapping
        mapping = DSpaceMapping.query.filter_by(publication_id=publication_id).first()
        if not mapping:
            return jsonify({'error': 'DSpace mapping not found for this publication'}), 404

        # Find the publication
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({'error': 'Publication not found'}), 404

        # Delete the mapping first
        db.session.delete(mapping)

        # Delete associated creators
        PublicationCreators.query.filter_by(publication_id=publication_id).delete()

        # Delete the publication
        db.session.delete(publication)

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Publication {publication_id} and its DSpace mapping deleted successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/sync/delete-all', methods=['DELETE'])
@jwt_required()
def delete_all_synced_items():
    """
    Delete all synced DSpace items and their mappings

    WARNING: This will delete all publications synced from DSpace
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    responses:
      200:
        description: All synced items deleted successfully
      401:
        description: Unauthorized
      500:
        description: Server error during deletion
    """
    try:
        # Get all mappings
        mappings = DSpaceMapping.query.all()
        publication_ids = [m.publication_id for m in mappings]

        # Delete all creators for these publications
        for pub_id in publication_ids:
            PublicationCreators.query.filter_by(publication_id=pub_id).delete()

        # Delete all publications
        Publications.query.filter(Publications.id.in_(publication_ids)).delete(synchronize_session=False)

        # Delete all mappings
        DSpaceMapping.query.delete()

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Deleted {len(publication_ids)} synced publications and their mappings'
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/preview/item/<uuid>', methods=['GET'])
@jwt_required()
def preview_item_metadata(uuid):
    """
    Preview DSpace item metadata extraction without syncing

    Shows exactly what metadata will be extracted from a DSpace item without creating
    a database record. Useful for testing and verification before syncing.
    ---
    tags:
      - DSpace Integration
    security:
      - Bearer: []
    parameters:
      - name: uuid
        in: path
        type: string
        required: true
        description: DSpace item UUID to preview
        example: 017138d0-9ced-4c49-9be1-5eebe816c528
    responses:
      200:
        description: Metadata extracted successfully
        schema:
          type: object
          properties:
            dspace_uuid:
              type: string
              description: DSpace item UUID
            dspace_handle:
              type: string
              description: DSpace handle
            raw_metadata:
              type: object
              description: Original DSpace metadata (Dublin Core format)
            mapped_data:
              type: object
              description: Transformed metadata for DOCiD
              properties:
                publication:
                  type: object
                  description: Publication data
                  properties:
                    document_title:
                      type: string
                    document_description:
                      type: string
                    published_date:
                      type: string
                    resource_type:
                      type: string
                creators:
                  type: array
                  description: List of authors/creators
                  items:
                    type: object
                    properties:
                      creator_name:
                        type: string
                      creator_role:
                        type: string
                extended_metadata:
                  type: object
                  description: Additional metadata (dates, identifiers, language, relations)
      404:
        description: Item not found in DSpace
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Server error during metadata extraction
    """
    try:
        current_user_id = get_jwt_identity()

        # Get DSpace item
        client = get_dspace_client()
        dspace_item = client.get_item(uuid)

        if not dspace_item:
            return jsonify({'error': f'Item {uuid} not found in DSpace'}), 404

        # Transform metadata
        mapped_data = DSpaceMetadataMapper.dspace_to_docid(dspace_item, current_user_id)

        # Return the full mapped data for preview
        return jsonify({
            'dspace_uuid': uuid,
            'dspace_handle': dspace_item.get('handle'),
            'raw_metadata': dspace_item.get('metadata'),  # Original DSpace metadata
            'mapped_data': mapped_data  # Transformed data for DOCiD
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
