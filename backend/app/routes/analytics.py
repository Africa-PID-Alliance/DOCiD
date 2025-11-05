from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from app import db
from app.models import PublicationViews, FileDownloads, Publications, PublicationFiles, PublicationDocuments, PublicationComments

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/api/publications/<int:publication_id>/views', methods=['POST'])
@cross_origin()
def track_view(publication_id):
    """
    Track a publication view
    ---
    tags:
      - Analytics
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: ID of the publication being viewed
      - name: body
        in: body
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: ID of the user viewing (optional)
    responses:
      201:
        description: View tracked successfully
      404:
        description: Publication not found
      500:
        description: Server error
    """
    try:
        # Verify publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({"status": "error", "message": "Publication not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')

        # Track view
        view = PublicationViews.track_view(
            publication_id=publication_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        current_app.logger.info(f"View tracked for publication {publication_id} from IP {ip_address}")

        return jsonify({
            "status": "success",
            "message": "View tracked",
            "view": view.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking view: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/views/count', methods=['GET'])
@cross_origin()
def get_view_count(publication_id):
    """
    Get view count for a publication
    ---
    tags:
      - Analytics
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: ID of the publication
    responses:
      200:
        description: View count retrieved successfully
      500:
        description: Server error
    """
    try:
        count = PublicationViews.get_view_count(publication_id)
        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "view_count": count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting view count: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/files/<int:file_id>/downloads', methods=['POST'])
@cross_origin()
def track_file_download(file_id):
    """
    Track a file download
    ---
    tags:
      - Analytics
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: ID of the file being downloaded
      - name: body
        in: body
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: ID of the user downloading (optional)
    responses:
      201:
        description: Download tracked successfully
      404:
        description: File not found
      500:
        description: Server error
    """
    try:
        # Verify file exists
        file = PublicationFiles.query.get(file_id)
        if not file:
            return jsonify({"status": "error", "message": "File not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr

        # Track download
        download = FileDownloads.track_download(
            file_id=file_id,
            user_id=user_id,
            ip_address=ip_address
        )

        current_app.logger.info(f"File download tracked for file {file_id} from IP {ip_address}")

        return jsonify({
            "status": "success",
            "message": "Download tracked",
            "download": download.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking download: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/documents/<int:document_id>/downloads', methods=['POST'])
@cross_origin()
def track_document_download(document_id):
    """
    Track a document download
    ---
    tags:
      - Analytics
    parameters:
      - name: document_id
        in: path
        type: integer
        required: true
        description: ID of the document being downloaded
      - name: body
        in: body
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: ID of the user downloading (optional)
    responses:
      201:
        description: Download tracked successfully
      404:
        description: Document not found
      500:
        description: Server error
    """
    try:
        # Verify document exists
        document = PublicationDocuments.query.get(document_id)
        if not document:
            return jsonify({"status": "error", "message": "Document not found"}), 404

        # Get request metadata
        user_id = request.json.get('user_id') if request.json else None
        ip_address = request.remote_addr

        # Track download
        download = FileDownloads.track_download(
            document_id=document_id,
            user_id=user_id,
            ip_address=ip_address
        )

        current_app.logger.info(f"Document download tracked for document {document_id} from IP {ip_address}")

        return jsonify({
            "status": "success",
            "message": "Download tracked",
            "download": download.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error tracking download: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/downloads/count', methods=['GET'])
@cross_origin()
def get_download_count(publication_id):
    """
    Get download count for all files in a publication
    ---
    tags:
      - Analytics
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: ID of the publication
    responses:
      200:
        description: Download count retrieved successfully
      500:
        description: Server error
    """
    try:
        count = FileDownloads.get_download_count(publication_id)
        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "download_count": count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting download count: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/stats', methods=['GET'])
@cross_origin()
def get_publication_stats(publication_id):
    """
    Get comprehensive stats for a publication (views, downloads, comments)
    ---
    tags:
      - Analytics
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: ID of the publication
    responses:
      200:
        description: Statistics retrieved successfully
      500:
        description: Server error
    """
    try:
        view_count = PublicationViews.get_view_count(publication_id)
        download_count = FileDownloads.get_download_count(publication_id)
        comment_count = PublicationComments.query.filter_by(
            publication_id=publication_id,
            status='active'
        ).count()

        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "stats": {
                "views": view_count,
                "downloads": download_count,
                "comments": comment_count
            }
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting publication stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/files/<int:file_id>/stats', methods=['GET'])
@cross_origin()
def get_file_stats(file_id):
    """
    Get download statistics for a specific publication file
    ---
    tags:
      - Analytics
    parameters:
      - name: file_id
        in: path
        type: integer
        required: true
        description: ID of the publication file
    responses:
      200:
        description: File statistics retrieved successfully
      404:
        description: File not found
      500:
        description: Server error
    """
    try:
        # Verify file exists
        file = PublicationFiles.query.get(file_id)
        if not file:
            return jsonify({"status": "error", "message": "File not found"}), 404

        # Get download count for this specific file
        download_count = FileDownloads.query.filter_by(publication_file_id=file_id).count()

        return jsonify({
            "status": "success",
            "file_id": file_id,
            "downloads": download_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting file stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/documents/<int:document_id>/stats', methods=['GET'])
@cross_origin()
def get_document_stats(document_id):
    """
    Get download statistics for a specific publication document
    ---
    tags:
      - Analytics
    parameters:
      - name: document_id
        in: path
        type: integer
        required: true
        description: ID of the publication document
    responses:
      200:
        description: Document statistics retrieved successfully
      404:
        description: Document not found
      500:
        description: Server error
    """
    try:
        # Verify document exists
        document = PublicationDocuments.query.get(document_id)
        if not document:
            return jsonify({"status": "error", "message": "Document not found"}), 404

        # Get download count for this specific document
        download_count = FileDownloads.query.filter_by(publication_document_id=document_id).count()

        return jsonify({
            "status": "success",
            "document_id": document_id,
            "downloads": download_count
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting document stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@analytics_bp.route('/api/publications/<int:publication_id>/files-stats', methods=['GET'])
@cross_origin()
def get_all_files_stats(publication_id):
    """
    Get download statistics for all files and documents in a publication
    ---
    tags:
      - Analytics
    parameters:
      - name: publication_id
        in: path
        type: integer
        required: true
        description: ID of the publication
    responses:
      200:
        description: Statistics retrieved successfully
      404:
        description: Publication not found
      500:
        description: Server error
    """
    try:
        # Verify publication exists
        publication = Publications.query.get(publication_id)
        if not publication:
            return jsonify({"status": "error", "message": "Publication not found"}), 404

        # Get all files for this publication
        files = PublicationFiles.query.filter_by(publication_id=publication_id).all()
        files_stats = []
        for file in files:
            download_count = FileDownloads.query.filter_by(publication_file_id=file.id).count()
            files_stats.append({
                "id": file.id,
                "title": file.title,
                "file_url": file.file_url,
                "downloads": download_count
            })

        # Get all documents for this publication
        documents = PublicationDocuments.query.filter_by(publication_id=publication_id).all()
        documents_stats = []
        for doc in documents:
            download_count = FileDownloads.query.filter_by(publication_document_id=doc.id).count()
            documents_stats.append({
                "id": doc.id,
                "title": doc.title,
                "file_url": doc.file_url,
                "downloads": download_count
            })

        return jsonify({
            "status": "success",
            "publication_id": publication_id,
            "files": files_stats,
            "documents": documents_stats
        }), 200

    except Exception as e:
        current_app.logger.error(f"Error getting files stats: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500
