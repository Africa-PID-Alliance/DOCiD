"""
OJS (Open Journal Systems) Integration API Endpoints
Read-only operations for retrieving journal submissions, issues, and articles
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, ResourceTypes, PublicationCreators, CreatorsRoles
from app.service_ojs import OJSClient, OJSMetadataMapper
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create Blueprint
ojs_bp = Blueprint('ojs', __name__, url_prefix='/api/v1/ojs')

# OJS configuration from environment
OJS_BASE_URL = os.getenv('OJS_BASE_URL', 'https://your-ojs-instance.com/api/v1')
OJS_API_KEY = os.getenv('OJS_API_KEY', '')


def get_ojs_client() -> OJSClient:
    """
    Create OJS client instance

    Returns:
        Configured OJSClient instance
    """
    return OJSClient(OJS_BASE_URL, OJS_API_KEY if OJS_API_KEY else None)


@ojs_bp.route('/config', methods=['GET'])
@cross_origin()
def get_config():
    """
    Get OJS integration configuration status
    ---
    tags:
      - OJS Integration
    responses:
      200:
        description: Configuration status retrieved successfully
        schema:
          type: object
          properties:
            ojs_url:
              type: string
              description: OJS API base URL
              example: https://your-journal.org/api/v1
            configured:
              type: boolean
              description: Whether API key is configured
              example: true
            status:
              type: string
              description: Connection status
              example: connected
            message:
              type: string
              description: Additional status message
    """
    try:
        client = get_ojs_client()
        connection_status = client.test_connection()

        return jsonify({
            'ojs_url': OJS_BASE_URL,
            'configured': bool(OJS_API_KEY),
            'status': connection_status.get('status', 'unknown'),
            'message': connection_status.get('message', connection_status.get('error', ''))
        }), 200

    except Exception as e:
        logger.error(f"Error getting OJS config: {str(e)}")
        return jsonify({'error': 'Failed to get configuration'}), 500


@ojs_bp.route('/submissions', methods=['GET'])
@jwt_required()
@cross_origin()
def get_submissions():
    """
    Get list of submissions from OJS (requires API key)
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: integer
        required: false
        description: |
          Filter by submission status:
          1=queued, 3=scheduled, 4=published, 5=declined
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number (1-indexed)
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Number of results per page (max 100)
      - name: q
        in: query
        type: string
        required: false
        description: Search in title and authors
    responses:
      200:
        description: Submissions retrieved successfully
        schema:
          type: object
          properties:
            items:
              type: array
              description: List of submissions
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Submission ID
                  title:
                    type: object
                    description: Multilingual title
                  status:
                    type: integer
                    description: Submission status
                  dateSubmitted:
                    type: string
                    description: Submission date
            itemsMax:
              type: integer
              description: Total number of submissions
            page:
              type: integer
              description: Current page number
            per_page:
              type: integer
              description: Results per page
      401:
        description: Unauthorized - JWT token required
      403:
        description: OJS API key not configured
      500:
        description: Internal server error
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        status = request.args.get('status', type=int)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_query = request.args.get('q', '').strip()

        client = get_ojs_client()
        results = client.get_submissions(
            status=status,
            page=page,
            per_page=per_page,
            search_phrase=search_query if search_query else None
        )

        if 'error' in results:
            return jsonify(results), 403

        logger.info(f"Retrieved {len(results.get('items', []))} OJS submissions")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error getting OJS submissions: {str(e)}")
        return jsonify({'error': 'Failed to get submissions'}), 500


@ojs_bp.route('/submissions/<int:submission_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def get_submission(submission_id):
    """
    Get details of a specific OJS submission
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: submission_id
        in: path
        type: integer
        required: true
        description: OJS submission ID
        example: 123
    responses:
      200:
        description: Submission details retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Submission ID
            title:
              type: object
              description: Multilingual title
            abstract:
              type: object
              description: Multilingual abstract
            status:
              type: integer
              description: Submission status
            dateSubmitted:
              type: string
              description: Submission date
            publications:
              type: array
              description: Publication versions
      401:
        description: Unauthorized - JWT token required
      403:
        description: OJS API key not configured
      404:
        description: Submission not found
      500:
        description: Internal server error
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        client = get_ojs_client()
        submission = client.get_submission(submission_id)

        if not submission:
            return jsonify({'error': f'Submission {submission_id} not found'}), 404

        logger.info(f"Retrieved OJS submission {submission_id}")

        return jsonify(submission), 200

    except Exception as e:
        logger.error(f"Error getting OJS submission {submission_id}: {str(e)}")
        return jsonify({'error': 'Failed to get submission'}), 500


@ojs_bp.route('/submissions/search', methods=['GET'])
@jwt_required()
@cross_origin()
def search_submissions():
    """
    Search OJS submissions by title and authors
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query string
        example: machine learning
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number (1-indexed)
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Number of results per page
    responses:
      200:
        description: Search results retrieved successfully
        schema:
          type: object
          properties:
            items:
              type: array
              description: List of matching submissions
            itemsMax:
              type: integer
              description: Total number of matching submissions
            page:
              type: integer
              description: Current page
            per_page:
              type: integer
              description: Results per page
            query:
              type: string
              description: Search query used
      400:
        description: Missing search query
      401:
        description: Unauthorized - JWT token required
      403:
        description: OJS API key not configured
      500:
        description: Internal server error
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query (q) is required'}), 400

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        client = get_ojs_client()
        results = client.search_submissions(query=query, page=page, per_page=per_page)
        results['query'] = query

        logger.info(f"OJS search for '{query}' returned {len(results.get('items', []))} results")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching OJS submissions: {str(e)}")
        return jsonify({'error': 'Failed to search submissions'}), 500


@ojs_bp.route('/issues', methods=['GET'])
@cross_origin()
def get_issues():
    """
    Get list of published journal issues (public endpoint)
    ---
    tags:
      - OJS Integration
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number (1-indexed)
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Number of results per page
      - name: is_published
        in: query
        type: boolean
        default: true
        description: Filter by published status
    responses:
      200:
        description: Issues retrieved successfully
        schema:
          type: object
          properties:
            items:
              type: array
              description: List of issues
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Issue ID
                  volume:
                    type: integer
                    description: Volume number
                  number:
                    type: string
                    description: Issue number
                  year:
                    type: integer
                    description: Publication year
                  title:
                    type: object
                    description: Multilingual title
                  datePublished:
                    type: string
                    description: Publication date
            itemsMax:
              type: integer
              description: Total number of issues
            page:
              type: integer
              description: Current page number
            per_page:
              type: integer
              description: Results per page
      500:
        description: Internal server error
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_published = request.args.get('is_published', 'true').lower() == 'true'

        client = get_ojs_client()
        results = client.get_issues(page=page, per_page=per_page, is_published=is_published)

        logger.info(f"Retrieved {len(results.get('items', []))} OJS issues")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error getting OJS issues: {str(e)}")
        return jsonify({'error': 'Failed to get issues'}), 500


@ojs_bp.route('/issues/<int:issue_id>', methods=['GET'])
@cross_origin()
def get_issue(issue_id):
    """
    Get details of a specific journal issue
    ---
    tags:
      - OJS Integration
    parameters:
      - name: issue_id
        in: path
        type: integer
        required: true
        description: OJS issue ID
        example: 1
    responses:
      200:
        description: Issue details retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Issue ID
            volume:
              type: integer
              description: Volume number
            number:
              type: string
              description: Issue number
            year:
              type: integer
              description: Publication year
            title:
              type: object
              description: Multilingual title
            description:
              type: object
              description: Multilingual description
            datePublished:
              type: string
              description: Publication date
            articles:
              type: array
              description: Articles in this issue
      404:
        description: Issue not found
      500:
        description: Internal server error
    """
    try:
        client = get_ojs_client()
        issue = client.get_issue(issue_id)

        if not issue:
            return jsonify({'error': f'Issue {issue_id} not found'}), 404

        logger.info(f"Retrieved OJS issue {issue_id}")

        return jsonify(issue), 200

    except Exception as e:
        logger.error(f"Error getting OJS issue {issue_id}: {str(e)}")
        return jsonify({'error': 'Failed to get issue'}), 500


@ojs_bp.route('/issues/current', methods=['GET'])
@cross_origin()
def get_current_issue():
    """
    Get the current (most recent published) journal issue
    ---
    tags:
      - OJS Integration
    responses:
      200:
        description: Current issue retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Issue ID
            volume:
              type: integer
              description: Volume number
            number:
              type: string
              description: Issue number
            title:
              type: object
              description: Multilingual title
            datePublished:
              type: string
              description: Publication date
      404:
        description: No current issue found
      500:
        description: Internal server error
    """
    try:
        client = get_ojs_client()
        issue = client.get_current_issue()

        if not issue:
            return jsonify({'error': 'No current issue found'}), 404

        logger.info("Retrieved current OJS issue")

        return jsonify(issue), 200

    except Exception as e:
        logger.error(f"Error getting current OJS issue: {str(e)}")
        return jsonify({'error': 'Failed to get current issue'}), 500


@ojs_bp.route('/preview/<int:submission_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def preview_submission_metadata(submission_id):
    """
    Preview OJS submission metadata mapped to DOCiD format (without importing)
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: submission_id
        in: path
        type: integer
        required: true
        description: OJS submission ID to preview
        example: 123
    responses:
      200:
        description: Metadata preview retrieved successfully
        schema:
          type: object
          properties:
            ojs_id:
              type: integer
              description: OJS submission ID
            raw_metadata:
              type: object
              description: Original OJS metadata
            mapped_data:
              type: object
              description: Metadata mapped to DOCiD format
              properties:
                publication:
                  type: object
                  description: Publication fields
                creators:
                  type: array
                  description: Authors/creators
                keywords:
                  type: array
                  description: Keywords
      401:
        description: Unauthorized - JWT token required
      403:
        description: OJS API key not configured
      404:
        description: Submission not found
      500:
        description: Internal server error
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        current_user_id = get_jwt_identity()

        client = get_ojs_client()
        submission = client.get_submission(submission_id)

        if not submission:
            return jsonify({'error': f'Submission {submission_id} not found in OJS'}), 404

        # Map to DOCiD format
        mapped_data = OJSMetadataMapper.ojs_to_docid(submission, current_user_id)

        logger.info(f"Previewed OJS submission {submission_id} for user {current_user_id}")

        return jsonify({
            'ojs_id': submission_id,
            'raw_metadata': submission,
            'mapped_data': mapped_data
        }), 200

    except Exception as e:
        logger.error(f"Error previewing OJS submission {submission_id}: {str(e)}")
        return jsonify({'error': 'Failed to preview submission metadata'}), 500


# ==================== Sync/Import Endpoints ====================

def save_ojs_creators(publication_id: int, creators_data: list):
    """
    Save creators from OJS submission to publication_creators table

    Args:
        publication_id: Publication ID
        creators_data: List of creator dictionaries from OJSMetadataMapper
    """
    if not creators_data:
        return

    for creator_data in creators_data:
        # Get role_id for the creator role
        role_name = creator_data.get('creator_role', 'Author')
        role = CreatorsRoles.query.filter_by(role_name=role_name).first()

        if not role:
            role = CreatorsRoles.query.filter_by(role_name='Author').first()

        if not role:
            continue

        # Parse full name into family_name and given_name
        full_name = creator_data.get('creator_name', '')
        name_parts = full_name.split(',', 1) if ',' in full_name else full_name.rsplit(' ', 1)

        if len(name_parts) == 2:
            if ',' in full_name:
                family_name = name_parts[0].strip()
                given_name = name_parts[1].strip()
            else:
                given_name = name_parts[0].strip()
                family_name = name_parts[1].strip()
        else:
            family_name = full_name.strip()
            given_name = ''

        # Handle ORCID identifier
        orcid_id = creator_data.get('orcid_id', '') or ''
        identifier_value = f"https://orcid.org/{orcid_id}" if orcid_id else ''
        identifier_type_value = 'orcid' if orcid_id else ''

        creator = PublicationCreators(
            publication_id=publication_id,
            family_name=family_name,
            given_name=given_name,
            identifier=identifier_value,
            identifier_type=identifier_type_value,
            role_id=role.role_id
        )
        db.session.add(creator)


@ojs_bp.route('/sync/submission/<int:submission_id>', methods=['POST'])
@jwt_required()
@cross_origin()
def sync_single_submission(submission_id):
    """
    Import a single OJS submission to DOCiD publications table
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: submission_id
        in: path
        type: integer
        required: true
        description: OJS submission ID to import
        example: 123
    responses:
      201:
        description: Submission imported successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            publication_id:
              type: integer
              description: Created publication ID in DOCiD
            docid:
              type: string
              description: Generated DOCiD identifier
            ojs_id:
              type: integer
              description: Original OJS submission ID
            message:
              type: string
      200:
        description: Submission already imported
      403:
        description: OJS API key not configured
      404:
        description: Submission not found on OJS
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error during import
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        current_user_id = get_jwt_identity()

        # Check if already imported
        existing = Publications.query.filter_by(ojs_submission_id=str(submission_id)).first()
        if existing:
            return jsonify({
                'message': 'Submission already imported',
                'publication_id': existing.id,
                'docid': existing.document_docid,
                'ojs_id': submission_id
            }), 200

        # Get submission from OJS
        client = get_ojs_client()
        submission = client.get_submission(submission_id)

        if not submission:
            return jsonify({'error': f'Submission {submission_id} not found on OJS'}), 404

        # Map metadata
        mapped_data = OJSMetadataMapper.ojs_to_docid(submission, current_user_id)
        pub_data = mapped_data['publication']

        # Get resource type ID (OJS is primarily Text/Articles)
        resource_type = ResourceTypes.query.filter_by(resource_type='Text').first()
        resource_type_id = resource_type.id if resource_type else 1

        # Generate DOCiD using OJS DOI or create one
        ojs_doi = pub_data.get('doi', '')
        document_docid = ojs_doi if ojs_doi else f"ojs:{submission_id}"

        # Create publication
        publication = Publications(
            user_id=current_user_id,
            document_title=pub_data['document_title'],
            document_description=pub_data.get('document_description', ''),
            resource_type_id=resource_type_id,
            doi=ojs_doi,
            document_docid=document_docid,
            ojs_submission_id=str(submission_id),
            ojs_url=pub_data.get('ojs_url', ''),
            owner='OJS Repository',
        )

        db.session.add(publication)
        db.session.flush()  # Get publication ID

        # Save creators
        save_ojs_creators(publication.id, mapped_data.get('creators', []))

        db.session.commit()

        logger.info(f"Imported OJS submission {submission_id} as publication {publication.id}")

        return jsonify({
            'success': True,
            'publication_id': publication.id,
            'docid': publication.document_docid,
            'ojs_id': submission_id,
            'ojs_url': publication.ojs_url,
            'message': 'Submission imported successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing OJS submission {submission_id}: {str(e)}")
        return jsonify({'error': f'Failed to import submission: {str(e)}'}), 500


@ojs_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
@cross_origin()
def sync_batch():
    """
    Batch import OJS submissions to DOCiD publications table
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            submission_ids:
              type: array
              description: Specific submission IDs to import
              items:
                type: integer
              example: [1, 2, 3]
            status:
              type: integer
              description: Filter by status (1=queued, 3=scheduled, 4=published, 5=declined)
              example: 4
            search_phrase:
              type: string
              description: Search phrase to filter submissions
            page:
              type: integer
              default: 1
              description: Page number
            page_size:
              type: integer
              default: 50
              description: Number of submissions to import (max 100)
            skip_existing:
              type: boolean
              default: true
              description: Skip submissions that are already imported
    responses:
      200:
        description: Batch import completed
        schema:
          type: object
          properties:
            total:
              type: integer
              description: Total submissions processed
            created:
              type: integer
              description: Successfully imported count
            skipped:
              type: integer
              description: Skipped count (already exist)
            errors:
              type: integer
              description: Failed count
            items:
              type: array
              description: Detailed results per submission
      401:
        description: Unauthorized - JWT token required
      403:
        description: OJS API key not configured
      500:
        description: Server error during batch import
    """
    try:
        if not OJS_API_KEY:
            return jsonify({
                'error': 'OJS API key not configured',
                'message': 'Contact administrator to configure OJS authentication'
            }), 403

        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        submission_ids = data.get('submission_ids', [])
        status = data.get('status')
        search_phrase = data.get('search_phrase', '').strip()
        page = data.get('page', 1)
        page_size = min(data.get('page_size', 50), 100)
        skip_existing = data.get('skip_existing', True)

        client = get_ojs_client()
        submissions_to_import = []

        # Get submissions either from specific IDs or search
        if submission_ids:
            for sid in submission_ids:
                submission = client.get_submission(sid)
                if submission:
                    submissions_to_import.append(submission)
        else:
            search_results = client.get_submissions(
                status=status,
                page=page,
                per_page=page_size,
                search_phrase=search_phrase if search_phrase else None
            )
            submissions_to_import = search_results.get('items', [])

        results = {
            'total': len(submissions_to_import),
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'items': []
        }

        for submission in submissions_to_import:
            submission_id = submission.get('id')

            try:
                # Check if exists
                if skip_existing:
                    existing = Publications.query.filter_by(ojs_submission_id=str(submission_id)).first()
                    if existing:
                        results['skipped'] += 1
                        results['items'].append({
                            'ojs_id': submission_id,
                            'status': 'skipped',
                            'reason': 'already_exists',
                            'publication_id': existing.id
                        })
                        continue

                # Map and create
                mapped_data = OJSMetadataMapper.ojs_to_docid(submission, current_user_id)
                pub_data = mapped_data['publication']

                # Get resource type ID
                resource_type = ResourceTypes.query.filter_by(resource_type='Text').first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD
                ojs_doi = pub_data.get('doi', '')
                document_docid = ojs_doi if ojs_doi else f"ojs:{submission_id}"

                publication = Publications(
                    user_id=current_user_id,
                    document_title=pub_data['document_title'],
                    document_description=pub_data.get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi=ojs_doi,
                    document_docid=document_docid,
                    ojs_submission_id=str(submission_id),
                    ojs_url=pub_data.get('ojs_url', ''),
                    owner='OJS Repository',
                )

                db.session.add(publication)
                db.session.flush()

                # Save creators
                save_ojs_creators(publication.id, mapped_data.get('creators', []))

                db.session.commit()

                results['created'] += 1
                results['items'].append({
                    'ojs_id': submission_id,
                    'publication_id': publication.id,
                    'docid': publication.document_docid,
                    'title': publication.document_title,
                    'status': 'created'
                })

            except Exception as e:
                db.session.rollback()
                results['errors'] += 1
                results['items'].append({
                    'ojs_id': submission_id,
                    'status': 'error',
                    'reason': str(e)
                })

        logger.info(f"OJS batch import completed: {results['created']} created, {results['skipped']} skipped, {results['errors']} errors")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error in OJS batch import: {str(e)}")
        return jsonify({'error': str(e)}), 500


@ojs_bp.route('/sync/stats', methods=['GET'])
@jwt_required()
@cross_origin()
def get_sync_stats():
    """
    Get OJS sync statistics
    ---
    tags:
      - OJS Integration
    security:
      - Bearer: []
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            total_imported:
              type: integer
              description: Total OJS submissions imported
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error
    """
    try:
        # Count all publications with ojs_submission_id
        total_imported = Publications.query.filter(
            Publications.ojs_submission_id.isnot(None),
            Publications.ojs_submission_id != ''
        ).count()

        return jsonify({
            'total_imported': total_imported,
            'ojs_configured': bool(OJS_API_KEY)
        }), 200

    except Exception as e:
        logger.error(f"Error getting OJS sync stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@ojs_bp.route('/sync/delete/<int:publication_id>', methods=['DELETE'])
@jwt_required()
@cross_origin()
def delete_synced_submission(publication_id):
    """
    Delete an OJS-imported publication
    ---
    tags:
      - OJS Integration
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
        description: Publication deleted successfully
      404:
        description: Publication not found or not an OJS import
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error during deletion
    """
    try:
        publication = Publications.query.get(publication_id)

        if not publication:
            return jsonify({'error': 'Publication not found'}), 404

        if not publication.ojs_submission_id:
            return jsonify({'error': 'Publication is not an OJS import'}), 404

        ojs_id = publication.ojs_submission_id

        # Delete associated creators
        PublicationCreators.query.filter_by(publication_id=publication_id).delete()

        # Delete the publication
        db.session.delete(publication)
        db.session.commit()

        logger.info(f"Deleted OJS publication {publication_id} (OJS ID: {ojs_id})")

        return jsonify({
            'success': True,
            'message': f'Publication {publication_id} deleted successfully',
            'ojs_id': ojs_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting OJS publication {publication_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
