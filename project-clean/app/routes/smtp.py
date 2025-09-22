from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ..email_utils import send_email
import re

# Initialize Blueprint and Rate Limiter
smtp_bp = Blueprint('smtp', __name__, url_prefix='/api/v1/smtp')
limiter = Limiter(key_func=get_remote_address)

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(regex, email) is not None

# Apply a rate limit to the send email route (e.g., 5 requests per minute per IP)
@limiter.limit("5 per minute")
@smtp_bp.route('/send', methods=['POST'])
# @jwt_required()  # Require JWT token for access
def send_email_route():
    data = request.get_json()
    email = data.get('email')
    subject = data.get('subject')
    body = data.get('body')

    # Validate email format
    if not is_valid_email(email):
     return jsonify({"error": "Invalid email address"}), 400

    # Check for missing fields
    if not subject or not body:
        return jsonify({"error": "Subject and body content are required"}), 400

    # Optional: Check if the user is allowed to send email to this address
    # (e.g., restrict to certain domains or whitelist)

    try:
        send_email(
            to=email,
            subject=subject,
            body=body
        )
        return jsonify({"message": "Email sent successfully"}), 200
    except Exception as e:
        current_app.logger.error(f"Failed to send email: {e}")
        return jsonify({"error": "Failed to send email"}), 500
