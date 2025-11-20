"""
DSpace Integration API Endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, DSpaceMapping, UserAccount, PublicationCreators, CreatorsRoles
from app.service_dspace import DSpaceClient, DSpaceMetadataMapper
import os

dspace_bp = Blueprint('dspace', __name__, url_prefix='/api/v1/dspace')

# DSpace configuration
DSPACE_BASE_URL = os.getenv('DSPACE_BASE_URL', 'https://demo.dspace.org/server')
DSPACE_USERNAME = os.getenv('DSPACE_USERNAME', 'dspacedemo+admin@gmail.com')
DSPACE_PASSWORD = os.getenv('DSPACE_PASSWORD', 'dspace')


def get_dspace_client():
    """Create and authenticate DSpace client"""
    client = DSpaceClient(DSPACE_BASE_URL, DSPACE_USERNAME, DSPACE_PASSWORD)
    client.authenticate()
    return client


def save_publication_creators(publication_id, creators_data):
    """
    Save creators to publication_creators table

    Args:
        publication_id: Publication ID
        creators_data: List of creator dictionaries from DSpaceMetadataMapper
    """
    if not creators_data:
        return

    creators = []
    for creator_data in creators_data:
        # Get role_id for the creator role
        role_name = creator_data.get('creator_role', 'Author')
        role = CreatorsRoles.query.filter_by(role_name=role_name).first()

        if not role:
            # Default to "Author" role if not found
            role = CreatorsRoles.query.filter_by(role_name='Author').first()

        if not role:
            continue  # Skip if no role found

        # Parse full name into family_name and given_name
        full_name = creator_data.get('creator_name', '')
        name_parts = full_name.split(',', 1) if ',' in full_name else full_name.rsplit(' ', 1)

        if len(name_parts) == 2:
            family_name = name_parts[0].strip()
            given_name = name_parts[1].strip()
        else:
            family_name = full_name.strip()
            given_name = ''

        # Only set identifier and identifier_type if there's an actual identifier value
        identifier_value = creator_data.get('orcid_id', '') or ''
        identifier_type_value = 'orcid' if identifier_value else ''

        creators.append(PublicationCreators(
            publication_id=publication_id,
            family_name=family_name,
            given_name=given_name,
            identifier=identifier_value,
            identifier_type=identifier_type_value,
            role_id=role.role_id
        ))

    if creators:
        db.session.bulk_save_objects(creators)


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
    Sync single DSpace item to DOCiD publications table

    Imports a DSpace item and creates a corresponding publication record in DOCiD database.
    Extracts metadata including title, description, authors, dates, identifiers, and language.
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
    responses:
      201:
        description: Item synced successfully to publications table
        schema:
          type: object
          properties:
            success:
              type: boolean
              description: Sync operation success status
              example: true
            publication_id:
              type: integer
              description: Created publication ID in DOCiD database
              example: 123
            docid:
              type: string
              description: Generated DOCiD identifier
              example: "20.500.DSPACE/017138d0-9ced-4c49-9be1-5eebe816c528"
            doi:
              type: string
              description: DSpace handle saved as DOI
              example: "123456789/131"
            dspace_handle:
              type: string
              description: DSpace handle identifier
              example: "123456789/131"
            message:
              type: string
              description: Success message
              example: "Item synced successfully"
      200:
        description: Item already synced (existing record found)
        schema:
          type: object
          properties:
            message:
              type: string
              description: Status message
              example: "Item already synced"
            publication_id:
              type: integer
              description: Existing publication ID
            docid:
              type: string
              description: Existing DOCiD identifier
      404:
        description: Item not found in DSpace
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Item 017138d0-9ced-4c49-9be1-5eebe816c528 not found in DSpace"
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Server error during sync operation
    """
    try:
        current_user_id = get_jwt_identity()

        # Get DSpace item
        client = get_dspace_client()
        dspace_item = client.get_item(uuid)

        if not dspace_item:
            return jsonify({'error': f'Item {uuid} not found in DSpace'}), 404

        handle = dspace_item.get('handle')

        # Check if already synced
        existing = DSpaceMapping.query.filter_by(dspace_uuid=uuid).first()
        if existing:
            return jsonify({
                'message': 'Item already synced',
                'publication_id': existing.publication_id,
                'docid': existing.publication.document_docid
            }), 200

        # Transform metadata
        mapped_data = DSpaceMetadataMapper.dspace_to_docid(dspace_item, current_user_id)

        # Get resource type ID
        from app.models import ResourceTypes
        resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
        resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
        resource_type_id = resource_type.id if resource_type else 1

        # Use DSpace handle as document_docid
        document_docid = handle if handle else f"20.500.DSPACE/{uuid}"

        # Construct full resolvable URL for handle_url
        handle_url = None
        if handle:
            base_url = DSPACE_BASE_URL.replace('/server', '')
            handle_url = f"{base_url}/handle/{handle}"

        # Create publication
        publication = Publications(
            user_id=current_user_id,
            document_title=mapped_data['publication']['document_title'],
            document_description=mapped_data['publication'].get('document_description', ''),
            resource_type_id=resource_type_id,
            doi=handle if handle else '',  # Use DSpace handle as DOI
            document_docid=document_docid,  # DSpace handle (not full URL)
            handle_url=handle_url,  # Full resolvable URL for DSpace item
            owner='DSpace Repository',  # Temporary - will be linked to university ID later
        )

        db.session.add(publication)
        db.session.flush()  # Get publication ID

        # Save creators
        save_publication_creators(publication.id, mapped_data.get('creators', []))

        # Create mapping
        mapping = DSpaceMapping(
            dspace_handle=handle,
            dspace_uuid=uuid,
            dspace_url=DSPACE_BASE_URL,
            publication_id=publication.id,
            sync_status='synced',
            dspace_metadata_hash=client.calculate_metadata_hash(dspace_item.get('metadata', {}))
        )

        db.session.add(mapping)
        db.session.commit()

        return jsonify({
            'success': True,
            'publication_id': publication.id,
            'docid': publication.document_docid,
            'doi': publication.doi,
            'dspace_handle': handle,
            'message': 'Item synced successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@dspace_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
def sync_batch():
    """
    Batch sync multiple DSpace items to DOCiD publications table

    Imports multiple items from DSpace in one operation. Useful for bulk importing
    repository content into DOCiD.
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
              example: 0
            size:
              type: integer
              default: 50
              description: Number of items to sync
              example: 50
            skip_existing:
              type: boolean
              default: true
              description: Skip items that are already synced
              example: true
    responses:
      200:
        description: Batch sync completed
        schema:
          type: object
          properties:
            total:
              type: integer
              description: Total items processed
            created:
              type: integer
              description: Number of items successfully synced
            skipped:
              type: integer
              description: Number of items skipped (already exist)
            errors:
              type: integer
              description: Number of items that failed to sync
            items:
              type: array
              description: Detailed results for each item
              items:
                type: object
                properties:
                  uuid:
                    type: string
                  handle:
                    type: string
                  status:
                    type: string
                    enum: [created, skipped, error]
                  publication_id:
                    type: integer
                  docid:
                    type: string
      401:
        description: Unauthorized - Invalid or missing JWT token
      500:
        description: Server error during batch sync
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        page = data.get('page', 0)
        size = data.get('size', 50)
        skip_existing = data.get('skip_existing', True)

        # Get items from DSpace
        client = get_dspace_client()
        items_data = client.get_items(page=page, size=size)

        items = items_data.get('_embedded', {}).get('items', [])

        results = {
            'total': len(items),
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'items': []
        }

        for item in items:
            uuid = item.get('uuid')
            handle = item.get('handle')

            try:
                # Check if exists
                if skip_existing:
                    existing = DSpaceMapping.query.filter_by(dspace_uuid=uuid).first()
                    if existing:
                        results['skipped'] += 1
                        results['items'].append({
                            'uuid': uuid,
                            'handle': handle,
                            'status': 'skipped',
                            'reason': 'already_exists'
                        })
                        continue

                # Get full item data
                full_item = client.get_item(uuid)
                if not full_item:
                    results['errors'] += 1
                    results['items'].append({
                        'uuid': uuid,
                        'handle': handle,
                        'status': 'error',
                        'reason': 'failed_to_fetch'
                    })
                    continue

                # Map and create
                mapped_data = DSpaceMetadataMapper.dspace_to_docid(full_item, current_user_id)

                # Get resource type ID
                from app.models import ResourceTypes
                resource_type_name = mapped_data['publication'].get('resource_type', 'Text')
                resource_type_obj = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                resource_type_id = resource_type_obj.id if resource_type_obj else 1

                # Use DSpace handle as document_docid
                document_docid = handle if handle else f"20.500.DSPACE/{uuid}"

                # Construct full resolvable URL for handle_url
                handle_url = None
                if handle:
                    base_url = DSPACE_BASE_URL.replace('/server', '')
                    handle_url = f"{base_url}/handle/{handle}"

                publication = Publications(
                    user_id=current_user_id,
                    document_title=mapped_data['publication']['document_title'],
                    document_description=mapped_data['publication'].get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi=handle if handle else '',  # Use DSpace handle as DOI
                    document_docid=document_docid,  # DSpace handle (not full URL)
                    handle_url=handle_url,  # Full resolvable URL for DSpace item
                    owner='DSpace Repository',  # Temporary - will be linked to university ID later
                )

                db.session.add(publication)
                db.session.flush()

                # Save creators
                save_publication_creators(publication.id, mapped_data.get('creators', []))

                mapping = DSpaceMapping(
                    dspace_handle=handle,
                    dspace_uuid=uuid,
                    dspace_url=DSPACE_BASE_URL,
                    publication_id=publication.id,
                    sync_status='synced',
                    dspace_metadata_hash=client.calculate_metadata_hash(full_item.get('metadata', {}))
                )

                db.session.add(mapping)
                db.session.commit()

                results['created'] += 1
                results['items'].append({
                    'uuid': uuid,
                    'handle': handle,
                    'publication_id': publication.id,
                    'docid': publication.document_docid,
                    'status': 'created'
                })

            except Exception as e:
                db.session.rollback()
                results['errors'] += 1
                results['items'].append({
                    'uuid': uuid,
                    'handle': handle,
                    'status': 'error',
                    'reason': str(e)
                })

        return jsonify(results), 200

    except Exception as e:
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
