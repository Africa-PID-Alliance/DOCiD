# app/routes/doi.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import DocIdLookup
from app.service_doi import get_datacite_doi
from xml.etree import ElementTree as ET
from sqlalchemy.sql import func
from flasgger import swag_from

docid_bp = Blueprint("docid", __name__, url_prefix="/api/v1/docid")

@docid_bp.route("/get-doi", methods=["GET"])
def get_docid():

    """
    Get DocID
    ---
    tags:
      - DocID
    responses:
      200:
        description: Get docid DOI as json
        schema:
          type: array
          items:
            type: string
      400:
        description: Error generating docid DOI (e.g., invalid request data)
      500:
        description: Internal server error
    """
    try:
        random_docid_pid = (
            db.session.query(DocIdLookup).order_by(func.random()).first()
        )
        return jsonify({"docid_doi": random_docid_pid.pid[:7]})
        # else:
        #     return jsonify({"error": "No random DocID DOI found"})
    except Exception as e:
        return jsonify({"error": "Failed to fetch DocID DOI: " + str(e)})
