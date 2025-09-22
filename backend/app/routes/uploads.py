from flask import Blueprint, send_from_directory, jsonify
import os

uploads_bp = Blueprint('uploads', __name__, url_prefix='/uploads')

# Define the path to the uploads directory
UPLOADS_DIRECTORY = os.path.join(os.getcwd(), 'uploads')

@uploads_bp.route('/<path:filename>', methods=['GET'])
def get_static_file(filename):
    """
    Serve a static file (e.g., images, PDFs) from the uploads directory.

    ---
    tags:
      - Static Files
    parameters:
      - in: path
        name: filename
        type: string
        required: true
        description: Name of the file to retrieve.
    responses:
      200:
        description: File successfully retrieved.
      404:
        description: File not found.
      500:
        description: Internal server error.
    """
    try:
        # Ensure the file exists in the uploads directory
        if not os.path.exists(os.path.join(UPLOADS_DIRECTORY, filename)):
            return jsonify({'error': 'File not found'}), 404

        # Serve the file
        return send_from_directory(UPLOADS_DIRECTORY, filename)

    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
