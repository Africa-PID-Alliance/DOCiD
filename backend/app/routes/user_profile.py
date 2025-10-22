# app/routes/user_profile.py
import logging
from logging.handlers import RotatingFileHandler
import os
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import UserAccount, Publications
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime

# Create logs directory if it doesn't exist
if not os.path.exists('logs'):
    os.makedirs('logs')

# Create file handler for user_profile.log with rotation
file_handler = RotatingFileHandler(
    'logs/user_profile.log',
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

user_profile_bp = Blueprint("user_profile", __name__, url_prefix="/api/v1/user-profile")


@user_profile_bp.route('/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    """
    Get user profile by user ID

    This endpoint retrieves comprehensive user profile information including
    all profile fields, social links, and identifiers.

    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the user
    responses:
      200:
        description: User profile retrieved successfully
        schema:
          type: object
          properties:
            user_id:
              type: integer
              description: User's unique identifier
            user_name:
              type: string
              description: Username
            full_name:
              type: string
              description: User's full name
            email:
              type: string
              description: User's email address
            type:
              type: string
              description: Account type (google, orcid, github, email)
            avator:
              type: string
              description: Profile avatar URL
            affiliation:
              type: string
              description: User's affiliation/organization
            role:
              type: string
              description: User's role
            orcid_id:
              type: string
              description: ORCID identifier
            ror_id:
              type: string
              description: ROR identifier
            country:
              type: string
              description: User's country
            city:
              type: string
              description: User's city
            location:
              type: string
              description: Custom location string
            linkedin_profile_link:
              type: string
              description: LinkedIn profile URL
            facebook_profile_link:
              type: string
              description: Facebook profile URL
            x_profile_link:
              type: string
              description: X (Twitter) profile URL
            instagram_profile_link:
              type: string
              description: Instagram profile URL
            github_profile_link:
              type: string
              description: GitHub profile URL
            date_joined:
              type: string
              description: Account creation date (ISO 8601)
            first_time:
              type: integer
              description: First time login flag (0 or 1)
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Fetching user profile for user_id: {user_id}")

        user = UserAccount.query.get(user_id)
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found'}), 404

        # Return comprehensive user profile (excluding sensitive data like password)
        profile_data = {
            'user_id': user.user_id,
            'user_name': user.user_name,
            'full_name': user.full_name,
            'email': user.email,
            'type': user.type,
            'avator': user.avator,
            'affiliation': user.affiliation,
            'role': user.role,
            'orcid_id': user.orcid_id,
            'ror_id': user.ror_id,
            'country': user.country,
            'city': user.city,
            'location': user.location,
            'linkedin_profile_link': user.linkedin_profile_link,
            'facebook_profile_link': user.facebook_profile_link,
            'x_profile_link': user.x_profile_link,
            'instagram_profile_link': user.instagram_profile_link,
            'github_profile_link': user.github_profile_link,
            'date_joined': user.date_joined.isoformat() if user.date_joined else None,
            'first_time': user.first_time
        }

        logger.info(f"User profile retrieved successfully for user_id: {user_id}")
        return jsonify(profile_data), 200

    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_profile_bp.route('/<int:user_id>', methods=['PUT', 'PATCH'])
def update_user_profile(user_id):
    """
    Update user profile

    This endpoint allows users to update their profile information.
    Only the user themselves can update their own profile.

    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the user
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              user_name:
                type: string
                description: Username (optional)
              full_name:
                type: string
                description: User's full name (optional)
              email:
                type: string
                description: User's email address (optional)
              affiliation:
                type: string
                description: User's affiliation/organization (optional)
              role:
                type: string
                description: User's role (optional)
              orcid_id:
                type: string
                description: ORCID identifier (optional)
              ror_id:
                type: string
                description: ROR identifier (optional)
              country:
                type: string
                description: User's country (optional)
              city:
                type: string
                description: User's city (optional)
              location:
                type: string
                description: Custom location string (optional)
              linkedin_profile_link:
                type: string
                description: LinkedIn profile URL (optional)
              facebook_profile_link:
                type: string
                description: Facebook profile URL (optional)
              x_profile_link:
                type: string
                description: X (Twitter) profile URL (optional)
              instagram_profile_link:
                type: string
                description: Instagram profile URL (optional)
              github_profile_link:
                type: string
                description: GitHub profile URL (optional)
              avator:
                type: string
                description: Profile avatar URL (optional)
    responses:
      200:
        description: User profile updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
              description: Success message
            user_data:
              type: object
              description: Updated user profile data
      400:
        description: Bad request (validation errors)
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Updating user profile for user_id: {user_id}")

        # Get user from database
        user = UserAccount.query.get(user_id)
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found'}), 404

        # Get update data from request
        data = request.get_json()
        if not data:
            logger.warning(f"No data provided for user_id: {user_id}")
            return jsonify({'message': 'No data provided'}), 400

        # Track what fields are being updated
        updated_fields = []

        # Update allowed fields
        updateable_fields = [
            'user_name', 'full_name', 'email', 'affiliation', 'role',
            'orcid_id', 'ror_id', 'country', 'city', 'location',
            'linkedin_profile_link', 'facebook_profile_link',
            'x_profile_link', 'instagram_profile_link', 'github_profile_link',
            'avator'
        ]

        for field in updateable_fields:
            if field in data:
                old_value = getattr(user, field)
                new_value = data[field]

                # Only update if value has changed
                if old_value != new_value:
                    setattr(user, field, new_value)
                    updated_fields.append(field)
                    logger.info(f"Updated {field} for user_id: {user_id}")

        # Update first_time flag if it exists in data
        if 'first_time' in data:
            try:
                first_time_value = int(data['first_time'])
                if first_time_value in [0, 1]:
                    user.first_time = first_time_value
                    updated_fields.append('first_time')
            except ValueError:
                logger.warning(f"Invalid first_time value: {data['first_time']}")

        if not updated_fields:
            logger.info(f"No changes detected for user_id: {user_id}")
            return jsonify({
                'message': 'No changes detected',
                'user_data': user.serialize()
            }), 200

        # Commit changes to database
        db.session.commit()

        logger.info(f"User profile updated successfully for user_id: {user_id}, fields: {updated_fields}")

        return jsonify({
            'message': 'User profile updated successfully',
            'updated_fields': updated_fields,
            'user_data': user.serialize()
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database integrity error: {str(e.orig)}", exc_info=True)
        return jsonify({'error': 'Database integrity error (possibly duplicate email or username)'}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating user profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_profile_bp.route('/<int:user_id>/publications', methods=['GET'])
def get_user_publications(user_id):
    """
    Get all publications for a specific user

    This endpoint retrieves all publications created by or associated with a user
    with optional pagination and filtering.

    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the user
      - name: page
        in: query
        type: integer
        description: Page number for pagination defaults to 1
      - name: page_size
        in: query
        type: integer
        description: Number of publications per page defaults to 10 max 100
      - name: sort
        in: query
        type: string
        description: Sort field published title updated_at or id
      - name: order
        in: query
        type: string
        description: Sort order asc or desc defaults to desc
    responses:
      200:
        description: Publications retrieved successfully
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Fetching publications for user_id: {user_id}")

        # Verify user exists
        user = UserAccount.query.get(user_id)
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found'}), 404

        # Get pagination parameters
        page = int(request.args.get('page', 1))
        page_size = min(int(request.args.get('page_size', 10)), 100)  # Max 100 per page

        # Get sorting parameters
        sort_field = request.args.get('sort', 'published')
        order = request.args.get('order', 'desc')

        # Validate parameters
        if page <= 0 or page_size <= 0:
            return jsonify({'message': 'page and page_size must be positive integers'}), 400

        if order not in ['asc', 'desc']:
            return jsonify({'message': 'Invalid order parameter (must be "asc" or "desc")'}), 400

        valid_sort_fields = ['published', 'title', 'updated_at', 'id']
        if sort_field not in valid_sort_fields:
            return jsonify({'message': f'Invalid sort field (must be one of {valid_sort_fields})'}), 400

        # Build query
        from sqlalchemy import desc as sql_desc, asc as sql_asc

        query = Publications.query.filter_by(user_id=user_id)

        # Apply sorting
        sort_column = getattr(Publications, sort_field)
        if order == 'desc':
            query = query.order_by(sql_desc(sort_column))
        else:
            query = query.order_by(sql_asc(sort_column))

        # Get total count
        total_publications = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        publications = query.limit(page_size).offset(offset).all()

        # Prepare publication data
        publications_data = [
            {
                'id': pub.id,
                'document_docid': pub.document_docid,
                'document_title': pub.document_title,
                'document_description': pub.document_description,
                'resource_type_id': pub.resource_type_id,
                'publication_poster_url': pub.publication_poster_url,
                'doi': pub.doi,
                'owner': pub.owner,
                'avatar': pub.avatar,
                'published': pub.published.isoformat() if pub.published else None,
                'updated_at': pub.updated_at.isoformat() if pub.updated_at else None,
                'updated_by': pub.updated_by
            }
            for pub in publications
        ]

        # Pagination metadata
        pagination_metadata = {
            'total': total_publications,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_publications + page_size - 1) // page_size
        }

        logger.info(f"Retrieved {len(publications_data)} publications for user_id: {user_id}")

        return jsonify({
            'user_id': user_id,
            'user_name': user.user_name,
            'full_name': user.full_name,
            'publications': publications_data,
            'pagination': pagination_metadata
        }), 200

    except ValueError as e:
        logger.error(f"Invalid parameter value: {str(e)}")
        return jsonify({'message': 'Invalid pagination parameters (must be integers)'}), 400
    except Exception as e:
        logger.error(f"Error fetching user publications: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_profile_bp.route('/<int:user_id>/change-password', methods=['POST'])
def change_password(user_id):
    """
    Change user password

    This endpoint allows users to change their password.
    Requires current password for verification.

    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the user
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - current_password
              - new_password
            properties:
              current_password:
                type: string
                description: User's current password
              new_password:
                type: string
                description: New password (minimum 8 characters)
    responses:
      200:
        description: Password changed successfully
      400:
        description: Bad request (validation errors or incorrect current password)
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Password change request for user_id: {user_id}")

        # Get user from database
        user = UserAccount.query.get(user_id)
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found'}), 404

        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 400

        current_password = data.get('current_password')
        new_password = data.get('new_password')

        # Validate required fields
        if not current_password or not new_password:
            logger.warning(f"Missing password fields for user_id: {user_id}")
            return jsonify({'message': 'Current password and new password are required'}), 400

        # Validate new password length
        if len(new_password) < 8:
            logger.warning(f"New password too short for user_id: {user_id}")
            return jsonify({'message': 'New password must be at least 8 characters long'}), 400

        # Check if user has a password set (for social auth users)
        if not user.password:
            logger.warning(f"User has no password set (social auth): user_id={user_id}")
            return jsonify({'message': 'Cannot change password for social auth accounts without existing password'}), 400

        # Verify current password
        if not check_password_hash(user.password, current_password):
            logger.warning(f"Incorrect current password for user_id: {user_id}")
            return jsonify({'message': 'Current password is incorrect'}), 400

        # Update password
        user.password = generate_password_hash(new_password)
        db.session.commit()

        logger.info(f"Password changed successfully for user_id: {user_id}")

        return jsonify({
            'message': 'Password changed successfully'
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error changing password: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@user_profile_bp.route('/<int:user_id>/statistics', methods=['GET'])
def get_user_statistics(user_id):
    """
    Get user statistics

    This endpoint retrieves statistics about a user's activity including
    publication counts, draft counts, etc.

    ---
    tags:
      - User Profile
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: The unique identifier of the user
    responses:
      200:
        description: Statistics retrieved successfully
        schema:
          type: object
          properties:
            user_id:
              type: integer
            total_publications:
              type: integer
            publications_this_year:
              type: integer
            publications_this_month:
              type: integer
            member_since:
              type: string
      404:
        description: User not found
      500:
        description: Internal server error
    """
    try:
        logger.info(f"Fetching statistics for user_id: {user_id}")

        # Verify user exists
        user = UserAccount.query.get(user_id)
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found'}), 404

        # Get total publications count
        total_publications = Publications.query.filter_by(user_id=user_id).count()

        # Get publications this year
        from sqlalchemy import extract
        current_year = datetime.utcnow().year
        publications_this_year = Publications.query.filter(
            Publications.user_id == user_id,
            extract('year', Publications.published) == current_year
        ).count()

        # Get publications this month
        current_month = datetime.utcnow().month
        publications_this_month = Publications.query.filter(
            Publications.user_id == user_id,
            extract('year', Publications.published) == current_year,
            extract('month', Publications.published) == current_month
        ).count()

        statistics_data = {
            'user_id': user_id,
            'user_name': user.user_name,
            'full_name': user.full_name,
            'total_publications': total_publications,
            'publications_this_year': publications_this_year,
            'publications_this_month': publications_this_month,
            'member_since': user.date_joined.isoformat() if user.date_joined else None
        }

        logger.info(f"Statistics retrieved for user_id: {user_id}")

        return jsonify(statistics_data), 200

    except Exception as e:
        logger.error(f"Error fetching user statistics: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500
