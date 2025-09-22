# app/routes/doi.py

import re
import logging
from logging.handlers import RotatingFileHandler
from flask import Blueprint, jsonify, abort, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from sqlalchemy import desc
from sqlalchemy.sql import func
from xml.etree import ElementTree as ET
from flasgger import swag_from

# App-specific imports
from app import db
from app.models import (
    DocIdLookup,
    Publications,
    PublicationFiles,
    PublicationDocuments,
    PublicationCreators,
    PublicationOrganization,
    PublicationFunders,
    PublicationProjects,
)

doi_bp = Blueprint('doi', __name__, url_prefix='/doi')

@doi_bp.route('/<prefix>/<suffix>', methods=['GET'])
@swag_from({
    "tags": ["DocID"],
    "parameters": [
        {
            "name": "prefix",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The prefix of the DOI (e.g., 20.500.14351)"
        },
        {
            "name": "suffix",
            "in": "path",
            "type": "string",
            "required": True,
            "description": "The suffix of the DOI (e.g., 834ce32a04333cd91d4b)"
        }
    ],
    "responses": {
        200: {
            "description": "Publication details fetched successfully",
            "schema": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "data": {"type": "object"}
                }
            }
        },
        400: {
            "description": "Invalid DOI format"
        },
        404: {
            "description": "No matching records found"
        },
        500: {
            "description": "Internal server error"
        }
    }
})

def handle_doi(prefix, suffix):
    """
    Handle DOI requests in the format /<prefix>/<suffix>.
    Example: /doi/20.500.14351/834ce32a04333cd91d4b
    """
    doi_pattern = r'^\d+(\.\d+)+$'
    if not re.match(doi_pattern, prefix) or not suffix.isalnum():
        abort(400, description="Invalid DOI format")
    
    docid = f"{prefix}/{suffix}"
    
    try:
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
            .filter_by(document_docid=docid) \
            .first()

        if not data:
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

        # Return the selected publication data with related tables
        return jsonify(publication_dict), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@doi_bp.app_errorhandler(400)
def bad_request(error):
    return jsonify({"error": str(error)}), 400

@doi_bp.app_errorhandler(404)
def not_found(error):
    if request.path.startswith('/doi/'):
        return jsonify({"error": "DOI not found"}), 404
    return error  # Allow other Blueprints to handle 404 errors
