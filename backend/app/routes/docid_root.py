# app/routes/docid_root.py

import re
import logging
import xml.etree.ElementTree as ET
from flask import jsonify, request, Response, abort
from sqlalchemy.orm import joinedload
from app.models import Publications
from app import db

logger = logging.getLogger(__name__)

def setup_docid_root_route(app):
    """
    Set up the root-level DocID route directly on the Flask app
    This allows URLs like: http://127.0.0.1:5001/20.500.14351%2F12345
    """
    
    @app.route('/<path:document_docid>', methods=['GET'])
    def get_publication_by_docid_root(document_docid):
        """
        Fetches a specific publication by its document DocID at the root level.
        This endpoint provides clean URLs like: example.com/20.500.14351/12345
        
        This route has the highest priority and will only process valid DocID patterns.
        If the pattern doesn't match a DocID, it returns 404 to let other routes handle it.

        ---
        tags:
          - Publications
        parameters:
          - in: path
            name: document_docid
            type: string
            required: true
            description: The unique DocID of the publication to retrieve (URL encoded if contains special characters).
          - in: query
            name: type
            type: string
            required: false
            description: The format of the response, either "json" or "xml". Default is "json".
        responses:
          200:
            description: Publication details
          404:
            description: Publication not found or invalid DocID format
          500:
            description: Internal server error
        """
        try:
            # Validate DocID format to avoid conflicts with other routes
            # A typical DocID might look like: 20.500.14351/834ce32a04333cd91d4b
            # We need to be strict here to avoid catching other routes
            docid_pattern = r'^\d+(\.\d+)+\/.+$'
            if not re.match(docid_pattern, document_docid):
                logger.debug(f"DocID pattern validation failed for: {document_docid}")
                # If it doesn't match DocID pattern, return 404 to let other routes handle it
                abort(404)
                
            logger.info(f"get_publication_by_docid_root called with document_docid={document_docid}")
            
            # Query for publication by DocID
            data = Publications.query \
                .options(
                    joinedload(Publications.publications_files),
                    joinedload(Publications.publication_documents),
                    joinedload(Publications.publication_creators),
                    joinedload(Publications.publication_organizations),
                    joinedload(Publications.publication_funders),
                    joinedload(Publications.publication_projects)
                ) \
                .filter_by(document_docid=document_docid) \
                .first()

            if not data:
                logger.warning(f"No publication found with DocID: {document_docid}")
                return jsonify({'message': 'No matching records found'}), 404

            # Create a dictionary for the main publication data
            publication_dict = {}
            desired_fields = ['id', 'document_title', 'document_description', 'document_docid',
                              'resource_type_id', 'user_id', 'avatar', 'owner', 'publication_poster_url', 'doi', 'published']

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
