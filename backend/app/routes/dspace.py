"""
DSpace Integration API Endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, DSpaceMapping, UserAccount
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


@dspace_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    """Get DSpace integration configuration"""
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
    Query params: page (default 0), size (default 20)
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
    Import single DSpace item to DOCiD

    Args:
        uuid: DSpace item UUID
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

        # Generate Handle-format DocID for DSpace items
        document_docid = f"20.500.DSPACE/{uuid}"

        # Create publication
        publication = Publications(
            user_id=current_user_id,
            document_title=mapped_data['publication']['document_title'],
            document_description=mapped_data['publication'].get('document_description', ''),
            resource_type_id=resource_type_id,
            doi='',  # Will be generated later
            document_docid=document_docid,
            owner='DSpace Repository',  # Temporary - will be linked to university ID later
        )

        db.session.add(publication)
        db.session.flush()  # Get publication ID

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
    Batch import items from DSpace

    Request body:
    {
        "page": 0,
        "size": 50,
        "skip_existing": true
    }
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

                # Generate Handle-format DocID for DSpace items
                document_docid = f"20.500.DSPACE/{uuid}"

                publication = Publications(
                    user_id=current_user_id,
                    document_title=mapped_data['publication']['document_title'],
                    document_description=mapped_data['publication'].get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi='',  # Will be generated later
                    document_docid=document_docid,
                    owner='DSpace Repository',  # Temporary - will be linked to university ID later
                )

                db.session.add(publication)
                db.session.flush()

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
    """Get DSpace integration statistics"""
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
