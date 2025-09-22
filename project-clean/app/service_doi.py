# app/service_doi.py
import requests
from flask import (
    Blueprint,
    jsonify,
)

def get_datacite_doi():
    """
        Get DataCite DOI from DataCite API.
    """
    try:
        url = (
            "https://api.test.datacite.org/dois?client_id=datacite.datacite&random=true"
        )
        headers = {"Content-Type": "application/json"}
        repository_id, password = "FPAV", "Tremis#123$"
        response = requests.get(
            url=url,
            headers=headers,
            auth=(repository_id, password),
        )
        response.raise_for_status()
        data = response.json()
        doi = data["data"][0]["id"]

        return jsonify({"doi": doi})

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch datacite DOI: {str(e)}"}), 500
