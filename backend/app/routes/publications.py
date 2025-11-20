# app/routes/publications.py
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Blueprint, jsonify, request, Response, abort
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from app import db
from app.models import Publications,PublicationFiles,PublicationDocuments,PublicationCreators,PublicationOrganization,PublicationFunders,PublicationProjects
from app.models import ResourceTypes,FunderTypes,CreatorsRoles,creatorsIdentifiers,PublicationIdentifierTypes,PublicationTypes,UserAccount,PublicationDrafts,PublicationAuditTrail
# from app.service_codra import push_apa_metadata
# CORDRA imports removed - functionality moved to push_to_cordra.py script
# from app.service_codra import update_object
from app.service_identifiers import IdentifierService
from sqlalchemy import desc
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import json
from config import Config

# from flasgger import Swagger

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create file handler for publications.log with rotation
file_handler = RotatingFileHandler(
    'logs/publications.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setLevel(logging.INFO)

# Create formatter and add it to handler
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)

# Create logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(file_handler)

# Also add console handler for development
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

publications_bp = Blueprint("publications", __name__, url_prefix="/api/v1/publications")

def clean_undefined_string(value):
    """Convert JavaScript 'undefined' strings to None"""
    if value and isinstance(value, str) and value.lower() == 'undefined':
        return None
    return value

@publications_bp.route('/get-list-resource-types', methods=['GET'])
# @jwt_required()
def get_resource_types():

    """
    Fetches all publications resource-types
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all resource-types
        schema:
          type: array
          items:
            type: object
            # ... properties of a resource-types object ...
      500:
        description: Internal server error
    """

    try:
        data = ResourceTypes.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching resource types found'}), 404
        data_list = [{ 'resource_type': row.resource_type, 'id': row.id} for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@publications_bp.route('/get-list-funder-types', methods=['GET'])
# @jwt_required()
def get_funder_types():

    """
    Fetches all publications funder-types
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all funder-types
        schema:
          type: array
          items:
            type: object
            # ... properties of a funder-types object ...
      500:
        description: Internal server error
    """

    try:
        data = FunderTypes.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching funder types found'}), 404
        data_list = [{ 'funder_type_name': row.funder_type_name, 'id': row.id} for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@publications_bp.route('/get-list-creators-roles', methods=['GET'])
# @jwt_required()
def get_creators_roles():

    """
    Fetches all publications  Creators & Organization creators-roles
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all  Creators & Organization creators-roles
        schema:
          type: array
          items:
            type: object
            # ... properties of a  Creators & Organization creators-roles object ...
      500:
        description: Internal server error
    """

    try:
        data = CreatorsRoles.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching creators roles found'}), 404
        data_list = [{ 'role_id': row.role_id, 'role_name': row.role_name } for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@publications_bp.route('/get-list-creators-identifiers', methods=['GET'])
# @jwt_required()
def get_creators_identifiers():

    """
    Fetches all publications  Creators & identifiers
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all  Creators & identifiers
        schema:
          type: array
          items:
            type: object
            # ... properties of a  Creators identifiers object ...
      500:
        description: Internal server error
    """

    try:
        data = creatorsIdentifiers.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching creators identifiers found'}), 404
        data_list = [{ 'id': row.id, 'identifier_name': row.identifier_name } for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@publications_bp.route('/get-list-identifier-types', methods=['GET'])
# @jwt_required()
def get_identifier_types():

    """
    Fetches all publications identifier-types
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all identifier-types
        schema:
          type: array
          items:
            type: object
            # ... properties of a identifier-types object ...
      500:
        description: Internal server error
    """

    try:
        data = PublicationIdentifierTypes.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching identifier type found'}), 404
        data_list = [{ 'identifier_type_name': row.identifier_type_name, 'id': row.id} for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



@publications_bp.route('/get-list-publication-types', methods=['GET'])
# @jwt_required()
def get_publication_types():

    """
    Fetches all publications publication-types
    ---
    tags:
      - Publications
    responses:
      200:
        description: List of all publication-types
        schema:
          type: array
          items:
            type: object
            # ... properties of a publication-types object ...
      500:
        description: Internal server error
    """

    try:
        data = PublicationTypes.query.all()
        if len(data) == 0:
            return jsonify({'message': 'No matching publication type found'}), 404
        data_list = [{ 'publication_type_name': row.publication_type_name, 'id': row.id} for row in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@publications_bp.route('/get-publications/<title>', methods=['GET'])
# @jwt_required()
def get_publications_title(title):
    """
    Fetches publications containing the specified title in their data.

    ---
    tags:
      - Publications
    parameters:
      - in: path
        name: title
        type: string
        required: true
        description: The title or partial title to search for in the publication data.
    responses:
      200:
        description: List of matching publications
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: The publication ID
              data:
                type: object  # Replace with actual data type if known
                description: The publication data in JSON format
      404:
        description: No publications found matching the search term
      500:
        description: Internal server error
    """
    try:
        # Search for publications containing the specified title
        data = Publications.query.filter(Publications.document_title.ilike(f"%{title}%")).all()
        if len(data) == 0:
            return jsonify({'message': 'No matching records found'}), 404
        # Prepare the response data
        data_list = [{'id': item.id, 'data': item.form_data} for item in data]
        return jsonify(data_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
      

@publications_bp.route('/get-publications', methods=['GET'])
def get_all_publications():
    """
    Fetches all publications with pagination and optional filtering by resource type.
    ---
    tags:
      - Publications
    parameters:
      - in: query
        name: page
        type: integer
        description: Page number to retrieve (default is 1)
      - in: query
        name: page_size
        type: integer
        description: Number of publications per page (default is 10)
      - in: query
        name: resource_type_id
        type: integer
        description: Filter publications by associated resource type ID
      - in: query
        name: sort
        type: string
        description: Sorting criteria (e.g., "published" or "title"). Default is "published".
      - in: query
        name: order
        type: string
        description: Sorting order ("asc" for ascending, "desc" for descending). Default is "desc".
    responses:
      200:
        description: List of publications (with optional filters, pagination, and sorting)
        schema:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  description:
                    type: string
                  resource_type_id:
                    type: integer
                  user_id:
                    type: integer
                  published:
                    type: string
            pagination:
              type: object
              properties:
                total:
                  type: integer
                page:
                  type: integer
                page_size:
                  type: integer
                total_pages:
                  type: integer
      400:
        description: Bad request
      500:
        description: Internal server error
    """
    try:
        # Default pagination parameters
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        if page <= 0 or page_size <= 0:
            return jsonify({'message': 'page and page_size must be positive integers'}), 400

        # Optional filter by resource_type_id
        resource_type_id = request.args.get('resource_type_id')

        # Sorting parameters
        sort_field = request.args.get('sort', 'published')  # Default sort field is 'published'
        order = request.args.get('order', 'desc')  # Default sort order is descending

        # Validate sort order
        if order not in ['asc', 'desc']:
            return jsonify({'message': 'Invalid order parameter (must be "asc" or "desc")'}), 400

        # Validate and set sort field
        valid_sort_fields = ['published', 'title', 'id']
        if sort_field not in valid_sort_fields:
            return jsonify({'message': f'Invalid sort field (must be one of {valid_sort_fields})'}), 400

        # Build the query using the Publications model
        query = Publications.query

        if resource_type_id:
            try:
                resource_type_id = int(resource_type_id)
                query = query.filter_by(resource_type_id=resource_type_id)
            except ValueError:
                return jsonify({'message': 'Invalid resource_type_id (must be an integer)'}), 400

        # Apply sorting
        sort_column = getattr(Publications, sort_field)
        if order == 'desc':
            sort_column = desc(sort_column)

        # Apply sorting and pagination
        offset = (page - 1) * page_size
        publications = (
            query.order_by(sort_column)
            .limit(page_size)
            .offset(offset)
            .all()
        )

        # Prepare the response data
        data_list = [
            {
                'id': pub.id,
                'title': pub.document_title,
                'description': pub.document_description,
                'resource_type_id': pub.resource_type_id,
                'user_id': pub.user_id,
                'publication_poster_url': pub.publication_poster_url,
                'docid': pub.document_docid,
                'doi': pub.doi,
                'owner': pub.owner,
                'avatar': pub.avatar,
                'published_isoformat': pub.published.isoformat() if pub.published else None,
                'published': int(pub.published.timestamp()) if pub.published else None  # Converted to Unix timestamp
            }
            for pub in publications
        ]

        # Pagination metadata
        total_publications = query.count()
        pagination = {
            'total': total_publications,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_publications + page_size - 1) // page_size
        }

        return jsonify({
            'data': data_list,
            'pagination': pagination
        }), 200

    except ValueError:
        return jsonify({'message': 'Invalid pagination parameters (must be integers)'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@publications_bp.route('/get-publication/<int:publication_id>', methods=['GET'])
def get_publication(publication_id):
    """
    Fetches a specific publication by its ID along with related tables.
    Can be optionally filtered by user_id.

    ---
    tags:
      - Publications
    parameters:
      - in: path
        name: publication_id
        type: integer
        required: true
        description: The unique identifier of the publication to retrieve.
      - in: query
        name: user_id
        type: integer
        required: false
        description: Filter publication by user ID. If provided, will check if the publication belongs to this user.
      - in: query
        name: type
        type: string
        required: false
        description: The format of the response, either "json" or "xml". Default is "json".
    responses:
      200:
        description: Publication details
      404:
        description: Publication not found
      403:
        description: Forbidden - publication doesn't belong to the specified user
      500:
        description: Internal server error
    """
    try:
        logger.info(f"get_publication called with publication_id={publication_id}")
        
        # Get user_id filter if provided
        user_id_str = request.args.get('user_id')
        user_id = None
        
        if user_id_str is not None:
            try:
                user_id = int(user_id_str)
                logger.info(f"User ID filter provided: {user_id}")
            except ValueError:
                logger.warning(f"Invalid user_id format: {user_id_str}")
                return jsonify({'message': 'Invalid user_id format (must be an integer)'}), 400

        # First check if the publication exists
        publication = Publications.query.filter_by(id=publication_id).first()
        if not publication:
            logger.warning(f"Publication not found with ID: {publication_id}")
            return jsonify({'message': 'Publication not found'}), 404
            
        # Apply user_id filter if provided
        if user_id is not None:
            if publication.user_id != user_id:
                logger.warning(f"Access denied: Publication {publication_id} does not belong to user {user_id}")
                return jsonify({'message': 'Access denied: Publication does not belong to the specified user'}), 403
            else:
                logger.info(f"User {user_id} has access to publication {publication_id}")
        else:
            logger.info(f"No user_id filter provided, showing publication {publication_id} to anyone")
            
        # Now fetch the publication with all its related data
        data = Publications.query \
            .options(
                db.joinedload(Publications.publications_files),
                db.joinedload(Publications.publication_documents),
                db.joinedload(Publications.publication_creators),
                db.joinedload(Publications.publication_organizations),
                db.joinedload(Publications.publication_funders),
                db.joinedload(Publications.publication_projects)
            ) \
            .filter_by(id=publication_id) \
            .first()
            
        # If data is None at this point, something went wrong
        if data is None:
            logger.error(f"Publication data with ID {publication_id} couldn't be loaded with relations")
            return jsonify({'message': 'Error loading publication data'}), 500

        # Create a dictionary for the main publication data
        publication_dict = {}
        desired_fields = ['id', 'document_title', 'document_description', 'document_docid',
                          'resource_type_id', 'user_id', 'avatar', 'owner', 'publication_poster_url', 'doi', 'published', 'handle_url']

        # Log publication details
        logger.info(f"Fetching publication details for ID: {publication_id}, User ID: {getattr(data, 'user_id', 'unknown')}")
        
        for field in desired_fields:
            if hasattr(data, field):
                # Special handling for datetime fields
                if field == 'published' and getattr(data, field):
                    publication_dict[field] = int(getattr(data, field).timestamp())
                else:
                    publication_dict[field] = getattr(data, field)

        # Add related data
        publication_dict['publications_files'] = [
            {
                'id': file.id,
                'title': file.title,
                'description': file.description,
                'publication_type_id': file.publication_type_id,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_url': file.file_url,
                'identifier': file.identifier,
                'generated_identifier': file.generated_identifier
            } for file in data.publications_files
        ]

        publication_dict['publication_documents'] = [
            {
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'publication_type': doc.publication_type_id,
                'file_url': doc.file_url,
                'identifier': doc.identifier_type_id,
                'generated_identifier': doc.generated_identifier
            } for doc in data.publication_documents
        ]

        publication_dict['publication_creators'] = [
            {
                'id': creator.id,
                'family_name': creator.family_name,
                'given_name': creator.given_name,
                'identifier': creator.identifier,
                'role': creator.role_id
            } for creator in data.publication_creators
        ]

        publication_dict['publication_organizations'] = [
            {
                'id': org.id,
                'name': org.name,
                'type': org.type,
                'other_name': org.other_name,
                'country': org.country
            } for org in data.publication_organizations
        ]

        publication_dict['publication_funders'] = [
            {
                'id': funder.id,
                'name': funder.name,
                'type': funder.type,
                'funder_type': funder.funder_type_id,
                'other_name': funder.other_name,
                'country': funder.country
            } for funder in data.publication_funders
        ]

        publication_dict['publication_projects'] = [
            {
                'id': project.id,
                'title': project.title,
                'raid_id': project.raid_id,
                'description': project.description
            } for project in data.publication_projects
        ]

        # Determine response format
        response_type = request.args.get('type', 'json').lower()

        if response_type == 'xml':
            # Convert the dictionary to XML
            root = ET.Element("publication")
            for key, value in publication_dict.items():
                if isinstance(value, list):
                    list_root = ET.SubElement(root, key)
                    for item in value:
                        item_root = ET.SubElement(list_root, "item")
                        for k, v in item.items():
                            ET.SubElement(item_root, k).text = str(v)
                else:
                    ET.SubElement(root, key).text = str(value)

            xml_response = ET.tostring(root, encoding='utf-8')
            return Response(xml_response, content_type='application/xml')

        # Default to JSON response
        return jsonify(publication_dict), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@publications_bp.route('/docid', methods=['GET'])
def get_publication_by_docid_prefix():
    """
    Fetches a specific publication by its document DocID along with related tables.

    ---
    tags:
      - Publications
    parameters:
      - in: query
        name: docid
        type: string
        required: true
        description: The unique DocID of the publication to retrieve.
      - in: query
        name: type
        type: string
        required: false
        description: The format of the response, either "json" or "xml". Default is "json".
    responses:
      200:
        description: Publication details
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        # Get docid from query parameter
        document_docid = request.args.get('docid')

        if not document_docid:
            return jsonify({'error': 'docid parameter is required'}), 400

        # Retrieve the publication data with all related tables using joinedload
        data = Publications.query \
            .options(
                db.joinedload(Publications.publications_files),
                db.joinedload(Publications.publication_documents),
                db.joinedload(Publications.publication_creators),
                db.joinedload(Publications.publication_organizations),
                db.joinedload(Publications.publication_funders),
                db.joinedload(Publications.publication_projects)
            ) \
            .filter_by(document_docid=document_docid) \
            .first()

        if not data:
            return jsonify({'message': 'No matching records found'}), 404

        # Create a dictionary for the main publication data
        publication_dict = {}
        desired_fields = ['id', 'document_title', 'document_description', 'document_docid',
                          'resource_type_id', 'user_id', 'avatar', 'owner', 'publication_poster_url', 'doi', 'published', 'handle_url']

        # Update main publication data with Unix timestamp for `published`
        for field in desired_fields:
            if hasattr(data, field):
                if field == 'published' and getattr(data, field):
                    publication_dict[field] = int(getattr(data, field).timestamp())
                else:
                    publication_dict[field] = getattr(data, field)

        # Add related data
        publication_dict['publications_files'] = [
            {
                'id': file.id,
                'title': file.title,
                'description': file.description,
                'publication_type_id': file.publication_type_id,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_url': file.file_url,
                'identifier': file.identifier,
                'generated_identifier': file.generated_identifier
            } for file in data.publications_files
        ]

        publication_dict['publication_documents'] = [
            {
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'publication_type': doc.publication_type_id,
                'file_url': doc.file_url,
                'identifier': doc.identifier_type_id,
                'generated_identifier': doc.generated_identifier
            } for doc in data.publication_documents
        ]

        publication_dict['publication_creators'] = [
            {
                'id': creator.id,
                'family_name': creator.family_name,
                'given_name': creator.given_name,
                'identifier': creator.identifier,
                'role': creator.role_id
            } for creator in data.publication_creators
        ]

        publication_dict['publication_organizations'] = [
            {
                'id': org.id,
                'name': org.name,
                'type': org.type,
                'other_name': org.other_name,
                'country': org.country
            } for org in data.publication_organizations
        ]

        publication_dict['publication_funders'] = [
            {
                'id': funder.id,
                'name': funder.name,
                'type': funder.type,
                'funder_type': funder.funder_type_id,
                'other_name': funder.other_name,
                'country': funder.country
            } for funder in data.publication_funders
        ]

        publication_dict['publication_projects'] = [
            {
                'id': project.id,
                'title': project.title,
                'raid_id': project.raid_id,
                'description': project.description
            } for project in data.publication_projects
        ]

        # Determine response format
        response_type = request.args.get('type', 'json').lower()

        if response_type == 'xml':
            # Convert the dictionary to XML
            root = ET.Element("publication")
            for key, value in publication_dict.items():
                if isinstance(value, list):
                    list_root = ET.SubElement(root, key)
                    for item in value:
                        item_root = ET.SubElement(list_root, "item")
                        for k, v in item.items():
                            ET.SubElement(item_root, k).text = str(v)
                else:
                    ET.SubElement(root, key).text = str(value)

            xml_response = ET.tostring(root, encoding='utf-8')
            return Response(xml_response, content_type='application/xml')

        # Default to JSON response
        return jsonify(publication_dict), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@publications_bp.route('/<path:document_docid>', methods=['GET'])
def get_publication_by_docid_simple(document_docid):
    """
    Fetches a specific publication by its document DocID at the root level.
    Similar to get_publication_by_docid but accessible at example.com/{docid}
    
    This endpoint provides the same functionality as /docid/{docid} but with a cleaner URL structure.

    ---
    tags:
      - Publications
    parameters:
      - in: path
        name: document_docid
        type: string
        required: true
        description: The unique DocID of the publication to retrieve.
      - in: query
        name: type
        type: string
        required: false
        description: The format of the response, either "json" or "xml". Default is "json".
    responses:
      200:
        description: Publication details
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        # Validate DocID format to avoid conflicts with other routes
        # A typical DocID might look like: 20.500.14351/834ce32a04333cd91d4b
        docid_pattern = r'^\d+(\.\d+)+\/.+$'
        if not re.match(docid_pattern, document_docid):
            # If it doesn't match DocID pattern, return 404 to let other routes handle it
            abort(404)
            
        logger.info(f"get_publication_by_docid_simple called with document_docid={document_docid}")
        
        # Retrieve the publication data with all related tables using joinedload
        data = Publications.query \
            .options(
                db.joinedload(Publications.publications_files),
                db.joinedload(Publications.publication_documents),
                db.joinedload(Publications.publication_creators),
                db.joinedload(Publications.publication_organizations),
                db.joinedload(Publications.publication_funders),
                db.joinedload(Publications.publication_projects)
            ) \
            .filter_by(document_docid=document_docid) \
            .first()

        if not data:
            logger.warning(f"No publication found with DocID: {document_docid}")
            return jsonify({'message': 'No matching records found'}), 404

        # Create a dictionary for the main publication data
        publication_dict = {}
        desired_fields = ['id', 'document_title', 'document_description', 'document_docid',
                          'resource_type_id', 'user_id', 'avatar', 'owner', 'publication_poster_url', 'doi', 'published', 'handle_url']

        # Update main publication data with Unix timestamp for `published`
        for field in desired_fields:
            if hasattr(data, field):
                if field == 'published' and getattr(data, field):
                    publication_dict[field] = int(getattr(data, field).timestamp())
                else:
                    publication_dict[field] = getattr(data, field)

        # Add related data
        publication_dict['publications_files'] = [
            {
                'id': file.id,
                'title': file.title,
                'description': file.description,
                'publication_type_id': file.publication_type_id,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_url': file.file_url,
                'identifier': file.identifier,
                'generated_identifier': file.generated_identifier
            } for file in data.publications_files
        ]

        publication_dict['publication_documents'] = [
            {
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'publication_type': doc.publication_type_id,
                'file_url': doc.file_url,
                'identifier': doc.identifier_type_id,
                'generated_identifier': doc.generated_identifier
            } for doc in data.publication_documents
        ]

        publication_dict['publication_creators'] = [
            {
                'id': creator.id,
                'family_name': creator.family_name,
                'given_name': creator.given_name,
                'identifier': creator.identifier,
                'role': creator.role_id
            } for creator in data.publication_creators
        ]

        publication_dict['publication_organizations'] = [
            {
                'id': org.id,
                'name': org.name,
                'type': org.type,
                'other_name': org.other_name,
                'country': org.country
            } for org in data.publication_organizations
        ]

        publication_dict['publication_funders'] = [
            {
                'id': funder.id,
                'name': funder.name,
                'type': funder.type,
                'funder_type': funder.funder_type_id,
                'other_name': funder.other_name,
                'country': funder.country
            } for funder in data.publication_funders
        ]

        publication_dict['publication_projects'] = [
            {
                'id': project.id,
                'title': project.title,
                'raid_id': project.raid_id,
                'description': project.description
            } for project in data.publication_projects
        ]

        # Determine response format
        response_type = request.args.get('type', 'json').lower()

        if response_type == 'xml':
            # Convert the dictionary to XML
            root = ET.Element("publication")
            for key, value in publication_dict.items():
                if isinstance(value, list):
                    list_root = ET.SubElement(root, key)
                    for item in value:
                        item_root = ET.SubElement(list_root, "item")
                        for k, v in item.items():
                            ET.SubElement(item_root, k).text = str(v)
                else:
                    ET.SubElement(root, key).text = str(value)

            xml_response = ET.tostring(root, encoding='utf-8')
            return Response(xml_response, content_type='application/xml')

        # Default to JSON response
        logger.info(f"Successfully retrieved publication for DocID: {document_docid}")
        return jsonify(publication_dict), 200

    except Exception as e:
        logger.error(f"Error retrieving publication by DocID {document_docid}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@publications_bp.route('/publish', methods=['POST'])
# @jwt_required()
def create_publication():
    """
    Create a new  Publication

    This endpoint allows users to create a new  publication, including associated files, documents, creators, organizations, funders, and projects.

    ---
    tags:
      -  Publications
    consumes:
      - multipart/form-data
    parameters:
      - name: documentDocid
        in: formData
        type: string
        required: true
        description: The document's unique identifier.
      - name: documentTitle
        in: formData
        type: string
        required: true
        description: The title of the document.
      - name: documentDescription
        in: formData
        type: string
        required: true
        description: A brief description of the document.
      - name: resourceType
        in: formData
        type: string
        required: true
        description: The type of the resource being published.
      - name: user_id
        in: formData
        type: integer
        required: true
        description: The ID of the user creating the publication.
      - name: owner
        in: formData
        type: string
        required: true
        description: The owner of the publication.
      - name: doi
        in: formData
        type: string
        required: true
        description: The DOI of the publication.
      - name: publicationPoster
        in: formData
        type: file
        required: false
        description: The poster image for the publication.
      - name: avatar
        in: formData
        type: string
        required: false
        description: URL to the avatar image of the owner.
    responses:
      200:
        description:  Publication created successfully.
        schema:
          type: object
          properties:
            message:
              type: string
              description: Success message.
            publication_id:
              type: integer
              description: ID of the created publication.
      400:
        description: Bad Request. Required fields are missing or contain invalid data.
        schema:
          type: object
          properties:
            message:
              type: string
              description: Error message.
      500:
        description: Internal Server Error.
        schema:
          type: object
          properties:
            error:
              type: string
              description: Error message.
    """
    try:
        # Log the start of the request
        logger.info(f"=== START: Create Publication Request at {datetime.now()} ===")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Create a complete data dump for logging
        logger.info("=" * 80)
        logger.info("COMPLETE REQUEST DATA DUMP:")
        logger.info("=" * 80)
        
        # Log all form data with INFO level for better visibility
        logger.info("FORM DATA RECEIVED:")
        logger.info("-" * 40)
        for key, value in request.form.items():
            # Truncate very long values for readability
            display_value = value[:500] + "..." if len(value) > 500 else value
            logger.info(f"  {key}: {display_value}")
        logger.info(f"Total form fields: {len(request.form)}")
        
        # Log all files with INFO level
        logger.info("-" * 40)
        logger.info("FILES RECEIVED:")
        logger.info("-" * 40)
        for key, file in request.files.items():
            logger.info(f"  {key}:")
            logger.info(f"    - Filename: {file.filename}")
            logger.info(f"    - Content Type: {file.content_type}")
            logger.info(f"    - Content Length: {file.content_length if hasattr(file, 'content_length') else 'N/A'}")
        logger.info(f"Total files: {len(request.files)}")
        
        # Log request size information
        logger.info("-" * 40)
        logger.info("REQUEST SIZE INFORMATION:")
        logger.info(f"  Content-Length header: {request.headers.get('Content-Length', 'Not specified')}")
        logger.info(f"  Content-Type: {request.headers.get('Content-Type', 'Not specified')}")
        
        # Log parsed JSON data if available
        if request.is_json:
            logger.info("-" * 40)
            logger.info("JSON DATA RECEIVED:")
            logger.info(f"  {request.get_json()}")
        
        logger.info("=" * 80)
        
        # Access form data from request.form and files from request.files
        document_docid = request.form.get('documentDocid')
        document_title = request.form.get('documentTitle')
        document_description = request.form.get('documentDescription')
        resource_type = request.form.get('resourceType')
        user_id = request.form.get('user_id')
        doi = clean_undefined_string(request.form.get('doi'))
        owner = request.form.get('owner')
        publication_poster = request.files.get('publicationPoster')
        avatar = clean_undefined_string(request.form.get('avatar'))  # Assuming it's a URL

        # Log main publication data
        logger.info("Main publication data:")
        logger.info(f"  documentDocid: {document_docid}")
        logger.info(f"  documentTitle: {document_title}")
        logger.info(f"  documentDescription: {document_description[:100]}..." if document_description and len(document_description) > 100 else f"  documentDescription: {document_description}")
        logger.info(f"  resourceType: {resource_type}")
        logger.info(f"  user_id: {user_id}")
        logger.info(f"  doi: {doi}")
        logger.info(f"  owner: {owner}")
        logger.info(f"  publicationPoster: {publication_poster.filename if publication_poster else 'None'}")
        logger.info(f"  avatar: {avatar}")

         # Validate required fields
        missing_fields = []

        if not document_docid:
            missing_fields.append('documentDocid')
        if not document_title:
            missing_fields.append('documentTitle')
        if not document_description:
            missing_fields.append('documentDescription')
        if not resource_type:
            missing_fields.append('resourceType')
        if not user_id:
            missing_fields.append('user_id')
        if not owner:
            missing_fields.append('owner')

        if missing_fields:
            logger.warning(f"Missing required fields: {', '.join(missing_fields)}")
            return jsonify({'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400
 
        # Try to convert the resource_type to an integer
        try:
            resource_type = int(resource_type)
        except ValueError:
            logger.error(f"Invalid resource type '{resource_type}' - not an integer")
            return jsonify({"message": f"Invalid resource type '{resource_type}'."}), 400

        # Now validate the resource type by querying the database
        resource_type_obj = ResourceTypes.query.filter_by(id=resource_type).first()
        if not resource_type_obj:
            logger.error(f"Resource type '{resource_type}' validation failed")
            return jsonify({"message": f"Invalid resource type '{resource_type}'."}), 400

        resource_type_id = resource_type_obj.id
        logger.info(f"Resource type validated: ID={resource_type_id}")

        
        # Try to convert the resource_type to an integer
        try:
            user_id = int(user_id)
        except ValueError:
            logger.error(f"Invalid user id type '{user_id}' - not an integer")
            return jsonify({"message": f"Invalid user id type '{user_id}'."}), 400

        # Validate user
        user = UserAccount.query.filter_by(user_id=user_id).first()
        if not user:
            logger.error(f"User '{user_id}' validation failed")
            return jsonify({"message": f"Invalid user '{user_id}'."}), 400
        
        logger.info(f"User validated: ID={user_id}")

        # Handle file uploads if they exist
        publication_poster_url = None
        if publication_poster:
            poster_filename = publication_poster.filename
            publication_poster.save(f'uploads/{poster_filename}')
            # Always use production domain for consistency
            base_url = 'https://docid.africapidalliance.org'
            publication_poster_url = f'{base_url}/uploads/{poster_filename}'
            logger.info(f"Publication poster saved: {publication_poster_url}")

        # Create the publication record
        publication = Publications(
            user_id=user_id,
            # document_docid=document_docid_live,
            document_docid=document_docid,
            document_title=document_title,
            document_description=document_description,
            owner=owner,
            doi=doi,
            resource_type_id=resource_type_id,
            avatar=avatar,
            publication_poster_url=publication_poster_url
        )
        db.session.add(publication)

        # Flush to get the newly created ID
        db.session.flush()
        publication_id = publication.id
        logger.info(f"Publication created with ID: {publication_id}")
        
        # Schedule CORDRA push to run after 1 minute
        try:
            from app.tasks import push_to_cordra_async
            # Schedule the task to run after 60 seconds
            push_to_cordra_async.apply_async(args=[publication_id], countdown=60)
            logger.info(f"Scheduled CORDRA push for publication {publication_id} to run in 60 seconds")
        except ImportError:
            logger.warning("Celery not configured. CORDRA push will need to be run manually via push_to_cordra.py script")

        # Save PublicationFiles records
        logger.info("Processing PublicationFiles...")
        files_publications = []
        index = 0
        while True:
            file_title = request.form.get(f'filesPublications[{index}][title]')
            if file_title is None:
                break

            file_description = clean_undefined_string(request.form.get(f'filesPublications[{index}][description]'))
            publication_type = request.form.get(f'filesPublications[{index}][publication_type]')
            file_type = request.form.get(f'filesPublications[{index}][file_type]')
            identifier = request.form.get(f'filesPublications[{index}][identifier]')
            generated_identifier = request.form.get(f'filesPublications[{index}][generated_identifier]')
            file = request.files.get(f'filesPublications_{index}_file')

            logger.info(f"PublicationFile [{index}]:")
            logger.info(f"  title: {file_title}")
            logger.info(f"  description: {file_description}")
            logger.info(f"  publication_type: {publication_type}")
            logger.info(f"  file_type: {file_type}")
            logger.info(f"  identifier: {identifier}")
            logger.info(f"  generated_identifier: {generated_identifier}")
            logger.info(f"  file: {file.filename if file else 'None'}")

            try:
                publication_type = int(publication_type) if publication_type else None
            except ValueError:
                logger.error(f"Invalid publication_type at index {index}: {publication_type}")
                return jsonify({'message': f'Invalid input for publication_type at index {index}. Expected an integer.'}), 400

            # Validate publication type
            if publication_type is None:
                logger.error(f"Publication type is required at index {index}")
                return jsonify({'message': f'Publication type is required at index {index}.'}), 400
                
            publication_type_obj = PublicationTypes.query.filter_by(id=publication_type).first()
            if not publication_type_obj:
                logger.error(f"Invalid publication type '{publication_type}' at index {index}")
                return jsonify({'message': f'Invalid publication type \'{publication_type}\' at index {index}.'}), 400
              
            publication_type_id = publication_type_obj.id
              
            file_url = None
            file_filename = None
            handle_id = None
            external_id = None
            external_id_type = None
            
            if file:
                file_filename = file.filename
                file.save(f'uploads/{file_filename}')
                # Always use production domain for consistency
                base_url = 'https://docid.africapidalliance.org'
                file_url = f'{base_url}/uploads/{file_filename}'
                logger.info(f"File saved: {file_url}")

                # Process the identifier
                handle_id, external_id, external_id_type = IdentifierService.process_identifier(generated_identifier)
                
                # Only create PublicationFiles record if there's an actual file uploaded
                files_publications.append(PublicationFiles(
                    publication_id=publication_id,
                    title=file_title,
                    description=file_description,
                    publication_type_id=publication_type_id,
                    file_name=file_filename,
                    file_type=file_type,
                    file_url=file_url,
                    identifier=identifier, # type: ignore
                    generated_identifier=generated_identifier,
                    handle_identifier=handle_id,
                    external_identifier=external_id,
                    external_identifier_type=external_id_type
                ))
                
                # CORDRA push has been moved to separate script push_to_cordra.py
                if handle_id:
                    logger.info(f"PublicationFile [{index}] has handle: {handle_id}. CORDRA push will be handled by push_to_cordra.py script")
                else:
                    logger.warning(f"No Handle available for PublicationFile [{index}]")
            else:
                logger.warning(f"PublicationFile [{index}] has no file uploaded - skipping file record creation")
            
            index += 1
        
        if files_publications:
            db.session.bulk_save_objects(files_publications)
            logger.info(f"Saved {len(files_publications)} PublicationFiles")

        # Save PublicationDocuments records
        logger.info("Processing PublicationDocuments...")
        files_documents = []
        index = 0
        while True:
          file_title = request.form.get(f'filesDocuments[{index}][title]')
          if file_title is None:
              break
          
          file_description = clean_undefined_string(request.form.get(f'filesDocuments[{index}][description]'))
          publication_type = request.form.get(f'filesDocuments[{index}][publication_type]')
          identifier_type_id = request.form.get(f'filesDocuments[{index}][identifier]')
          generated_identifier = request.form.get(f'filesDocuments[{index}][generated_identifier]')
          file = request.files.get(f'filesDocuments_{index}_file')
          
          logger.info(f"PublicationDocument [{index}]:")
          logger.info(f"  title: {file_title}")
          logger.info(f"  description: {file_description}")
          logger.info(f"  publication_type: {publication_type}")
          logger.info(f"  identifier_type_id: {identifier_type_id}")
          logger.info(f"  generated_identifier: {generated_identifier}")
          logger.info(f"  file: {file.filename if file else 'None'}")
          
          try:
              publication_type = int(publication_type) if publication_type else None
          except ValueError:
              logger.error(f"Invalid publication_type at index {index}: {publication_type}")
              return jsonify({'message': f'Invalid input for Publication Documents publication_type at index {index}. Expected an integer.'}), 400
          
          # Validate publication type
          if publication_type is None:
              logger.error(f"Publication type is required at index {index}")
              return jsonify({'message': f'Publication type is required at index {index}.'}), 400
                
          publication_type_obj = PublicationTypes.query.filter_by(id=publication_type).first()
          if not publication_type_obj:
              logger.error(f"Invalid publication type '{publication_type}' at index {index}")
              return jsonify({'message': f'Invalid publication type \'{publication_type}\' at index {index}.'}), 400
          
          publication_type_id = publication_type_obj.id
          
          # Handle identifier_type_id - make it optional
          validated_identifier_type_id = None
          if identifier_type_id:  # Only process if identifier_type_id is provided
              try:
                  identifier_type_id = int(identifier_type_id)
              except ValueError:
                  logger.error(f"Invalid identifier_type_id at index {index}: {identifier_type_id}")
                  return jsonify({'message': f'Invalid input for identifier_type_id at index {index}. Expected an integer.'}), 400
              
              # Validate identifier type
              identifier_type = PublicationIdentifierTypes.query.filter_by(id=identifier_type_id).first()
              if not identifier_type:
                  logger.error(f"Invalid identifier type ID {identifier_type_id} at index {index}")
                  return jsonify({'message': f'Invalid identifier type ID {identifier_type_id} at index {index}.'}), 400
              
              # If identifier_type_id is provided, generated_identifier is required
              if not generated_identifier or generated_identifier.strip() == '':
                  logger.error(f"Missing generated_identifier when identifier_type_id is provided at index {index}")
                  return jsonify({'message': f'generated_identifier is required when identifier_type_id is provided at index {index}.'}), 400
              
              validated_identifier_type_id = identifier_type_id
          else:
              # If no identifier_type_id, set generated_identifier to None
              generated_identifier = None
          
          file_url = None
          handle_id = None
          external_id = None
          external_id_type = None
          
          if file:
              file_filename = file.filename
              file.save(f'uploads/{file_filename}')
              # Always use production domain for consistency
              base_url = 'https://docid.africapidalliance.org'
              file_url = f'{base_url}/uploads/{file_filename}'
              logger.info(f"File saved: {file_url}")

              # Process the identifier only if we have generated_identifier and a file
              if generated_identifier:
                  handle_id, external_id, external_id_type = IdentifierService.process_identifier(generated_identifier)
              
              # Only create PublicationDocuments record if there's an actual file uploaded
              files_documents.append(PublicationDocuments(
                  publication_id=publication_id,
                  title=file_title,
                  description=file_description,
                  publication_type_id=publication_type_id,
                  file_url=file_url,
                  identifier_type_id=validated_identifier_type_id,  # Use validated value
                  generated_identifier=generated_identifier,
                  handle_identifier=handle_id,
                  external_identifier=external_id,
                  external_identifier_type=external_id_type
              ))
              
              # CORDRA push has been moved to separate script push_to_cordra.py
              if handle_id:
                  logger.info(f"PublicationDocument [{index}] has handle: {handle_id}. CORDRA push will be handled by push_to_cordra.py script")
              else:
                  logger.warning(f"No Handle available for PublicationDocument [{index}]")
          else:
              logger.warning(f"PublicationDocument [{index}] has no file uploaded - skipping document record creation")
          
          index += 1

        if files_documents:
            db.session.bulk_save_objects(files_documents)
            logger.info(f"Saved {len(files_documents)} PublicationDocuments")

        # Save PublicationCreators records
        logger.info("Processing PublicationCreators...")
        creators = []
        index = 0
        while True:
            family_name = request.form.get(f'creators[{index}][family_name]')
            if family_name is None:
                break

            given_name = request.form.get(f'creators[{index}][given_name]')
            identifier_type = request.form.get(f'creators[{index}][identifier]')  # This contains 'orcid', 'isni', etc.
            role_id = request.form.get(f'creators[{index}][role]')
            
            # Get the actual identifier value based on the type
            identifier_value = None
            if identifier_type:
                # Try to get the specific identifier value (e.g., creators[0][orcid] or creators[0][orcid_id])
                identifier_value = request.form.get(f'creators[{index}][{identifier_type}]')
                if not identifier_value:
                    # Try with _id suffix (e.g., creators[0][orcid_id])
                    identifier_value = request.form.get(f'creators[{index}][{identifier_type}_id]')
            
            # Format identifier as resolvable URL
            resolvable_identifier = None
            if identifier_type and identifier_value:
                if identifier_type.lower() == 'orcid':
                    # Format ORCID as resolvable URL - check if already formatted
                    if identifier_value.startswith('https://orcid.org/'):
                        resolvable_identifier = identifier_value
                    elif identifier_value.startswith('orcid.org/'):
                        resolvable_identifier = f"https://{identifier_value}"
                    else:
                        # Just the ORCID ID part, add the full URL
                        resolvable_identifier = f"https://orcid.org/{identifier_value}"
                elif identifier_type.lower() == 'isni':
                    # Format ISNI as resolvable URL
                    if identifier_value.startswith('https://isni.org/'):
                        resolvable_identifier = identifier_value
                    else:
                        resolvable_identifier = f"https://isni.org/isni/{identifier_value}"
                elif identifier_type.lower() == 'viaf':
                    # Format VIAF as resolvable URL
                    if identifier_value.startswith('https://viaf.org/'):
                        resolvable_identifier = identifier_value
                    else:
                        resolvable_identifier = f"https://viaf.org/viaf/{identifier_value}"
                else:
                    # For unknown types, store the raw value
                    resolvable_identifier = identifier_value
            
            logger.info(f"PublicationCreator [{index}]:")
            logger.info(f"  family_name: {family_name}")
            logger.info(f"  given_name: {given_name}")
            logger.info(f"  identifier_type: {identifier_type}")
            logger.info(f"  identifier_value: {identifier_value}")
            logger.info(f"  resolvable_identifier: {resolvable_identifier}")
            logger.info(f"  role_id: {role_id}")
            
            # Debug logging for identifier lookup
            if identifier_type:
                debug_value1 = request.form.get(f'creators[{index}][{identifier_type}]')
                debug_value2 = request.form.get(f'creators[{index}][{identifier_type}_id]')
                logger.info(f"  DEBUG - Looking for creators[{index}][{identifier_type}]: {debug_value1}")
                logger.info(f"  DEBUG - Looking for creators[{index}][{identifier_type}_id]: {debug_value2}")
         
            # try:
            #     role_id = int(role_id) if role_id else None
            # except ValueError:
            #     return jsonify({'message': f'Invalid input for Publication Creators role_id at index {index}. Expected an integer.'}), 400

            # Validate role
            creators_role = CreatorsRoles.validate_creators_role(role_id)
            if not creators_role:
                logger.error(f"Invalid creators role '{role_id}' at index {index}")
                raise ValueError(f"Invalid creators role '{role_id}'.")
            
            role_id  = creators_role.role_id
              
            creators.append(PublicationCreators(
                publication_id=publication_id,
                family_name=family_name,
                given_name=given_name,
                identifier=resolvable_identifier,  # Store the full resolvable URL
                identifier_type=identifier_type,   # Store the type (e.g., 'orcid')
                role_id=role_id
            ))
            index += 1
        
        if creators:
            db.session.bulk_save_objects(creators)
            logger.info(f"Saved {len(creators)} PublicationCreators")

        # Save PublicationOrganization records
        logger.info("Processing PublicationOrganizations...")
        organizations = []
        index = 0
        while True:
            name = request.form.get(f'organization[{index}][name]')
            if name is None:
                break

            org_type = request.form.get(f'organization[{index}][type]')
            other_name = clean_undefined_string(request.form.get(f'organization[{index}][other_name]'))
            country = request.form.get(f'organization[{index}][country]')
            
            # Get identifier fields (e.g., ROR ID for organizations)
            identifier_type = request.form.get(f'organization[{index}][identifier_type]')  # e.g., 'ror'
            identifier_value = request.form.get(f'organization[{index}][identifier]')  # e.g., '02nr0ka47'
            
            # If no explicit identifier_type but we have a ROR field, handle it
            if not identifier_type and not identifier_value:
                # Check for specific identifier fields like organization[0][ror] or organization[0][ror_id]
                ror_id = request.form.get(f'organization[{index}][ror]')
                if not ror_id:
                    ror_id = request.form.get(f'organization[{index}][ror_id]')
                if ror_id:
                    identifier_type = 'ror'
                    identifier_value = ror_id
                else:
                    # Also check for GRID ID with both formats
                    grid_id = request.form.get(f'organization[{index}][grid]')
                    if not grid_id:
                        grid_id = request.form.get(f'organization[{index}][grid_id]')
                    if grid_id:
                        identifier_type = 'grid'
                        identifier_value = grid_id
            
            # Format identifier as resolvable URL
            resolvable_identifier = None
            if identifier_type and identifier_value:
                if identifier_type.lower() == 'ror':
                    # Format ROR as resolvable URL
                    if identifier_value.startswith('https://ror.org/'):
                        resolvable_identifier = identifier_value
                    elif identifier_value.startswith('ror.org/'):
                        resolvable_identifier = f"https://{identifier_value}"
                    else:
                        # Just the ID part, add the full URL
                        resolvable_identifier = f"https://ror.org/{identifier_value}"
                elif identifier_type.lower() == 'grid':
                    # Format GRID as resolvable URL
                    if not identifier_value.startswith('http'):
                        resolvable_identifier = f"https://www.grid.ac/institutes/{identifier_value}"
                    else:
                        resolvable_identifier = identifier_value
                elif identifier_type.lower() == 'isni':
                    # Format ISNI as resolvable URL
                    resolvable_identifier = f"https://isni.org/isni/{identifier_value}"
                else:
                    # For unknown types, store the raw value
                    resolvable_identifier = identifier_value
            
            logger.info(f"PublicationOrganization [{index}]:")
            logger.info(f"  name: {name}")
            logger.info(f"  type: {org_type}")
            logger.info(f"  other_name: {other_name}")
            logger.info(f"  country: {country}")
            logger.info(f"  identifier_type: {identifier_type}")
            logger.info(f"  identifier_value: {identifier_value}")
            logger.info(f"  resolvable_identifier: {resolvable_identifier}")
            
            # Debug logging for identifier lookup
            debug_ror1 = request.form.get(f'organization[{index}][ror]')
            debug_ror2 = request.form.get(f'organization[{index}][ror_id]')
            debug_grid1 = request.form.get(f'organization[{index}][grid]')
            debug_grid2 = request.form.get(f'organization[{index}][grid_id]')
            logger.info(f"  DEBUG - Looking for organization[{index}][ror]: {debug_ror1}")
            logger.info(f"  DEBUG - Looking for organization[{index}][ror_id]: {debug_ror2}")
            logger.info(f"  DEBUG - Looking for organization[{index}][grid]: {debug_grid1}")
            logger.info(f"  DEBUG - Looking for organization[{index}][grid_id]: {debug_grid2}")

            organizations.append(PublicationOrganization(
                publication_id=publication_id,
                name=name,
                type=org_type,
                other_name=other_name,
                country=country,
                identifier=resolvable_identifier,  # Store the full resolvable URL
                identifier_type=identifier_type    # Store the type (e.g., 'ror', 'grid', 'isni')
            ))
            index += 1
        
        if organizations:
            db.session.bulk_save_objects(organizations)
            logger.info(f"Saved {len(organizations)} PublicationOrganizations")

        # Save PublicationFunders records
        logger.info("Processing PublicationFunders...")
        funders = []
        index = 0
        while True:
            name = request.form.get(f'funders[{index}][name]')
            if name is None:
                break

            other_name = clean_undefined_string(request.form.get(f'funders[{index}][other_name]'))            
            funder_type = request.form.get(f'funders[{index}][type]')
            funder_category = request.form.get(f'funders[{index}][type]')
            country = request.form.get(f'funders[{index}][country]')
            
            # Get identifier fields (e.g., ROR ID)
            identifier_type = request.form.get(f'funders[{index}][identifier_type]')  # e.g., 'ror'
            identifier_value = request.form.get(f'funders[{index}][identifier]')  # e.g., '01ej9dk98'
            
            # If no explicit identifier_type but we have a ROR field, handle it
            if not identifier_type and not identifier_value:
                # Check for specific identifier fields like funders[0][ror] or funders[0][ror_id]
                ror_id = request.form.get(f'funders[{index}][ror]')
                if not ror_id:
                    ror_id = request.form.get(f'funders[{index}][ror_id]')
                if ror_id:
                    identifier_type = 'ror'
                    identifier_value = ror_id
            
            # Format identifier as resolvable URL
            resolvable_identifier = None
            if identifier_type and identifier_value:
                if identifier_type.lower() == 'ror':
                    # Format ROR as resolvable URL
                    # ROR IDs can come with or without the URL prefix
                    if identifier_value.startswith('https://ror.org/'):
                        resolvable_identifier = identifier_value
                    elif identifier_value.startswith('ror.org/'):
                        resolvable_identifier = f"https://{identifier_value}"
                    else:
                        # Just the ID part, add the full URL
                        resolvable_identifier = f"https://ror.org/{identifier_value}"
                elif identifier_type.lower() == 'fundref':
                    # Format FundRef (Crossref Funder ID) as resolvable URL
                    if not identifier_value.startswith('http'):
                        resolvable_identifier = f"https://doi.org/10.13039/{identifier_value}"
                    else:
                        resolvable_identifier = identifier_value
                elif identifier_type.lower() == 'isni':
                    # Format ISNI as resolvable URL
                    resolvable_identifier = f"https://isni.org/isni/{identifier_value}"
                else:
                    # For unknown types, store the raw value
                    resolvable_identifier = identifier_value
            
            logger.info(f"PublicationFunder [{index}]:")
            logger.info(f"  name: {name}")
            logger.info(f"  other_name: {other_name}")
            logger.info(f"  funder_type: {funder_type}")
            logger.info(f"  funder_category: {funder_category}")
            logger.info(f"  country: {country}")
            logger.info(f"  identifier_type: {identifier_type}")
            logger.info(f"  identifier_value: {identifier_value}")
            logger.info(f"  resolvable_identifier: {resolvable_identifier}")
            
            # Debug logging for identifier lookup
            debug_ror1 = request.form.get(f'funders[{index}][ror]')
            debug_ror2 = request.form.get(f'funders[{index}][ror_id]')
            logger.info(f"  DEBUG - Looking for funders[{index}][ror]: {debug_ror1}")
            logger.info(f"  DEBUG - Looking for funders[{index}][ror_id]: {debug_ror2}")
            
            # check funder_type_id
            
            
            try:
                funder_type = int(funder_type) if funder_type else None
            except ValueError:
                logger.error(f"Invalid funder_type at index {index}: {funder_type}")
                return jsonify({'message': f'Invalid input for Publication Funders  funder_type at index {index}. Expected an integer.'}), 400

            # Validate funder type
            if funder_type is None:
                logger.error(f"Funder type is required at index {index}")
                return jsonify({'message': f'Funder type is required at index {index}.'}), 400
                
            funder_type_obj = FunderTypes.query.filter_by(id=funder_type).first()
            if not funder_type_obj:
                logger.error(f"Invalid Funders type '{funder_type}' at index {index}")
                return jsonify({'message': f'Invalid Funders type \'{funder_type}\' at index {index}.'}), 400
            
            funder_type_id = funder_type_obj.id

            funders.append(PublicationFunders(
                publication_id=publication_id,
                name=name,
                type=funder_category,
                funder_type_id=funder_type_id,
                other_name=other_name,
                country=country,
                identifier=resolvable_identifier,  # Store the full resolvable URL
                identifier_type=identifier_type    # Store the type (e.g., 'ror')
            ))
            index += 1
        
        if funders:
            db.session.bulk_save_objects(funders)
            logger.info(f"Saved {len(funders)} PublicationFunders")

        # Save PublicationProjects records
        logger.info("Processing PublicationProjects...")
        projects = []
        index = 0
        while True:
            title = request.form.get(f'projects[{index}][title]')
            if title is None:
                break

            raid_id = request.form.get(f'projects[{index}][raid_id]')
            description = clean_undefined_string(request.form.get(f'projects[{index}][description]'))
            # For NOT NULL columns, use empty string instead of None
            if description is None:
                description = ""
            
            # Format RAID as identifier
            resolvable_identifier = None
            identifier_type = None
            if raid_id:
                identifier_type = 'raid'
                # RAID is already a URL, just ensure it's properly formatted
                if raid_id.startswith('http://') or raid_id.startswith('https://'):
                    resolvable_identifier = raid_id
                elif raid_id.startswith('10.'):  # Handle format like 10.80368/b1adfb3a
                    resolvable_identifier = f"https://app.demo.raid.org.au/raids/{raid_id}"
                else:
                    # Assume it's just the ID part
                    resolvable_identifier = f"https://app.demo.raid.org.au/raids/{raid_id}"
            
            logger.info(f"PublicationProject [{index}]:")
            logger.info(f"  title: {title}")
            logger.info(f"  raid_id: {raid_id}")
            logger.info(f"  description: {description}")
            logger.info(f"  identifier_type: {identifier_type}")
            logger.info(f"  identifier: {resolvable_identifier}")

            projects.append(PublicationProjects(
                publication_id=publication_id,
                title=title,
                raid_id=raid_id,  # Keep for backward compatibility
                description=description,
                identifier=resolvable_identifier,  # Store the full resolvable URL
                identifier_type=identifier_type    # Store as 'raid'
            ))
            index += 1
        
        if projects:
            db.session.bulk_save_objects(projects)
            logger.info(f"Saved {len(projects)} PublicationProjects")

        # Commit all changes
        db.session.commit()
        
        logger.info(f"=== SUCCESS: Publication created successfully with ID: {publication_id} ===")

        # Prepare full publication data to return
        publication_data = {
            'id': publication.id,
            'document_title': publication.document_title,
            'document_description': publication.document_description,
            'document_docid': publication.document_docid,
            'resource_type_id': publication.resource_type_id,
            'user_id': publication.user_id,
            'owner': publication.owner,
            'doi': publication.doi,
            'avatar': publication.avatar,
            'publication_poster_url': publication.publication_poster_url,
            'published': int(publication.published.timestamp()) if publication.published else None
        }
        
        return jsonify({
            "message": "Publication created successfully", 
            "publication_id": publication_id,
            "publication": publication_data
        }), 200

    except Exception as e:
        logger.error(f"=== ERROR: Failed to create publication ===")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Stack trace:", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


# ===== DRAFT MANAGEMENT ENDPOINTS =====

@publications_bp.route('/draft', methods=['POST'])
def save_draft():
    """
    Save draft form data for assign-docid form
    ---
    tags:
      - Publications
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            email:
              type: string
              description: User email
            formData:
              type: object
              description: Complete form state
    responses:
      200:
        description: Draft saved successfully
      400:
        description: Missing required data
      500:
        description: Internal server error
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        email = data.get('email')
        form_data = data.get('formData')
        
        if not email or not form_data:
            return jsonify({'error': 'Email and formData are required'}), 400
        
        logger.info(f"Saving draft for user: {email}")
        
        # Save draft data
        draft = PublicationDrafts.save_draft(email, form_data)
        
        return jsonify({
            'message': 'Draft saved successfully',
            'timestamp': draft.updated_at.isoformat(),
            'saved': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error saving draft: {str(e)}")
        return jsonify({'error': 'Failed to save draft'}), 500


@publications_bp.route('/draft/<email>', methods=['GET'])
def get_draft_data(email):
    """
    Get saved draft data for user
    ---
    tags:
      - Publications  
    parameters:
      - name: email
        in: path
        type: string
        required: true
        description: User email
    responses:
      200:
        description: Draft data retrieved successfully
      404:
        description: No draft data found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Retrieving draft data for user: {email}")
        
        draft = PublicationDrafts.get_draft(email)
        
        if not draft:
            return jsonify({'message': 'No draft found', 'hasDraft': False}), 200
        
        return jsonify({
            'hasDraft': True,
            'formData': draft.form_data,
            'lastSaved': draft.updated_at.isoformat(),
            'message': 'Draft retrieved successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving draft: {str(e)}")
        return jsonify({'error': 'Failed to retrieve draft'}), 500


@publications_bp.route('/draft/<email>', methods=['DELETE'])
def delete_draft_data(email):
    """
    Delete draft data after successful submission
    ---
    tags:
      - Publications
    parameters:
      - name: email
        in: path
        type: string
        required: true
        description: User email
    responses:
      200:
        description: Draft deleted successfully
      404:
        description: No draft found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Deleting draft for user: {email}")
        
        deleted = PublicationDrafts.delete_draft(email)
        
        if deleted:
            return jsonify({'message': 'Draft deleted successfully'}), 200
        else:
            return jsonify({'message': 'No draft found to delete'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting draft: {str(e)}")
        return jsonify({'error': 'Failed to delete draft'}), 500


@publications_bp.route('/drafts/stats', methods=['GET'])
def get_draft_stats():
    """
    Get draft statistics for admin dashboard (optional)
    ---
    tags:
      - Publications
    responses:
      200:
        description: Draft statistics
      500:
        description: Internal server error
    """
    try:
        total_drafts = PublicationDrafts.get_user_drafts_count()

        return jsonify({
            'totalDrafts': total_drafts,
            'message': 'Draft statistics retrieved successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving draft stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve draft statistics'}), 500


@publications_bp.route('/draft/by-user/<int:user_id>', methods=['GET'])
def get_draft_by_user_id(user_id):
    """
    Get saved draft data for user by user_id
    ---
    tags:
      - Publications
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: User ID
    responses:
      200:
        description: Draft data retrieved successfully
      404:
        description: User not found or no draft data found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Retrieving draft data for user_id: {user_id}")

        # First, get the user's email from user_id
        user = UserAccount.query.get(user_id)
        if not user:
            return jsonify({
                'error': 'User not found',
                'hasDraft': False
            }), 404

        # Then get the draft using email
        draft = PublicationDrafts.get_draft(user.email)

        if not draft:
            return jsonify({
                'message': 'No draft found',
                'hasDraft': False,
                'user_email': user.email
            }), 200

        return jsonify({
            'hasDraft': True,
            'formData': draft.form_data,
            'lastSaved': draft.updated_at.isoformat(),
            'user_email': user.email,
            'message': 'Draft retrieved successfully'
        }), 200

    except Exception as e:
        logger.error(f"Error retrieving draft by user_id: {str(e)}")
        return jsonify({'error': 'Failed to retrieve draft'}), 500


@publications_bp.route('/update-publication/<int:publication_id>', methods=['PUT'])
def update_publication(publication_id):
    """
    Update an existing publication
    
    This endpoint allows users to update their own publications, including associated files, documents, 
    creators, organizations, funders, and projects. Changes are logged in the audit trail.
    
    ---
    tags:
      - Publications
    consumes:
      - multipart/form-data
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the publication to update.
      - name: user_id
        in: formData
        type: integer
        required: true
        description: The ID of the user updating the publication (must own the publication).
      - name: documentTitle
        in: formData
        type: string
        required: false
        description: The updated title of the document.
      - name: documentDescription
        in: formData
        type: string
        required: false
        description: The updated description of the document.
      - name: resourceType
        in: formData
        type: string
        required: false
        description: The updated type of the resource.
      - name: doi
        in: formData
        type: string
        required: false
        description: The updated DOI of the publication.
      - name: publicationPoster
        in: formData
        type: file
        required: false
        description: The updated poster image for the publication.
      - name: avatar
        in: formData
        type: string
        required: false
        description: Updated URL to the avatar image of the owner.
    responses:
      200:
        description: Publication updated successfully.
        schema:
          type: object
          properties:
            message:
              type: string
              description: Success message.
            publication_id:
              type: integer
              description: ID of the updated publication.
      400:
        description: Bad Request. Invalid data or missing required fields.
      403:
        description: Forbidden. User doesn't own this publication.
      404:
        description: Publication not found.
      500:
        description: Internal Server Error.
    """
    try:
        logger.info(f"=== START: Update Publication Request for ID {publication_id} at {datetime.now()} ===")
        
        # Get user_id from form data
        user_id_str = request.form.get('user_id')
        if not user_id_str:
            logger.warning("Missing user_id in update request")
            return jsonify({'message': 'User ID is required'}), 400
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            logger.warning(f"Invalid user_id format: {user_id_str}")
            return jsonify({'message': 'Invalid user_id format (must be an integer)'}), 400
        
        # Check if publication exists and user owns it
        publication = Publications.query.filter_by(id=publication_id).first()
        if not publication:
            logger.warning(f"Publication not found with ID: {publication_id}")
            return jsonify({'message': 'Publication not found'}), 404
            
        if publication.user_id != user_id:
            logger.warning(f"Access denied: User {user_id} doesn't own publication {publication_id}")
            return jsonify({'message': 'Access denied: You can only edit your own publications'}), 403
        
        # Check publication status (workflow state validation)
        # Note: Add status field check when available in Publications model
        # For now, assume all publications can be edited
        
        # Get client information for audit trail
        ip_address = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Track changes for audit trail
        changes_made = []
        
        # Log request data for debugging
        logger.info("Update request form data:")
        for key, value in request.form.items():
            display_value = value[:100] + "..." if len(value) > 100 else value
            logger.info(f"  {key}: {display_value}")
        
        # Update title if provided
        new_title = request.form.get('documentTitle')
        if new_title and new_title != publication.document_title:
            old_value = publication.document_title
            publication.document_title = new_title
            changes_made.append({
                'field': 'document_title',
                'old_value': old_value,
                'new_value': new_title
            })
            logger.info(f"Title updated from '{old_value}' to '{new_title}'")
        
        # Update description if provided  
        new_description = request.form.get('documentDescription')
        if new_description and new_description != publication.document_description:
            old_value = publication.document_description
            publication.document_description = new_description
            changes_made.append({
                'field': 'document_description',
                'old_value': old_value,
                'new_value': new_description
            })
            logger.info(f"Description updated")
        
        # Update resource type if provided
        new_resource_type = request.form.get('resourceType')
        if new_resource_type:
            try:
                resource_type_id = int(new_resource_type)
                # Validate resource type exists
                resource_type_obj = ResourceTypes.query.filter_by(id=resource_type_id).first()
                if not resource_type_obj:
                    return jsonify({'message': f'Invalid resource type ID: {resource_type_id}'}), 400
                
                if resource_type_id != publication.resource_type_id:
                    old_value = publication.resource_type_id
                    publication.resource_type_id = resource_type_id
                    changes_made.append({
                        'field': 'resource_type_id',
                        'old_value': str(old_value),
                        'new_value': str(resource_type_id)
                    })
                    logger.info(f"Resource type updated from {old_value} to {resource_type_id}")
            except ValueError:
                return jsonify({'message': f'Invalid resource type format: {new_resource_type}'}), 400
        
        # Update DOI if provided
        new_doi = clean_undefined_string(request.form.get('doi'))
        if new_doi and new_doi != publication.doi:
            old_value = publication.doi
            publication.doi = new_doi
            changes_made.append({
                'field': 'doi',
                'old_value': old_value,
                'new_value': new_doi
            })
            logger.info(f"DOI updated from '{old_value}' to '{new_doi}'")
        
        # Update avatar if provided
        new_avatar = clean_undefined_string(request.form.get('avatar'))
        if new_avatar and new_avatar != publication.avatar:
            old_value = publication.avatar
            publication.avatar = new_avatar
            changes_made.append({
                'field': 'avatar',
                'old_value': old_value,
                'new_value': new_avatar
            })
            logger.info(f"Avatar updated")
        
        # Handle file uploads (publication poster)
        publication_poster = request.files.get('publicationPoster')
        if publication_poster and publication_poster.filename:
            # TODO: Implement file upload logic similar to create_publication
            # This would involve saving the file and updating publication_poster_url
            logger.info(f"New publication poster uploaded: {publication_poster.filename}")
            # For now, log the change without implementing full file upload
            changes_made.append({
                'field': 'publication_poster_url',
                'old_value': publication.publication_poster_url,
                'new_value': f'New file: {publication_poster.filename}'
            })
        
        # Update the updated_at and updated_by fields
        publication.updated_at = datetime.utcnow()
        publication.updated_by = user_id
        
        # Save changes to database
        if changes_made:
            try:
                db.session.commit()
                logger.info(f"Publication {publication_id} updated successfully with {len(changes_made)} changes")
                
                # Log each change in audit trail
                for change in changes_made:
                    PublicationAuditTrail.log_change(
                        publication_id=publication_id,
                        user_id=user_id,
                        action='UPDATE',
                        field_name=change['field'],
                        old_value=change['old_value'],
                        new_value=change['new_value'],
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                    logger.info(f"Audit trail logged for field: {change['field']}")
                
                return jsonify({
                    'message': 'Publication updated successfully',
                    'publication_id': publication_id,
                    'changes_count': len(changes_made)
                }), 200
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Database error during update: {str(e)}")
                return jsonify({'error': 'Failed to save changes to database'}), 500
        else:
            logger.info(f"No changes detected for publication {publication_id}")
            return jsonify({
                'message': 'No changes detected',
                'publication_id': publication_id,
                'changes_count': 0
            }), 200
            
    except Exception as e:
        logger.error(f"Error updating publication {publication_id}: {str(e)}")
        return jsonify({'error': 'Internal server error during publication update'}), 500


# Helper endpoint to get publication for editing (with user ownership validation)
@publications_bp.route('/get-publication-for-edit/<int:publication_id>', methods=['GET'])
def get_publication_for_edit(publication_id):
    """
    Get publication data specifically for editing purposes
    
    This endpoint returns publication data with user ownership validation and includes
    all related data needed for the edit form.
    
    ---
    tags:
      - Publications
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the publication.
      - name: user_id
        in: query
        type: integer
        required: true
        description: The user ID requesting edit access (must own the publication).
    responses:
      200:
        description: Publication data for editing
      400:
        description: Missing or invalid user_id
      403:
        description: Access denied - user doesn't own the publication
      404:
        description: Publication not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Get publication for edit: ID={publication_id}")
        
        # Get and validate user_id
        user_id_str = request.args.get('user_id')
        if not user_id_str:
            return jsonify({'message': 'User ID parameter is required'}), 400
        
        try:
            user_id = int(user_id_str)
        except ValueError:
            return jsonify({'message': 'Invalid user_id format (must be an integer)'}), 400
        
        # Check if publication exists
        publication = Publications.query.filter_by(id=publication_id).first()
        if not publication:
            logger.warning(f"Publication not found with ID: {publication_id}")
            return jsonify({'message': 'Publication not found'}), 404
        
        # Check user ownership
        if publication.user_id != user_id:
            logger.warning(f"Edit access denied: Publication {publication_id} does not belong to user {user_id}")
            return jsonify({'message': 'Access denied: You can only edit your own publications'}), 403
        
        # Check publication status (workflow state validation)
        # TODO: Implement status checking when status field is available
        # For now, assume all publications can be edited
        
        # Use existing get_publication endpoint logic but with ownership already validated
        # Fetch publication with all related data
        data = Publications.query \
            .options(
                db.joinedload(Publications.publications_files),
                db.joinedload(Publications.publication_documents),
                db.joinedload(Publications.publication_creators),
                db.joinedload(Publications.publication_organizations),
                db.joinedload(Publications.publication_funders),
                db.joinedload(Publications.publication_projects)
            ) \
            .filter_by(id=publication_id) \
            .first()
        
        if data is None:
            logger.error(f"Publication data with ID {publication_id} couldn't be loaded with relations")
            return jsonify({'message': 'Error loading publication data'}), 500
        
        # Build response data (similar to get_publication but optimized for editing)
        publication_dict = {}
        desired_fields = ['id', 'document_title', 'document_description', 'document_docid',
                          'resource_type_id', 'user_id', 'avatar', 'owner', 'publication_poster_url', 
                          'doi', 'published', 'updated_at', 'updated_by']
        
        for field in desired_fields:
            if hasattr(data, field):
                value = getattr(data, field)
                if field in ['published', 'updated_at'] and value:
                    publication_dict[field] = int(value.timestamp())
                else:
                    publication_dict[field] = value
        
        # Add related data
        publication_dict['publications_files'] = [
            {
                'id': file.id,
                'title': file.title,
                'description': file.description,
                'publication_type_id': file.publication_type_id,
                'file_name': file.file_name,
                'file_type': file.file_type,
                'file_url': file.file_url,
                'identifier': file.identifier,
                'generated_identifier': file.generated_identifier,
                'handle_identifier': getattr(file, 'handle_identifier', None),
                'external_identifier': getattr(file, 'external_identifier', None),
                'external_identifier_type': getattr(file, 'external_identifier_type', None)
            } for file in data.publications_files
        ]
        
        publication_dict['publication_documents'] = [
            {
                'id': doc.id,
                'title': doc.title,
                'description': doc.description,
                'publication_type': doc.publication_type_id,
                'file_url': doc.file_url,
                'identifier': doc.identifier_type_id,
                'generated_identifier': doc.generated_identifier,
                'handle_identifier': getattr(doc, 'handle_identifier', None),
                'external_identifier': getattr(doc, 'external_identifier', None),
                'external_identifier_type': getattr(doc, 'external_identifier_type', None)
            } for doc in data.publication_documents
        ]
        
        publication_dict['publication_creators'] = [
            {
                'id': creator.id,
                'family_name': creator.family_name,
                'given_name': creator.given_name,
                'identifier': creator.identifier,
                'role': creator.role_id,
                'identifier_type': getattr(creator, 'identifier_type', None)
            } for creator in data.publication_creators
        ]
        
        publication_dict['publication_organizations'] = [
            {
                'id': org.id,
                'name': org.name,
                'type': org.type,
                'other_name': org.other_name,
                'country': org.country,
                'identifier': getattr(org, 'identifier', None),
                'identifier_type': getattr(org, 'identifier_type', None)
            } for org in data.publication_organizations
        ]
        
        publication_dict['publication_funders'] = [
            {
                'id': funder.id,
                'funder_name': funder.funder_name,
                'funder_type_id': funder.funder_type_id,
                'award_number': funder.award_number,
                'award_title': funder.award_title,
                'award_uri': funder.award_uri,
                'identifier': getattr(funder, 'identifier', None),
                'identifier_type': getattr(funder, 'identifier_type', None)
            } for funder in data.publication_funders
        ]
        
        publication_dict['publication_projects'] = [
            {
                'id': project.id,
                'project_name': project.project_name,
                'project_description': project.project_description,
                'project_acronym': project.project_acronym,
                'identifier': getattr(project, 'identifier', None),
                'identifier_type': getattr(project, 'identifier_type', None)
            } for project in data.publication_projects
        ]
        
        logger.info(f"Publication data for edit retrieved successfully: ID={publication_id}, User={user_id}")
        return jsonify(publication_dict), 200

    except Exception as e:
        logger.error(f"Error retrieving publication for edit {publication_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@publications_bp.route('/<int:publication_id>', methods=['DELETE'])
@jwt_required()
def delete_publication(publication_id):
    """
    Delete a publication by ID (requires authentication)
    ---
    tags:
      - Publications
    security:
      - Bearer: []
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: The ID of the publication to delete
    responses:
      200:
        description: Publication deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: Publication deleted successfully
      401:
        description: Unauthorized - Authentication required
      403:
        description: Forbidden - Cannot delete published documents or user not authorized
        schema:
          type: object
          properties:
            error:
              type: string
              example: Cannot delete published documents. Please contact support.
      404:
        description: Publication not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: Publication not found
      500:
        description: Internal server error
    """
    try:
        from flask_jwt_extended import get_jwt_identity

        # Get the current user from JWT token
        current_user_id = get_jwt_identity()
        logger.info(f"User {current_user_id} attempting to delete publication with ID: {publication_id}")

        # Find the publication
        publication = Publications.query.get(publication_id)

        if not publication:
            logger.warning(f"Publication not found: ID={publication_id}")
            return jsonify({'error': 'Publication not found'}), 404

        # Check if the current user owns this publication
        if publication.user_id != current_user_id:
            logger.warning(f"User {current_user_id} attempted to delete publication {publication_id} owned by user {publication.user_id}")
            return jsonify({
                'error': 'You do not have permission to delete this publication'
            }), 403

        # Check if publication is published (has a DOCiD assigned)
        if publication.document_docid:
            logger.warning(f"Attempt to delete published publication: ID={publication_id}, DOCiD={publication.document_docid}")
            return jsonify({
                'error': 'Cannot delete published documents at this time. Please contact support if you need to remove this publication.'
            }), 403

        # Store info for logging before deletion
        publication_title = publication.document_title
        user_id = publication.user_id

        # Delete related records first (cascading delete)
        try:
            # Delete publication creators
            PublicationCreators.query.filter_by(publication_id=publication_id).delete()

            # Delete publication organizations
            PublicationOrganization.query.filter_by(publication_id=publication_id).delete()

            # Delete publication funders
            PublicationFunders.query.filter_by(publication_id=publication_id).delete()

            # Delete publication projects
            PublicationProjects.query.filter_by(publication_id=publication_id).delete()

            # Delete publication files
            PublicationFiles.query.filter_by(publication_id=publication_id).delete()

            # Delete publication documents
            PublicationDocuments.query.filter_by(publication_id=publication_id).delete()

            # Delete audit trail entries
            PublicationAuditTrail.query.filter_by(publication_id=publication_id).delete()

            # Finally delete the publication itself
            db.session.delete(publication)
            db.session.commit()

            logger.info(f"Publication deleted successfully: ID={publication_id}, Title='{publication_title}', User={user_id}")

            return jsonify({
                'message': 'Publication deleted successfully',
                'publication_id': publication_id
            }), 200

        except Exception as delete_error:
            db.session.rollback()
            logger.error(f"Error during cascade deletion for publication {publication_id}: {str(delete_error)}")
            raise delete_error

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting publication {publication_id}: {str(e)}")
        return jsonify({'error': 'Failed to delete publication'}), 500

 