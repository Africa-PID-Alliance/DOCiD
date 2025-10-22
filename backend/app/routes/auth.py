# app/routes/auth.py
import functools
import logging
from logging.handlers import RotatingFileHandler
from flask import Blueprint, g, redirect, request, session, url_for, jsonify
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from app.models import UserAccount, PasswordResets, RegistrationTokens   
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# ✅ Configure Logging
logger = logging.getLogger("auth_logger")
logger.setLevel(logging.DEBUG)
handler = RotatingFileHandler("auth.log", maxBytes=1000000, backupCount=5)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


# JWT configuration
jwt = JWTManager()

auth_bp = Blueprint('auth', __name__, url_prefix="/api/v1/auth")

@auth_bp.route("/store-registration-token", methods=["POST"])
def store_registration_token():
    """
    Store a registration token for initiating user registration.

    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: query
        required: true
        schema:
          type: string
        description: The email address of the user to register.
      - name: token
        in: query
        required: true
        schema:
          type: string
        description: The unique registration token.
      - name: expires_at
        in: query
        required: true
        schema:
          type: string
          format: date-time
        description: The expiration timestamp of the registration token (ISO format).
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                description: The email address of the user to register.
                example: "user@example.com"
              token:
                type: string
                description: The unique registration token.
                example: "unique-registration-token"
              expires_at:
                type: string
                format: date-time
                description: The expiration timestamp of the registration token (ISO format).
                example: "2024-10-08T12:34:56"
    responses:
      201:
        description: Registration token stored successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                success:
                  type: boolean
                  example: true
                message:
                  type: string
                  example: "Registration token stored successfully."
      400:
        description: Bad request (e.g., missing or invalid parameters)
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Email already exists or required fields missing."
      500:
        description: Internal server error
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  example: "Failed to store registration token: <error details>"
    """
    logger.info("Received request to store registration token")
    try:
        data = request.get_json()
        email = data.get("email")
        token = data.get("token")
        expires_at = data.get("expires_at")
        
        if not email or not token or not expires_at:
            logger.warning("Missing required fields: email, token, expires_at")
            return jsonify({"error": "Email, token, and expires_at are required fields."}), 400

        existing_user = UserAccount.query.filter_by(email=email).first()
        if existing_user:
            logger.warning(f"Email {email} already exists")
            return jsonify({"error": "Email already exists."}), 400

        new_token = RegistrationTokens(email=email, token=token, expires_at=expires_at)
        db.session.add(new_token)
        db.session.commit()
        
        logger.info("Registration token stored successfully")
        return jsonify({"success": True, "message": "Registration token stored successfully."}), 201
    
    except IntegrityError:
        db.session.rollback()
        logger.error("IntegrityError: Token already exists")
        return jsonify({"error": "Token already exists."}), 400
    except Exception as e:
        logger.exception("Failed to store registration token")
        return jsonify({"error": f"Failed to store registration token: {str(e)}"}), 500
 
@auth_bp.route("/complete-registration", methods=["POST"])
def complete_registration():
    """
    Completes user registration by verifying the token and adding the user to the users table if valid.

    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: query
        required: true
        schema:
          type: string
          description: The email associated with the registration token.
          example: "user@example.com"
      - name: token
        in: query
        required: true
        schema:
          type: string
          description: The registration token.
          example: "unique-registration-token"
      - name: avator
        in: query
        required: false
        schema:
          type: string
          description: The URL of the user's avatar (optional).
          example: "https://example.com/avatar.jpg"
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                required: true
                description: The email associated with the registration token.
                example: "user@example.com"
              token:
                type: string
                required: true
                description: The registration token.
                example: "unique-registration-token"
              username:
                type: string
                description: The username to be assigned to the user.
                example: "johndoe"
              name:
                type: string
                description: The full name of the user.
                example: "John Doe"
              affiliation:
                type: string
                description: The user's affiliation (optional).
                example: "ABC Company"
              password:
                type: string
                description: The user's password.
                example: "securePassword123"
              avator:
                type: string
                description: The user's avatar URL.
                example: "https://example.com/avatar.jpg"
    responses:
      200:
        description: Registration completed successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Success message indicating registration completion.
                  example: "Registration completed successfully"
      400:
        description: Invalid token, email, or token has expired, or user already exists
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message explaining the issue.
                  example: "Invalid token or email"
      500:
        description: Internal server error
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message in case of database or other server issues.
                  example: "Database error occurred: <error details>"
    """
    logger.info("Received request to complete user registration")
    try:
        data = request.get_json()
        if not data:
            logger.warning("Missing JSON data")
            return jsonify({'message': 'Missing JSON data'}), 400

        email = data.get("email")
        token = data.get("token")
        avator = data.get("avator")

        if not email or not token:
            logger.warning("Missing required fields: email or token")
            return jsonify({'message': 'Missing required fields'}), 400

        token_entry = RegistrationTokens.query.filter_by(email=email, token=token).first()
        if not token_entry:
            logger.warning("Invalid token or email")
            return jsonify({'message': 'Invalid token or email'}), 400

        if datetime.utcnow() > token_entry.expires_at:
            logger.warning("Token has expired")
            return jsonify({'message': 'Token has expired'}), 400

        user = UserAccount.query.filter_by(email=email).first()
        if user is None:
            logger.warning("User not found")
            return jsonify({"message": "User not found"}), 404

        logger.info("User registration completed successfully")
        return jsonify({
            "user_id": user.user_id,
            "user_name": user.user_name,
            "full_name": user.full_name,
            "social_id": user.social_id,
            "type": user.type,
            "affiliation": user.affiliation,
            "date_joined": user.date_joined.isoformat(),
            "email": user.email,
            "first_time": user.first_time,
            "avator": user.avator
        }), 200

    except Exception as e:
        logger.exception("Error completing registration")
        return jsonify({'message': f"Error completing registration: {str(e)}"}), 500
        

@auth_bp.route("/social-auth-register", methods=["POST"])
def social_auth_register():
    """
    Social Authentication Registration.

    This endpoint registers a user using a social authentication provider (e.g., Google, Facebook).

    ---
    tags:
      - Authentication
    parameters:
      - name: social_id
        in: query
        required: true
        schema:
          type: string
        description: The unique ID provided by the social authentication provider.
        example: "1234567890"
      - name: type
        in: query
        required: true
        schema:
          type: string
        description: The type of social provider (e.g., google, facebook).
        example: "google"
      - name: name
        in: query
        required: false
        schema:
          type: string
        description: The full name of the user from the social provider.
        example: "John Doe"
      - name: email
        in: query
        required: false
        schema:
          type: string
        description: The email address from the social provider.
        example: "johndoe@example.com"
      - name: avator
        in: query
        required: false
        schema:
          type: string
        description: The user's profile avator URL from the social provider.
        example: "https://example.com/profile.jpg"
      - name: timestamp
        in: query
        required: false
        schema:
          type: string
        description: The timestamp of the authentication event in ISO format.
        example: "2024-10-08T12:34:56Z"
      - name: username
        in: query
        required: false
        schema:
          type: string
        description: The desired username.
        example: "johndoe"
      - name: affiliation
        in: query
        required: false
        schema:
          type: string
        description: The user's affiliation, if available.
        example: "ABC Company"
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              social_id:
                type: string
                description: The unique social ID of the user.
                example: "1234567890"
              type:
                type: string
                description: The type of social provider (e.g., google, facebook).
                example: "google"
              name:
                type: string
                description: The full name of the user from the social provider.
                example: "John Doe"
              email:
                type: string
                description: The email address from the social provider.
                example: "johndoe@example.com"
              avator:
                type: string
                description: The user's profile avator URL from the social provider.
                example: "https://example.com/profile.jpg"
              timestamp:
                type: string
                description: The timestamp of the authentication event in ISO format.
                example: "2024-10-08T12:34:56Z"
              username:
                type: string
                description: The desired username.
                example: "johndoe"
              affiliation:
                type: string
                description: The user's affiliation, if available.
                example: "ABC Company"
    responses:
      200:
        description: User authenticated or registered successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Indicates if the request was successful.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "User registered successfully."
                user_data:
                  type: object
                  description: User information.
                  properties:
                    user_id:
                      type: integer
                      description: Unique identifier for the user.
                      example: 1
                    user_name:
                      type: string
                      description: Username.
                      example: "johndoe"
                    full_name:
                      type: string
                      description: Full name of the user.
                      example: "John Doe"
                    email:
                      type: string
                      description: User's email address.
                      example: "johndoe@example.com"
                    avator:
                      type: string
                      description: URL of the user's profile avator.
                      example: "https://example.com/profile.jpg"
      400:
        description: Missing required fields or user already exists.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message.
                  example: "User already exists."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "Failed to register user due to server error."
    """
      
    try:
        data = request.get_json()
        social_id = data.get("social_id")
        account_type = data.get("type")
        name = data.get("name")
        email = data.get("email")
        avator = data.get("avator", "https://example.com/default-avatar.jpg")
        username = data.get("username", "")
        affiliation = data.get("affiliation", "")

        # ✅ Log incoming request
        logger.info(f"Received social authentication registration request: social_id={social_id}, type={account_type}")

        # ✅ Check for required fields
        if not social_id or not account_type:
            logger.warning("Registration failed: Missing required fields (social_id, type).")
            return jsonify({'error': 'Social ID and account type are required.'}), 400

        # ✅ Check if the user already exists
        existing_user = UserAccount.query.filter_by(social_id=social_id).first()
        if existing_user:
            logger.info(f"User with social_id={social_id} already exists.")
            return jsonify({
                'status': True,
                'message': 'User already exists',
                'user_data': existing_user.serialize()
            }), 200

        # ✅ Register new user
        new_user = UserAccount(
            user_name=username,
            full_name=name,
            email=email,
            social_id=social_id,
            type=account_type,
            affiliation=affiliation,
            avator=avator,
            first_time=1
        )
        db.session.add(new_user)
        db.session.commit()
        logger.info(f"User registered successfully: social_id={social_id}, email={email}")

        return jsonify({
            'status': True,
            'message': 'User registered successfully',
            'user_data': new_user.serialize()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error during registration for social_id={social_id}: {str(e.orig)}", exc_info=True)
        return jsonify({'error': 'Database error occurred.', 'details': str(e.orig)}), 400
    except Exception as e:
        logger.exception(f"Unexpected error during registration for social_id={social_id}")
        return jsonify({'error': f'Failed to register user: {str(e)}'}), 500 

@auth_bp.route("/set-password-social", methods=["POST"])
def set_password_social():
    """
    Set a password for a user registered via social authentication.

    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: body
        required: true
        schema:
          type: string
          example: "user@example.com"
      - name: password
        in: body
        required: true
        schema:
          type: string
          example: "securePassword123"
      - name: type
        in: body
        required: true
        schema:
          type: string
          example: "google"
      - name: id
        in: body
        required: true
        schema:
          type: integer
          example: 1
    responses:
      200:
        description: Password set successfully
      400:
        description: User not found or other error
      500:
        description: Internal server error
    """
     
    try:
        data = request.json
        email = data.get("email")
        password = data.get("password")
        account_type = data.get("type")
        user_id = data.get("id")

        # ✅ Log incoming request
        logger.info(f"Received set-password request for user_id={user_id}, email={email}")

        # ✅ Check for required fields
        if not email or not password or not account_type or not user_id:
            logger.warning("Password setting failed: Missing required fields (email, password, type, id).")
            return jsonify({'message': 'Email, password, type, and user ID are required.'}), 400

        # ✅ Find the user by ID
        user = UserAccount.query.filter_by(user_id=user_id).first()
        if not user:
            logger.warning(f"User not found: user_id={user_id}")
            return jsonify({'message': 'User not found.'}), 400

        # ✅ Update password
        user.password = generate_password_hash(password)
        user.email = email
        user.type = account_type
        user.first_time = 0
        db.session.commit()

        logger.info(f"Password updated successfully for user_id={user_id}")

        return jsonify({
            'status': True,
            'message': 'Password set successfully',
            'user_id': user.user_id,
            'user_name': user.user_name,
            'full_name': user.full_name,
            'email': user.email,
            'avator': user.avator
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error while setting password for user_id={user_id}: {str(e.orig)}", exc_info=True)
        return jsonify({'message': 'Database error occurred.', 'error': str(e.orig)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemy error while setting password for user_id={user_id}: {str(e)}", exc_info=True)
        return jsonify({'message': 'Database error occurred.', 'error': str(e)}), 500
    except Exception as e:
        logger.exception(f"Unexpected error while setting password for user_id={user_id}")
        return jsonify({'message': str(e)}), 500
      

@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a New User Account.

    This endpoint registers a new user, checking if the email or username already exists.

    ---
    tags:
      - Authentication
    parameters:
      - name: social_id
        in: query
        required: false
        schema:
          type: string
        description: The social login ID (e.g., Google, Facebook, etc.).
        example: "1234567890"
      - name: type
        in: query
        required: true
        schema:
          type: string
        description: The type of login (e.g., google, facebook, orcid).
        example: "google"
      - name: user_name
        in: query
        required: true
        schema:
          type: string
        description: The desired username.
        example: "johndoe"
      - name: full_name
        in: query
        required: true
        schema:
          type: string
        description: The full name of the user.
        example: "John Doe"
      - name: email
        in: query
        required: true
        schema:
          type: string
        description: The email address of the user.
        example: "johndoe@example.com"
      - name: affiliation
        in: query
        required: false
        schema:
          type: string
        description: The user's affiliation.
        example: "ABC Company"
      - name: avator
        in: query
        required: false
        schema:
          type: string
        description: The user's profile avator URL.
        example: "https://example.com/profile.jpg"
      - name: password
        in: query
        required: false
        schema:
          type: string
        description: The user's password (optional for social logins).
        example: "SecurePassword123"
    """
    
    try:
        data = request.json
        social_id = data.get("social_id")
        account_type = data.get("type")
        username = data.get("user_name")
        full_name = data.get("full_name")
        email = data.get("email")
        affiliation = data.get("affiliation", None)
        avator = data.get("avator", None)
        password = data.get("password", None)

        logger.info(f"Received registration request - Type: {account_type}, Email: {email}, Social ID: {social_id}, Username: {username}")

        # Determine query condition based on account type
        if account_type in ["google", "orcid", "github"] and social_id:
            logger.info(f"Checking existing user with social_id: {social_id}")
            existing_user = UserAccount.query.filter(UserAccount.social_id == social_id).first()
        elif account_type == "email" and email:
            logger.info(f"Checking existing user with email: {email}")
            existing_user = UserAccount.query.filter(UserAccount.email == email).first()
        else:
            logger.warning("Invalid account type or missing required identifier (email/social_id)")
            return jsonify({"message": "Invalid account type or missing identifier (email/social_id)."}), 400

        if existing_user:
            logger.warning(f"User already exists: {existing_user.email if existing_user.email else existing_user.social_id}")
            return jsonify({
                'status': False,  
                "message": "User already exists", 
                'user_id': existing_user.user_id,
                'user_name': existing_user.user_name,
                'full_name': existing_user.full_name,
                'type': existing_user.type,
                'first_time': existing_user.first_time,
                'email': existing_user.email,
                'avator': existing_user.avator,
                'affiliation': existing_user.affiliation
            }), 200

        hashed_password = generate_password_hash(password) if password else None

        new_user = UserAccount(
            user_name=username,
            full_name=full_name,
            email=email,
            social_id=social_id,
            type=account_type,
            affiliation=affiliation,
            avator=avator,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.flush()
        new_user_id = new_user.user_id  # Access the ID after flush
        db.session.commit()

        logger.info(f"User registered successfully: {new_user_id}, Email: {email if email else 'N/A'}, Social ID: {social_id if social_id else 'N/A'}")

        return jsonify({
            'status': True,
            'message': 'Registration successful',
            'user_id': new_user.user_id,
            'user_name': new_user.user_name,
            'full_name': new_user.full_name,
            'type': new_user.type,
            'first_time': new_user.first_time,
            'email': new_user.email,
            'avator': new_user.avator,
            'affiliation': new_user.affiliation
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error during registration: {str(e.orig)}")
        return jsonify({'message': 'Database error occurred.', 'error': str(e.orig)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemy error during registration: {str(e)}")
        return jsonify({'message': 'Database error occurred.', 'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({'message': str(e)}), 500  

@auth_bp.route("/user/<int:user_id>")
def get_user(user_id):
    """
    Gets a user by their user ID.

    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: The ID of the user to retrieve.
    responses:
      200:
        description: User retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID.
                user_name:
                  type: string
                  description: The user's username.
                full_name:
                  type: string
                  description: The user's full name.
                github_id:
                  type: string
                  description: (Optional) The user's GitHub ID.
                orcid_id:
                  type: string
                  description: (Optional) The user's ORCID ID.
                openaire_id:
                  type: string
                  description: (Optional) The user's OpenAIRE ID.
                affiliation:
                  type: string
                  description: (Optional) The user's affiliation.
                date_joined:
                  type: string
                  description: The date the user joined (formatted as ISO 8601 string).
                email:
                  type: string
                  description: The user's email address.
                avator:
                  type: string
                  description: The user's avator.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
    """
    user = UserAccount.query.get(user_id)
    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Consider security implications before returning all user data
    # You might want to filter sensitive fields like email
    return jsonify(user.serialize())

@auth_bp.route("/user/id/<int:user_id>", methods=["GET"])
def get_user_by_user_id(user_id):
    """
    Gets a user by their user ID.

    ---
    tags:
      - Users
    parameters:
      - name: user_id
        in: path
        required: true
        type: integer
        description: The user ID of the user to retrieve.
    responses:
      200:
        description: User retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID.
                user_name:
                  type: string
                  description: The user's username.
                full_name:
                  type: string
                  description: The user's full name.
                social_id:
                  type: string
                  description: The user's social ID.
                type:
                  type: string
                  description: The type of account (e.g., google, orcid, email).
                affiliation:
                  type: string
                  description: (Optional) The user's affiliation.
                date_joined:
                  type: string
                  description: The date the user joined (formatted as ISO 8601 string).
                email:
                  type: string
                  description: The user's email address.
                avator:
                  type: string
                  description: The user's avatar URL.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
    """
    user = UserAccount.query.filter_by(user_id=user_id).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Return user information
    return jsonify({
        "user_id": user.user_id,
        "user_name": user.user_name,
        "full_name": user.full_name,
        "social_id": user.social_id,
        "type": user.type,
        "affiliation": user.affiliation,
        "date_joined": user.date_joined.isoformat(),
        "email": user.email,
        "avator": user.avator
    }), 200

@auth_bp.route("/user/username/<string:user_name>", methods=["GET"])
def get_user_by_username(user_name):
    """
    Gets a user by their username.

    ---
    tags:
      - Users
    parameters:
      - name: user_name
        in: path
        required: true
        type: string
        description: The username of the user to retrieve.
    responses:
      200:
        description: User retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID.
                user_name:
                  type: string
                  description: The user's username.
                full_name:
                  type: string
                  description: The user's full name.
                social_id:
                  type: string
                  description: The user's social ID.
                type:
                  type: string
                  description: The type of account (e.g., google, orcid, email).
                affiliation:
                  type: string
                  description: (Optional) The user's affiliation.
                date_joined:
                  type: string
                  description: The date the user joined (formatted as ISO 8601 string).
                email:
                  type: string
                  description: The user's email address.
                avator:
                  type: string
                  description: The user's avatar URL.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
    """
    user = UserAccount.query.filter_by(user_name=user_name).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Return user information
    return jsonify({
        "user_id": user.user_id,
        "user_name": user.user_name,
        "full_name": user.full_name,
        "social_id": user.social_id,
        "type": user.type,
        "affiliation": user.affiliation,
        "date_joined": user.date_joined.isoformat(),
        "email": user.email,
        "avator": user.avator
    }), 200

@auth_bp.route("/user/email/<string:email>", methods=["GET"])
def get_user_by_email(email):
    """
    Gets a user by their email address.

    ---
    tags:
      - Users
    parameters:
      - name: email
        in: path
        required: true
        type: string
        description: The email address of the user to retrieve.
    responses:
      200:
        description: User retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID.
                user_name:
                  type: string
                  description: The user's username.
                full_name:
                  type: string
                  description: The user's full name.
                social_id:
                  type: string
                  description: (Optional) The user's social ID.
                type:
                  type: string
                  description: The type of account (e.g., google, orcid, email).
                affiliation:
                  type: string
                  description: (Optional) The user's affiliation.
                date_joined:
                  type: string
                  description: The date the user joined (formatted as ISO 8601 string).
                email:
                  type: string
                  description: The user's email address.
                avator:
                  type: string
                  description: The user's avatar URL.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
      400:
        description: Invalid email format
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
    """
    
    # Check for valid email format (basic check)
    if not "@" in email or not "." in email.split("@")[-1]:
        return jsonify({"message": "Invalid email format"}), 400

    user = UserAccount.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Return user information with only fields from the model
    return jsonify({
        "user_id": user.user_id,
        "user_name": user.user_name,
        "full_name": user.full_name,
        "social_id": user.social_id,
        "type": user.type,
        "affiliation": user.affiliation,
        "date_joined": user.date_joined.isoformat(),
        "email": user.email,
        "avator": user.avator
    }), 200

@auth_bp.route("/user/social/<string:social_id>", methods=["GET"])
def get_user_by_social_id(social_id):
    """
    Gets a user by their social ID.

    ---
    tags:
      - Users
    parameters:
      - name: social_id
        in: path
        required: true
        type: string
        description: The social ID of the user to retrieve.
    responses:
      200:
        description: User retrieved successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: integer
                  description: The user's ID.
                user_name:
                  type: string
                  description: The user's username.
                full_name:
                  type: string
                  description: The user's full name.
                social_id:
                  type: string
                  description: The user's social ID.
                type:
                  type: string
                  description: The type of account (e.g., google, orcid, email).
                affiliation:
                  type: string
                  description: (Optional) The user's affiliation.
                date_joined:
                  type: string
                  description: The date the user joined (formatted as ISO 8601 string).
                email:
                  type: string
                  description: The user's email address.
                avator:
                  type: string
                  description: The user's avatar URL.
      404:
        description: User not found
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message
    """
    user = UserAccount.query.filter_by(social_id=social_id).first()

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Return user information
    return jsonify({
        "user_id": user.user_id,
        "user_name": user.user_name,
        "full_name": user.full_name,
        "social_id": user.social_id,
        "type": user.type,
        "affiliation": user.affiliation,
        "date_joined": user.date_joined.isoformat(),
        "email": user.email,
        "avator": user.avator
    }), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Logs in a user with email and password.

    This endpoint authenticates a user by verifying their email and password. If the credentials are valid, a JWT token is generated for the session.

    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: body
        required: true
        schema:
          type: string
          description: The email address of the user.
          example: "user@example.com"
      - name: password
        in: body
        required: true
        schema:
          type: string
          description: The user's password.
          example: "password123"
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                description: The email address of the user.
                example: "user@example.com"
              password:
                type: string
                description: The user's password.
                example: "password123"
    responses:
      200:
        description: Login successful
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Indicates if login was successful.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "Login successful"
                token:
                  type: string
                  description: The JWT token for user authentication.
                user_id:
                  type: integer
                  description: The user's unique identifier.
                  example: 1
                user_name:
                  type: string
                  description: The user's username.
                  example: "johndoe"
                full_name:
                  type: string
                  description: The user's full name.
                  example: "John Doe"
                email:
                  type: string
                  description: The user's email.
                  example: "user@example.com"
                avator:
                  type: string
                  description: The URL of the user's profile avator.
                  example: "https://example.com/avatar.jpg"
      401:
        description: Unauthorized - Invalid email or password.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Indicates if login was unsuccessful.
                  example: false
                message:
                  type: string
                  description: Error message.
                  example: "Invalid email or password."
      400:
        description: Bad Request - Missing required fields.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message explaining missing fields.
                  example: "Missing required fields: email, password."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
                  example: "An error occurred during login."
    """
    try:
        data = request.json
        user_email = data.get("email")
        user_password = data.get("password")

        if not user_email or not user_password:
            logger.warning("Login failed: Missing email or password")
            return jsonify({'message': 'Missing required fields: email, password'}), 400

        # Log login attempt
        logger.info(f"Login attempt for email: {user_email}")

        # Find user by email
        user = UserAccount.query.filter_by(email=user_email).first()

        # Verify password
        if user and check_password_hash(user.password, user_password):
            # Generate access and refresh tokens
            access_token = create_access_token(identity=user.user_id)
            refresh_token = create_refresh_token(identity=user.user_id)

            # Set session details
            session["user_id"] = user.user_id
            session["user_name"] = user.user_name
            session["full_name"] = user.full_name
            session["email"] = user.email

            # Log successful login
            logger.info(f"Login successful for user: {user_email}")

            # Return successful login with user data and tokens
            return jsonify({
                'status': True,
                'message': 'Login successful',
                'token': access_token,
                'refresh_token': refresh_token,
                'user_id': user.user_id,
                'user_name': user.user_name,
                'full_name': user.full_name,
                'email': user.email,
                'avator': user.avator
            }), 200

        else:
            logger.warning(f"Login failed: Invalid credentials for email {user_email}")
            return jsonify({'status': False, 'message': 'Invalid email or password.'}), 401

    except Exception as e:
        logger.error(f"An error occurred during login: {str(e)}", exc_info=True)
        return jsonify({'message': f"An error occurred during login: {str(e)}"}), 500

@auth_bp.route("/social_auth", methods=["POST"])
def social_auth():
    
    """
    Social Authentication or Registration via Social ID.

    This endpoint allows for initial registration or login using a social authentication provider like Google or Facebook.

    ---
    tags:
      - Authentication
    parameters:
      - name: social_id
        in: query
        required: true
        schema:
          type: string
        description: The unique ID provided by the social authentication provider.
      - name: type
        in: query
        required: true
        schema:
          type: string
        description: The type of social provider (e.g., google, facebook).
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              social_id:
                type: string
                description: The unique social ID of the user.
                example: "1234567890"
              type:
                type: string
                description: The type of social provider (e.g., google, facebook).
                example: "google"
              name:
                type: string
                description: The full name of the user from the social provider.
                example: "John Doe"
              email:
                type: string
                description: The email address from the social provider.
                example: "johndoe@example.com"
              avator:
                type: string
                description: The user's profile avator URL from the social provider.
                example: "https://example.com/profile.jpg"
              timestamp:
                type: string
                description: The timestamp of the authentication event in ISO format.
                example: "2024-10-08T12:34:56Z"
              username:
                type: string
                description: The desired username.
                example: "johndoe"
              affiliation:
                type: string
                description: The user's affiliation, if available.
                example: "ABC Company"
              password:
                type: string
                description: The password (optional for social logins).
                example: "secureTokenPassword123"
    responses:
      200:
        description: User authenticated or registered successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Indicates if the request was successful.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "User logged in successfully."
                user_data:
                  type: object
                  description: User information.
                  properties:
                    user_id:
                      type: integer
                      description: Unique identifier for the user.
                      example: 1
                    user_name:
                      type: string
                      description: Username.
                      example: "johndoe"
                    full_name:
                      type: string
                      description: Full name of the user.
                      example: "John Doe"
                    email:
                      type: string
                      description: User's email address.
                      example: "johndoe@example.com"
                    avator:
                      type: string
                      description: URL of the user's profile avator.
                      example: "https://example.com/profile.jpg"
      400:
        description: Missing required fields or user already exists.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message.
                  example: "User already exists."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "Failed to authenticate user due to server error."
    """
    
    try:
        data = request.get_json()
        social_id = data.get("social_id")
        account_type = data.get("type")
        name = data.get("name")
        email = data.get("email")
        avator = data.get("avator", "https://example.com/default-avatar.jpg")
        username = data.get("username", "")
        affiliation = data.get("affiliation", "")
        password = data.get("password", None)

        if not social_id:
            logger.warning("Social authentication failed: Missing social_id.")
            return jsonify({'error': 'social_id is required.'}), 400

        # ✅ Convert social_id to string to avoid PostgreSQL type errors
        social_id = str(social_id)

        logger.info(f"Checking existing user with social_id: {social_id}")

        existing_user = UserAccount.query.filter_by(social_id=social_id).first()

        if existing_user:
            logger.info(f"User already exists: social_id={social_id}, user_id={existing_user.user_id}")
            access_token = create_access_token(identity=existing_user.user_id)
            refresh_token = create_refresh_token(identity=existing_user.user_id)
            return jsonify({
                'status': True,
                'message': 'User logged in successfully',
                'token': access_token,
                'refresh_token': refresh_token,
                'user_data': existing_user.serialize()
            }), 200

        # ✅ Register new user
        hashed_password = generate_password_hash(password) if password else None
        new_user = UserAccount(
            user_name=username,
            full_name=name,
            email=email,
            social_id=social_id,  # Ensure it's a string
            type=account_type,
            affiliation=affiliation,
            avator=avator,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        logger.info(f"New user registered successfully: social_id={social_id}, user_id={new_user.user_id}")

        access_token = create_access_token(identity=new_user.user_id)
        refresh_token = create_refresh_token(identity=new_user.user_id)
        return jsonify({
            'status': True,
            'message': 'User registered and logged in successfully',
            'token': access_token,
            'refresh_token': refresh_token,
            'user_data': new_user.serialize()
        }), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error during registration: {str(e.orig)}", exc_info=True)
        return jsonify({'error': 'Database error occurred.', 'details': str(e.orig)}), 400
    except Exception as e:
        logger.exception("Unexpected error during social authentication")
        return jsonify({'error': f'Failed to authenticate user: {str(e)}'}), 500
      
      
@auth_bp.route("/request-password-reset", methods=["POST"])
def request_password_reset():
    """
    Request Password Reset.

    This endpoint initiates a password reset request by generating a reset token and saving it with an expiration date.

    ---
    tags:
      - Authentication
    parameters:
      - name: email
        in: query
        required: true
        schema:
          type: string
        description: The email address of the user requesting the password reset.
        example: "user@example.com"
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              email:
                type: string
                description: The user's email address for the password reset request.
                example: "user@example.com"
    responses:
      200:
        description: Password reset request generated successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Status of the request.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "Password reset email sent successfully."
                token:
                  type: string
                  description: The generated reset token (for testing; typically sent via email in production).
                  example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      400:
        description: Missing or invalid email address, or a reset request already exists.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "A password reset request already exists for this email."
      404:
        description: User not found.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "User not found."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "Failed to create password reset request due to server error."
    """
      
    try:
        data = request.get_json()
        email = data.get("email")
        token = data.get("token")
        expires_at = data.get("expiresAt")

        # ✅ Log incoming request
        logger.info(f"Password reset request received for email: {email}")

        # ✅ Check for required fields
        if not email:
            logger.warning("Password reset request failed: Missing email.")
            return jsonify({'error': 'Email is required.'}), 400

        if not token:
            logger.warning(f"Password reset request failed for {email}: Missing token.")
            return jsonify({'error': 'Token is required.'}), 400

        if not expires_at:
            logger.warning(f"Password reset request failed for {email}: Missing expiresAt.")
            return jsonify({'error': 'expiresAt is required.'}), 400

        # ✅ Validate expiration timestamp
        try:
            expiration_datetime = datetime.fromisoformat(expires_at)
        except ValueError:
            logger.warning(f"Invalid expiresAt format for {email}: {expires_at}")
            return jsonify({'error': 'Invalid expiresAt format. Use ISO 8601 (e.g., "2025-01-19T12:00:00Z").'}), 400

        if expiration_datetime <= datetime.utcnow():
            logger.warning(f"Password reset request failed for {email}: Expiration time must be in the future.")
            return jsonify({'error': 'Expiration time must be in the future.'}), 400

        # ✅ Check if the user exists
        user = UserAccount.query.filter_by(email=email).first()
        if not user:
            logger.warning(f"Password reset request failed: User not found ({email}).")
            return jsonify({"error": "User not found."}), 404

        # ✅ Check for an existing reset request and remove it
        existing_request = PasswordResets.query.filter_by(email=email).first()
        if existing_request:
            db.session.delete(existing_request)
            db.session.commit()  # Commit the deletion
            logger.info(f"Old password reset request removed for {email}.")

        # ✅ Save the new password reset request
        password_reset_entry = PasswordResets(
            email=email,
            token=token,
            type="password_reset",
            expires_at=expiration_datetime
        )

        db.session.add(password_reset_entry)
        db.session.commit()
        logger.info(f"Password reset request successfully created for {email}.")

        # ✅ Return success response
        return jsonify({
            'status': True,
            'message': 'Password reset email sent successfully.',
            'data': password_reset_entry.serialize(),
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error occurred for {email}: {str(e.orig)}", exc_info=True)
        return jsonify({'error': 'Database error occurred.', 'details': str(e.orig)}), 400
    except Exception as e:
        logger.error(f"Unexpected error during password reset request for {email}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to create password reset request: {str(e)}'}), 500
      

@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    """
    Reset Password.

    This endpoint resets a user's password using a provided token and new password.

    ---
    tags:
      - Authentication
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              token:
                type: string
                description: The reset token.
                example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
              password:
                type: string
                description: The new password for the user.
                example: "NewSecurePassword123"
    responses:
      200:
        description: Password reset successful.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Status of the password reset request.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "Password has been reset successfully."
      400:
        description: Invalid token, or token has expired.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message explaining the issue.
                  example: "Invalid or expired token."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                error:
                  type: string
                  description: Error message.
                  example: "Failed to reset password due to server error."
    """
      
    try:
        data = request.get_json()
        token = data.get("token")
        new_password = data.get("password")

        # ✅ Log incoming request
        logger.info(f"Received password reset request with token: {token}")

        # ✅ Check for required fields
        if not token or not new_password:
            logger.warning(f"Password reset failed: Missing required fields.")
            return jsonify({'error': 'Token and password are required.'}), 400

        # ✅ Validate the reset token
        reset_entry = PasswordResets.query.filter_by(token=token).first()
        if not reset_entry:
            logger.warning(f"Password reset failed: Invalid token ({token}).")
            return jsonify({'error': 'Invalid token.'}), 400

        # ✅ Check if the token has expired
        if reset_entry.expires_at < datetime.utcnow():
            logger.warning(f"Password reset failed: Token expired ({token}).")
            return jsonify({'error': 'Token expired.'}), 400

        # ✅ Retrieve the user account based on the reset request email
        user = UserAccount.query.filter_by(email=reset_entry.email).first()
        if not user:
            logger.warning(f"Password reset failed: User not found for token ({token}).")
            return jsonify({'error': 'User not found.'}), 404

        # ✅ Update the user's password (hashed)
        user.password = generate_password_hash(new_password)
        db.session.commit()
        logger.info(f"Password successfully reset for user {user.email}.")

        # ✅ Remove the used token
        db.session.delete(reset_entry)
        db.session.commit()
        logger.info(f"Password reset token {token} deleted.")

        # ✅ Return success response
        return jsonify({
            'status': True,
            'message': 'Password has been reset successfully.'
        }), 200

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database error occurred while resetting password for token {token}: {str(e.orig)}", exc_info=True)
        return jsonify({'error': 'Database error occurred.', 'details': str(e.orig)}), 400
    except Exception as e:
        logger.error(f"Unexpected error during password reset for token {token}: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to reset password: {str(e)}'}), 500
      

@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    """
    Logs out the authenticated user.

    This endpoint logs out the current user by clearing their session.

    ---
    tags:
      - Authentication
    parameters:
      - name: Authorization
        in: header
        required: true
        schema:
          type: string
          format: bearer
          example: "Bearer <JWT token>"
        description: The Bearer token for authorization (JWT token).
    responses:
      200:
        description: User logged out successfully.
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: boolean
                  description: Indicates if the logout was successful.
                  example: true
                message:
                  type: string
                  description: Success message.
                  example: "User logged out successfully."
      401:
        description: Unauthorized - User is not authenticated or token is invalid.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
                  example: "Invalid token or user not authenticated."
      500:
        description: Internal server error.
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  description: Error message.
                  example: "An error occurred during logout."
    """
    try:
        # Clear user session data
        session.clear()
        return jsonify({
            'status': True,
            'message': 'User logged out successfully.'
        }), 200

    except Exception as e:
        return jsonify({'message': f"An error occurred during logout: {str(e)}"}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using a valid refresh token.
    ---
    tags:
      - Authentication
    security:
      - bearerAuth: []
    responses:
      200:
        description: New access token generated successfully
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  description: New JWT access token
                  example: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      401:
        description: Invalid or expired refresh token
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "Invalid or expired refresh token"
      500:
        description: Server error
        content:
          application/json:
            schema:
              type: object
              properties:
                message:
                  type: string
                  example: "An error occurred while refreshing token"
    """
    try:
        current_user_id = get_jwt_identity()
        logger.info(f"Refreshing token for user_id: {current_user_id}")

        # Generate new access token
        new_access_token = create_access_token(identity=current_user_id)

        return jsonify({
            'access_token': new_access_token
        }), 200

    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}", exc_info=True)
        return jsonify({'message': f"An error occurred while refreshing token: {str(e)}"}), 500
