from flask import Blueprint, jsonify, request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging
import re
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta
import time

# https://api.demo.raid.org.au/swagger-ui/index.html#/

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('raid_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Blueprint definition
raid_bp = Blueprint("raid", __name__, url_prefix="/api/v1/raid")

# Configuration constants
import os
from dotenv import load_dotenv

load_dotenv()

RAID_CONFIG = {
    'API_URL': os.getenv('RAID_API_URL', "https://api.demo.raid.org.au/raid/"),
    'TOKEN_URL': os.getenv('RAID_TOKEN_URL', "https://iam.demo.raid.org.au/realms/raid/protocol/openid-connect/token"),
    'GRANT_TYPE': os.getenv('RAID_GRANT_TYPE', "password"),
    'CLIENT_ID': os.getenv('RAID_CLIENT_ID'),
    'CLIENT_SECRET': os.getenv('RAID_CLIENT_SECRET'),
    'USERNAME': os.getenv('RAID_USERNAME'),
    'PASSWORD': os.getenv('RAID_PASSWORD')
}

class TokenManager:
    """
    Manages access tokens for the RAiD API.

    Methods:
        - is_token_valid: Checks if the current token is valid and not expired.
        - update_token: Updates the token and expiry time.
        - get_token: Returns the current valid token if available.
    """
    def __init__(self):
        self.access_token = None
        self.token_expiry = None

    def is_token_valid(self) -> bool:
        """
        Check if the current token is valid and not expired.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self.access_token or not self.token_expiry:
            return False
        return datetime.now() < self.token_expiry - timedelta(minutes=5)

    def update_token(self, token_data: Dict):
        """
        Update the access token and its expiry time.

        Args:
            token_data (Dict): The token data from the API response.
        """
        self.access_token = token_data['access_token']
        self.token_expiry = datetime.now() + timedelta(seconds=token_data['expires_in'])
        logger.info("Token updated successfully")

    def get_token(self) -> Optional[str]:
        """
        Get the current valid token if available.

        Returns:
            str: The current valid token or None.
        """
        return self.access_token if self.is_token_valid() else None

# Create global token manager instance
token_manager = TokenManager()

RAID_PATTERNS = {
    'prefix': re.compile(r'^10\.\d{4,}$'),
    'suffix': re.compile(r'^[a-zA-Z0-9\-_]{1,30}$')
}

class RAIDValidationError(Exception):
    """Custom exception for RAID validation errors."""
    pass

def validate_raid_identifier(prefix: str, suffix: str) -> bool:
    """
    Validates the RAID identifier format.

    Args:
        prefix (str): The RAID prefix (e.g., "10.1234").
        suffix (str): The RAID suffix (e.g., "abcd1234").

    Returns:
        bool: True if valid.

    Raises:
        RAIDValidationError: If the prefix or suffix is invalid.
    """
    if not RAID_PATTERNS['prefix'].match(prefix):
        raise RAIDValidationError(f"Invalid RAID prefix format: {prefix}")
    if not RAID_PATTERNS['suffix'].match(suffix):
        raise RAIDValidationError(f"Invalid RAID suffix format: {suffix}")
    return True

def fetch_new_token() -> Optional[str]:
    """
    Fetch a new access token from the RAiD API.

    Returns:
        str: The new access token or None if the request fails.
    """
    try:
        data = {
            'grant_type': RAID_CONFIG['GRANT_TYPE'],
            'client_id': RAID_CONFIG['CLIENT_ID'],
            'client_secret': RAID_CONFIG['CLIENT_SECRET'],
            'username': RAID_CONFIG['USERNAME'],
            'password': RAID_CONFIG['PASSWORD']
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        response = requests.post(
            RAID_CONFIG['TOKEN_URL'],
            headers=headers,
            data=data,
            timeout=10
        )

        if response.status_code == 200:
            token_data = response.json()
            token_manager.update_token(token_data)
            return token_data['access_token']
        else:
            logger.error(f"Token fetch failed with status {response.status_code}: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Token fetch failed: {str(e)}")
        return None

def ensure_valid_token() -> Optional[str]:
    """
    Ensure there is a valid access token, fetching a new one if needed.

    Returns:
        str: The valid access token or None.
    """
    token = token_manager.get_token()
    if not token:
        token = fetch_new_token()
    return token

def log_api_request(func):
    """
    Decorator to log API requests with detailed information.

    Args:
        func (function): The function to wrap.

    Returns:
        function: The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"

        logger.info(f"Request {request_id} started - Endpoint: {request.endpoint}")
        logger.info(f"Request {request_id} params: {request.args}")

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"Request {request_id} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Request {request_id} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

@raid_bp.route('/get-access-token', methods=['POST'])
@limiter.limit("5 per minute")
@log_api_request
def request_raid_token():
    """
    Request a new access token from the RAiD API.

    ---
    tags:
      - RAiD
    responses:
      200:
        description: Successfully retrieved a new access token.
        content:
          application/json:
            schema:
              type: object
              properties:
                access_token:
                  type: string
                  description: The newly generated access token.
      500:
        description: Failed to fetch a new access token.
    """
    token = fetch_new_token()
    if token:
        return jsonify({'access_token': token}), 200
    return jsonify({'error': 'Failed to obtain access token'}), 500
  
  
@raid_bp.route('/get-raid', methods=['GET'])
@limiter.limit("100 per hour")
@log_api_request
def get_raid():
    """
    Retrieve RAID data using the full RAID URL.

    ---
    tags:
      - RAiD
    parameters:
      - name: raid_url
        in: query
        required: true
        schema:
          type: string
          description: The full RAID URL (e.g., "https://app.demo.raid.org.au/raids/10.80368/b1adfb3a").
    responses:
      200:
        description: Successfully retrieved RAID data.
      400:
        description: Invalid RAID identifier or URL.
      403:
        description: Access denied.
      500:
        description: Internal server error.
    """
    try:
        # Get the full RAID URL from query parameters
        raid_url = request.args.get('raid_url')
        if not raid_url:
            return jsonify({'error': 'raid_url parameter is required'}), 400

        # Extract prefix and suffix using regex - handle multiple formats
        import re
        
        # Try different patterns
        patterns = [
            r'/raids/(?P<prefix>\d+\.\d+)/(?P<suffix>[a-zA-Z0-9]+)',  # Original format: /raids/10.123/abc
            r'(?P<prefix>\d+\.\d+)/(?P<suffix>[a-zA-Z0-9]+)/?$',       # Just the identifier: 10.123/abc (with optional trailing slash)
            r'raid\.org\.au/raids/(?P<prefix>\d+\.\d+)/(?P<suffix>[a-zA-Z0-9]+)', # raid.org.au format
            r'raid\.org/(?P<prefix>\d+\.\d+)/(?P<suffix>[a-zA-Z0-9]+)' # raid.org format
        ]
        
        match = None
        for pattern in patterns:
            match = re.search(pattern, raid_url)
            if match:
                break
        
        if not match:
            return jsonify({'error': 'Invalid RAID URL format. Expected formats: 10.12345/abc123, https://raid.org/10.12345/abc123, or https://app.demo.raid.org.au/raids/10.12345/abc123'}), 400

        prefix = match.group('prefix')
        suffix = match.group('suffix')

        # Validate the extracted RAID identifier
        validate_raid_identifier(prefix, suffix)

        # Ensure a valid token
        token = ensure_valid_token()
        if not token:
            return jsonify({'error': 'Failed to obtain valid access token'}), 500

        # Construct API URL and make the request
        api_url = f"{RAID_CONFIG['API_URL']}{prefix}/{suffix}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        logger.info(f"Making request to {api_url}")
        response = requests.get(api_url, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            return jsonify(result), 200
        elif response.status_code == 403:
            return jsonify({'error': 'Access denied - RAID may be closed or embargoed'}), 403
        else:
            return jsonify({'error': response.text}), response.status_code

    except RAIDValidationError as e:
        logger.error(f"RAID validation error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@raid_bp.route('/mint-raid', methods=['POST'])
@limiter.limit("10 per hour")
@log_api_request
def mint_raid():
    """
    Mint a new RAID (Research Activity Identifier).

    ---
    tags:
      - RAiD
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              identifier:
                type: object
                description: Details about the identifier.
              title:
                type: array
                description: Titles associated with the RAID.
              date:
                type: object
                description: Start and end date.
              description:
                type: array
                description: Descriptions associated with the RAID.
              access:
                type: object
                description: Access details including embargo information.
              alternateUrl:
                type: array
                description: Alternate URLs for the RAID.
              contributor:
                type: array
                description: Contributors for the RAID.
              organisation:
                type: array
                description: Organisations associated with the RAID.
              subject:
                type: array
                description: Subjects associated with the RAID.
              relatedRaid:
                type: array
                description: Related RAIDs.
              relatedObject:
                type: array
                description: Related objects.
              alternateIdentifier:
                type: array
                description: Alternate identifiers for the RAID.
              spatialCoverage:
                type: array
                description: Spatial coverage information.
              traditionalKnowledgeLabel:
                type: array
                description: Traditional knowledge labels.
    responses:
      201:
        description: Successfully minted the RAID.
      400:
        description: Invalid request payload.
      500:
        description: Internal server error.
    """
    try:
        # Validate and parse JSON payload
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request body is required'}), 400

        token = ensure_valid_token()
        if not token:
            return jsonify({'error': 'Failed to obtain valid access token'}), 500

        # Prepare request to RAID API
        api_url = RAID_CONFIG['API_URL']
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        response = requests.post(api_url, json=data, headers=headers)

        if response.status_code == 201:
            return jsonify(response.json()), 201
        elif response.status_code == 400:
            return jsonify({'error': response.json()}), 400
        else:
            logger.error(f"Failed to mint RAID: {response.text}")
            return jsonify({'error': 'Failed to mint RAID'}), response.status_code

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
