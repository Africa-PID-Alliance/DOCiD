# app/routes/datacite.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import DocIdLookup
from app.service_doi import get_datacite_doi
from xml.etree import ElementTree as ET
from sqlalchemy.sql import func
from flasgger import swag_from

datacite_bp = Blueprint("datacite", __name__, url_prefix="/api/v1/datacite")

@datacite_bp.route('/get-doi', methods=['GET'])
def datacite_doi():
    """
    Fetches a DataCite DOI.
    ---
    tags:
      - DataCite
    responses:
      200:
        description: DataCite DOI retrieved successfully
        content:
          application/json:
            schema:
              type: object
              # Adjust the schema properties based on the actual response structure
              # (e.g., 'doi': { type: string })
    """

    response = get_datacite_doi()
    return response
