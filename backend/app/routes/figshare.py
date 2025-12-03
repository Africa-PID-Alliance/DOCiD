"""
Figshare Integration API Endpoints
Read-only operations for searching and retrieving Figshare articles/datasets
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Publications, ResourceTypes, PublicationCreators, CreatorsRoles
from app.service_figshare import FigshareClient, FigshareMetadataMapper
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
figshare_bp = Blueprint('figshare', __name__, url_prefix='/api/v1/figshare')

# Figshare configuration from environment
FIGSHARE_BASE_URL = os.getenv('FIGSHARE_BASE_URL', 'https://api.figshare.com/v2')
FIGSHARE_API_TOKEN = os.getenv('FIGSHARE_API_TOKEN', '')


def get_figshare_client(use_token: bool = False) -> FigshareClient:
    """
    Create Figshare client instance

    Args:
        use_token: Whether to include API token for authenticated requests

    Returns:
        Configured FigshareClient instance
    """
    token = FIGSHARE_API_TOKEN if use_token and FIGSHARE_API_TOKEN else None
    return FigshareClient(FIGSHARE_BASE_URL, token)


@figshare_bp.route('/config', methods=['GET'])
@cross_origin()
def get_config():
    """
    Get Figshare integration configuration status
    ---
    tags:
      - Figshare Integration
    responses:
      200:
        description: Configuration status retrieved successfully
        schema:
          type: object
          properties:
            figshare_url:
              type: string
              description: Figshare API base URL
              example: https://api.figshare.com/v2
            configured:
              type: boolean
              description: Whether API token is configured
              example: true
            status:
              type: string
              description: Connection status
              example: connected
    """
    try:
        client = get_figshare_client()
        connection_status = client.test_connection()

        return jsonify({
            'figshare_url': FIGSHARE_BASE_URL,
            'configured': bool(FIGSHARE_API_TOKEN),
            'status': connection_status.get('status', 'unknown')
        }), 200

    except Exception as e:
        logger.error(f"Error getting Figshare config: {str(e)}")
        return jsonify({'error': 'Failed to get configuration'}), 500


@figshare_bp.route('/search', methods=['GET'])
@cross_origin()
def search_articles():
    """
    Search for public articles/datasets on Figshare
    ---
    tags:
      - Figshare Integration
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search query string
        example: climate change
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number (1-indexed)
      - name: page_size
        in: query
        type: integer
        default: 10
        description: Number of results per page (max 1000)
      - name: item_type
        in: query
        type: integer
        required: false
        description: |
          Filter by item type:
          1=figure, 2=media, 3=dataset, 4=fileset, 5=poster,
          6=journal contribution, 7=presentation, 8=thesis,
          9=software, 11=online resource, 12=preprint, 13=book,
          14=conference contribution, 15=chapter, 16=peer review,
          17=educational resource
      - name: order
        in: query
        type: string
        default: published_date
        description: Sort field (published_date, modified_date, views, shares, downloads, cites)
      - name: order_direction
        in: query
        type: string
        default: desc
        description: Sort direction (asc, desc)
    responses:
      200:
        description: Search results retrieved successfully
        schema:
          type: object
          properties:
            articles:
              type: array
              description: List of matching articles
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Figshare article ID
                  title:
                    type: string
                    description: Article title
                  doi:
                    type: string
                    description: Article DOI
                  url_public_html:
                    type: string
                    description: Public URL to article
            page:
              type: integer
              description: Current page number
            page_size:
              type: integer
              description: Results per page
            query:
              type: string
              description: Search query used
      400:
        description: Missing search query
      500:
        description: Internal server error
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query (q) is required'}), 400

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)
        item_type = request.args.get('item_type', type=int)
        order = request.args.get('order', 'published_date')
        order_direction = request.args.get('order_direction', 'desc')

        client = get_figshare_client()
        results = client.search_articles(
            query=query,
            page=page,
            page_size=page_size,
            item_type=item_type,
            order=order,
            order_direction=order_direction
        )

        logger.info(f"Figshare search for '{query}' returned {len(results.get('articles', []))} results")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error searching Figshare: {str(e)}")
        return jsonify({'error': 'Failed to search Figshare'}), 500


@figshare_bp.route('/articles/<int:article_id>', methods=['GET'])
@cross_origin()
def get_article(article_id):
    """
    Get details of a public Figshare article by ID
    ---
    tags:
      - Figshare Integration
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: Figshare article ID
        example: 12345678
    responses:
      200:
        description: Article details retrieved successfully
        schema:
          type: object
          properties:
            id:
              type: integer
              description: Figshare article ID
            title:
              type: string
              description: Article title
            description:
              type: string
              description: Article description/abstract
            doi:
              type: string
              description: Article DOI
            url_public_html:
              type: string
              description: Public URL to article
            authors:
              type: array
              description: List of authors
              items:
                type: object
                properties:
                  full_name:
                    type: string
                  orcid_id:
                    type: string
            categories:
              type: array
              description: Article categories
            tags:
              type: array
              description: Article tags/keywords
            defined_type_name:
              type: string
              description: Item type (dataset, software, etc.)
            published_date:
              type: string
              description: Publication date
            license:
              type: object
              description: License information
      404:
        description: Article not found
      500:
        description: Internal server error
    """
    try:
        client = get_figshare_client()
        article = client.get_article(article_id)

        if not article:
            return jsonify({'error': f'Article {article_id} not found'}), 404

        logger.info(f"Retrieved Figshare article {article_id}: {article.get('title', 'Unknown')}")

        return jsonify(article), 200

    except Exception as e:
        logger.error(f"Error getting Figshare article {article_id}: {str(e)}")
        return jsonify({'error': 'Failed to get article'}), 500


@figshare_bp.route('/articles/<int:article_id>/files', methods=['GET'])
@cross_origin()
def get_article_files(article_id):
    """
    Get files associated with a public Figshare article
    ---
    tags:
      - Figshare Integration
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: Figshare article ID
        example: 12345678
    responses:
      200:
        description: Files retrieved successfully
        schema:
          type: object
          properties:
            article_id:
              type: integer
              description: Figshare article ID
            files:
              type: array
              description: List of files
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: File ID
                  name:
                    type: string
                    description: File name
                  size:
                    type: integer
                    description: File size in bytes
                  download_url:
                    type: string
                    description: Direct download URL
                  computed_md5:
                    type: string
                    description: MD5 checksum
            total_files:
              type: integer
              description: Total number of files
      500:
        description: Internal server error
    """
    try:
        client = get_figshare_client()
        files = client.get_article_files(article_id)

        logger.info(f"Retrieved {len(files)} files for Figshare article {article_id}")

        return jsonify({
            'article_id': article_id,
            'files': files,
            'total_files': len(files)
        }), 200

    except Exception as e:
        logger.error(f"Error getting files for Figshare article {article_id}: {str(e)}")
        return jsonify({'error': 'Failed to get article files'}), 500


@figshare_bp.route('/articles/<int:article_id>/versions', methods=['GET'])
@cross_origin()
def get_article_versions(article_id):
    """
    Get version history of a public Figshare article
    ---
    tags:
      - Figshare Integration
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: Figshare article ID
        example: 12345678
    responses:
      200:
        description: Versions retrieved successfully
        schema:
          type: object
          properties:
            article_id:
              type: integer
              description: Figshare article ID
            versions:
              type: array
              description: List of versions
              items:
                type: object
                properties:
                  version:
                    type: integer
                    description: Version number
                  url:
                    type: string
                    description: URL to this version
            total_versions:
              type: integer
              description: Total number of versions
      500:
        description: Internal server error
    """
    try:
        client = get_figshare_client()
        versions = client.get_article_versions(article_id)

        logger.info(f"Retrieved {len(versions)} versions for Figshare article {article_id}")

        return jsonify({
            'article_id': article_id,
            'versions': versions,
            'total_versions': len(versions)
        }), 200

    except Exception as e:
        logger.error(f"Error getting versions for Figshare article {article_id}: {str(e)}")
        return jsonify({'error': 'Failed to get article versions'}), 500


@figshare_bp.route('/my-articles', methods=['GET'])
@jwt_required()
@cross_origin()
def get_my_articles():
    """
    Get authenticated user's Figshare articles (requires Figshare API token)
    ---
    tags:
      - Figshare Integration
    security:
      - Bearer: []
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Page number (1-indexed)
      - name: page_size
        in: query
        type: integer
        default: 10
        description: Number of results per page
    responses:
      200:
        description: User's articles retrieved successfully
        schema:
          type: object
          properties:
            articles:
              type: array
              description: List of user's articles
            page:
              type: integer
              description: Current page number
            page_size:
              type: integer
              description: Results per page
      401:
        description: Unauthorized - JWT token required
      403:
        description: Figshare API token not configured
      500:
        description: Internal server error
    """
    try:
        if not FIGSHARE_API_TOKEN:
            return jsonify({
                'error': 'Figshare API token not configured',
                'message': 'Contact administrator to configure Figshare authentication'
            }), 403

        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 10, type=int)

        client = get_figshare_client(use_token=True)
        results = client.get_my_articles(page=page, page_size=page_size)

        if 'error' in results:
            return jsonify(results), 403

        logger.info(f"Retrieved {len(results.get('articles', []))} private Figshare articles")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error getting user's Figshare articles: {str(e)}")
        return jsonify({'error': 'Failed to get user articles'}), 500


@figshare_bp.route('/preview/<int:article_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def preview_article_metadata(article_id):
    """
    Preview Figshare article metadata mapped to DOCiD format (without importing)
    ---
    tags:
      - Figshare Integration
    security:
      - Bearer: []
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: Figshare article ID to preview
        example: 12345678
    responses:
      200:
        description: Metadata preview retrieved successfully
        schema:
          type: object
          properties:
            figshare_id:
              type: integer
              description: Figshare article ID
            raw_metadata:
              type: object
              description: Original Figshare metadata
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
                categories:
                  type: array
                  description: Subject categories
                tags:
                  type: array
                  description: Keywords/tags
      404:
        description: Article not found
      401:
        description: Unauthorized - JWT token required
      500:
        description: Internal server error
    """
    try:
        current_user_id = get_jwt_identity()

        client = get_figshare_client()
        article = client.get_article(article_id)

        if not article:
            return jsonify({'error': f'Article {article_id} not found on Figshare'}), 404

        # Map to DOCiD format
        mapped_data = FigshareMetadataMapper.figshare_to_docid(article, current_user_id)

        logger.info(f"Previewed Figshare article {article_id} for user {current_user_id}")

        return jsonify({
            'figshare_id': article_id,
            'raw_metadata': article,
            'mapped_data': mapped_data
        }), 200

    except Exception as e:
        logger.error(f"Error previewing Figshare article {article_id}: {str(e)}")
        return jsonify({'error': 'Failed to preview article metadata'}), 500


# ==================== Sync/Import Endpoints ====================

def save_figshare_creators(publication_id: int, creators_data: list):
    """
    Save creators from Figshare article to publication_creators table

    Args:
        publication_id: Publication ID
        creators_data: List of creator dictionaries from FigshareMetadataMapper
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


@figshare_bp.route('/sync/article/<int:article_id>', methods=['POST'])
@jwt_required()
@cross_origin()
def sync_single_article(article_id):
    """
    Import a single Figshare article to DOCiD publications table
    ---
    tags:
      - Figshare Integration
    security:
      - Bearer: []
    parameters:
      - name: article_id
        in: path
        type: integer
        required: true
        description: Figshare article ID to import
        example: 12345678
    responses:
      201:
        description: Article imported successfully
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
            figshare_id:
              type: integer
              description: Original Figshare article ID
            message:
              type: string
      200:
        description: Article already imported
        schema:
          type: object
          properties:
            message:
              type: string
            publication_id:
              type: integer
            docid:
              type: string
      404:
        description: Article not found on Figshare
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error during import
    """
    try:
        current_user_id = get_jwt_identity()

        # Check if already imported
        existing = Publications.query.filter_by(figshare_article_id=str(article_id)).first()
        if existing:
            return jsonify({
                'message': 'Article already imported',
                'publication_id': existing.id,
                'docid': existing.document_docid,
                'figshare_id': article_id
            }), 200

        # Get article from Figshare
        client = get_figshare_client()
        article = client.get_article(article_id)

        if not article:
            return jsonify({'error': f'Article {article_id} not found on Figshare'}), 404

        # Map metadata
        mapped_data = FigshareMetadataMapper.figshare_to_docid(article, current_user_id)
        pub_data = mapped_data['publication']

        # Get resource type ID
        resource_type_name = pub_data.get('resource_type', 'Dataset')
        resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
        resource_type_id = resource_type.id if resource_type else 1

        # Generate DOCiD using Figshare DOI or create one
        figshare_doi = pub_data.get('doi', '')
        document_docid = figshare_doi if figshare_doi else f"figshare:{article_id}"

        # Create publication
        publication = Publications(
            user_id=current_user_id,
            document_title=pub_data['document_title'],
            document_description=pub_data.get('document_description', ''),
            resource_type_id=resource_type_id,
            doi=figshare_doi,
            document_docid=document_docid,
            figshare_article_id=str(article_id),
            figshare_url=pub_data.get('figshare_url', ''),
            owner='Figshare Repository',
        )

        db.session.add(publication)
        db.session.flush()  # Get publication ID

        # Save creators
        save_figshare_creators(publication.id, mapped_data.get('creators', []))

        db.session.commit()

        logger.info(f"Imported Figshare article {article_id} as publication {publication.id}")

        return jsonify({
            'success': True,
            'publication_id': publication.id,
            'docid': publication.document_docid,
            'figshare_id': article_id,
            'figshare_url': publication.figshare_url,
            'message': 'Article imported successfully'
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error importing Figshare article {article_id}: {str(e)}")
        return jsonify({'error': f'Failed to import article: {str(e)}'}), 500


@figshare_bp.route('/sync/batch', methods=['POST'])
@jwt_required()
@cross_origin()
def sync_batch():
    """
    Batch import Figshare articles to DOCiD publications table
    ---
    tags:
      - Figshare Integration
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            query:
              type: string
              description: Search query to find articles (required if article_ids not provided)
              example: "university research data"
            article_ids:
              type: array
              description: Specific article IDs to import (alternative to query)
              items:
                type: integer
              example: [12345678, 12345679]
            page:
              type: integer
              default: 1
              description: Page number for search results
            page_size:
              type: integer
              default: 50
              description: Number of articles to import (max 100)
            skip_existing:
              type: boolean
              default: true
              description: Skip articles that are already imported
            item_type:
              type: integer
              description: Filter by Figshare item type (3=dataset, 9=software, etc.)
    responses:
      200:
        description: Batch import completed
        schema:
          type: object
          properties:
            total:
              type: integer
              description: Total articles processed
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
              description: Detailed results per article
      401:
        description: Unauthorized - JWT token required
      400:
        description: Bad request - missing query or article_ids
      500:
        description: Server error during batch import
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json() or {}

        query = data.get('query', '').strip()
        article_ids = data.get('article_ids', [])
        page = data.get('page', 1)
        page_size = min(data.get('page_size', 50), 100)
        skip_existing = data.get('skip_existing', True)
        item_type = data.get('item_type')

        if not query and not article_ids:
            return jsonify({'error': 'Either query or article_ids is required'}), 400

        client = get_figshare_client()
        articles_to_import = []

        # Get articles either from search or specific IDs
        if article_ids:
            for aid in article_ids:
                article = client.get_article(aid)
                if article:
                    articles_to_import.append(article)
        else:
            search_results = client.search_articles(
                query=query,
                page=page,
                page_size=page_size,
                item_type=item_type
            )
            articles_to_import = search_results.get('articles', [])

        results = {
            'total': len(articles_to_import),
            'created': 0,
            'skipped': 0,
            'errors': 0,
            'items': []
        }

        for article in articles_to_import:
            article_id = article.get('id')

            try:
                # Check if exists
                if skip_existing:
                    existing = Publications.query.filter_by(figshare_article_id=str(article_id)).first()
                    if existing:
                        results['skipped'] += 1
                        results['items'].append({
                            'figshare_id': article_id,
                            'status': 'skipped',
                            'reason': 'already_exists',
                            'publication_id': existing.id
                        })
                        continue

                # Get full article details if we only have summary
                if 'description' not in article:
                    article = client.get_article(article_id)
                    if not article:
                        results['errors'] += 1
                        results['items'].append({
                            'figshare_id': article_id,
                            'status': 'error',
                            'reason': 'failed_to_fetch_details'
                        })
                        continue

                # Map and create
                mapped_data = FigshareMetadataMapper.figshare_to_docid(article, current_user_id)
                pub_data = mapped_data['publication']

                # Get resource type ID
                resource_type_name = pub_data.get('resource_type', 'Dataset')
                resource_type = ResourceTypes.query.filter_by(resource_type=resource_type_name).first()
                resource_type_id = resource_type.id if resource_type else 1

                # Generate DOCiD
                figshare_doi = pub_data.get('doi', '')
                document_docid = figshare_doi if figshare_doi else f"figshare:{article_id}"

                publication = Publications(
                    user_id=current_user_id,
                    document_title=pub_data['document_title'],
                    document_description=pub_data.get('document_description', ''),
                    resource_type_id=resource_type_id,
                    doi=figshare_doi,
                    document_docid=document_docid,
                    figshare_article_id=str(article_id),
                    figshare_url=pub_data.get('figshare_url', ''),
                    owner='Figshare Repository',
                )

                db.session.add(publication)
                db.session.flush()

                # Save creators
                save_figshare_creators(publication.id, mapped_data.get('creators', []))

                db.session.commit()

                results['created'] += 1
                results['items'].append({
                    'figshare_id': article_id,
                    'publication_id': publication.id,
                    'docid': publication.document_docid,
                    'title': publication.document_title,
                    'status': 'created'
                })

            except Exception as e:
                db.session.rollback()
                results['errors'] += 1
                results['items'].append({
                    'figshare_id': article_id,
                    'status': 'error',
                    'reason': str(e)
                })

        logger.info(f"Batch import completed: {results['created']} created, {results['skipped']} skipped, {results['errors']} errors")

        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error in batch import: {str(e)}")
        return jsonify({'error': str(e)}), 500


@figshare_bp.route('/sync/stats', methods=['GET'])
@jwt_required()
@cross_origin()
def get_sync_stats():
    """
    Get Figshare sync statistics
    ---
    tags:
      - Figshare Integration
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
              description: Total Figshare articles imported
            by_type:
              type: object
              description: Breakdown by resource type
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error
    """
    try:
        # Count all publications with figshare_article_id
        total_imported = Publications.query.filter(
            Publications.figshare_article_id.isnot(None),
            Publications.figshare_article_id != ''
        ).count()

        # Get breakdown by resource type
        from sqlalchemy import func
        type_counts = db.session.query(
            ResourceTypes.resource_type,
            func.count(Publications.id)
        ).join(
            Publications, Publications.resource_type_id == ResourceTypes.id
        ).filter(
            Publications.figshare_article_id.isnot(None),
            Publications.figshare_article_id != ''
        ).group_by(ResourceTypes.resource_type).all()

        by_type = {t[0]: t[1] for t in type_counts}

        return jsonify({
            'total_imported': total_imported,
            'by_type': by_type
        }), 200

    except Exception as e:
        logger.error(f"Error getting sync stats: {str(e)}")
        return jsonify({'error': 'Failed to get statistics'}), 500


@figshare_bp.route('/sync/delete/<int:publication_id>', methods=['DELETE'])
@jwt_required()
@cross_origin()
def delete_synced_article(publication_id):
    """
    Delete a Figshare-imported publication
    ---
    tags:
      - Figshare Integration
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
        description: Publication not found or not a Figshare import
      401:
        description: Unauthorized - JWT token required
      500:
        description: Server error during deletion
    """
    try:
        publication = Publications.query.get(publication_id)

        if not publication:
            return jsonify({'error': 'Publication not found'}), 404

        if not publication.figshare_article_id:
            return jsonify({'error': 'Publication is not a Figshare import'}), 404

        figshare_id = publication.figshare_article_id

        # Delete associated creators
        PublicationCreators.query.filter_by(publication_id=publication_id).delete()

        # Delete the publication
        db.session.delete(publication)
        db.session.commit()

        logger.info(f"Deleted Figshare publication {publication_id} (Figshare ID: {figshare_id})")

        return jsonify({
            'success': True,
            'message': f'Publication {publication_id} deleted successfully',
            'figshare_id': figshare_id
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting publication {publication_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500
