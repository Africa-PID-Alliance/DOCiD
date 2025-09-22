# app/routes/crossref.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import DocIdLookup,CrossrefMetadata
from app.service_crossref import deposit_metadata
from sqlalchemy.sql import func
from habanero import Crossref
import logging

# Initialize logger
logging.basicConfig(level=logging.ERROR)

"""Retrieves DOI information from Crossref API based on provided data.

    Crossref - Crossref search API.

    works - /works route
    members - /members route
    prefixes - /prefixes route
    funders - /funders route
    journals - /journals route
    types - /types route
    licenses - /licenses route

    Expects JSON doi in the request get
        - 'doi': A single DOI string e.g oi=10.1016/8756-3282(95)91695-4
    Returns a JSON response with the following structure:
        - 'status': string indicating success (status) or failure (False)
        - 'message': Success/error message
        - 'doi' (optional): Retrieved DOI (if successful)
    """

crossref_bp = Blueprint("crossref", __name__, url_prefix="/api/v1/crossref")
@crossref_bp.route('/doi/', methods=['GET'])
def get_doi_info():
    """
    Fetches metadata for a DOI from the Crossref API.

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve metadata for.
    responses:
      200:
        description: DOI metadata from Crossref API
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Status of the request
                data:
                  type: object
                  description: Retrieved DOI metadata
      400:
        description: Missing DOI parameter or error retrieving metadata from Crossref API
    """
    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
        # Initialize Crossref client
        cr = Crossref()
        # Fetch works by DOI
        works = cr.works(ids=doi)

        # Extracting specific data points
        data = {
            'doi': doi,
            'title': works['message'].get('title', [None])[0],
            'authors': [f"{a['given']} {a['family']}" for a in works['message'].get('author', [])],
            'publisher': works['message'].get('publisher', 'Unknown'),
            'published_date': works['message'].get('published-print', {}).get('date-parts', [[None]])[0]
        }
        # Save metadata to the database
        save_metadata(doi, data)
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        logging.error(f"Error retrieving works by DOI {doi}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
      
      

@crossref_bp.route('/cached-doi/', methods=['GET'])
# Example of a caching decorator using Flask-Caching
def get_cached_doi_info():
    """
    Fetches cached metadata for a DOI, or retrieves from Crossref API if not cached.

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve metadata for.
    responses:
      200:
        description: DOI metadata from cache or Crossref API
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Status of the request
                data:
                  type: object
                  description: Retrieved DOI metadata
      400:
        description: Missing DOI parameter or error retrieving metadata from Crossref API
    """
    doi = request.args.get('doi')
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
        # Check if DOI metadata is cached
        cached_entry = db.session.query(CrossrefMetadata).filter_by(doi=doi).first()
        if cached_entry:
            return jsonify({'status': 'success','from':'cache', 'data': cached_entry.to_dict()}), 200
        # If not cached, fetch from Crossref
        cr = Crossref()
        # Fetch works by DOI
        works = cr.works(ids=doi)
        # Fetch funders, journals, types, and licenses
        funders = cr.funders(ids=doi)
        journals = cr.journals(ids=doi)
        types = cr.types(ids=doi)
        licenses = cr.licenses(ids=doi)

        # Extracting specific data points
        data = {
            'doi': doi,
            'title': works['message'].get('title', [None])[0],
            'authors': [f"{a['given']} {a['family']}" for a in works['message'].get('author', [])],
            'publisher': works['message'].get('publisher', 'Unknown'),
            'funders': funders.get('message', {}).get('items', []),
            'journals': journals.get('message', {}).get('items', []),
            'types': types.get('message', {}).get('items', []),
            'licenses': licenses.get('message', {}).get('items', [])
        }
        # Save metadata to the database
        save_metadata(doi, data)
        return jsonify({'status': 'success','from':'api' ,'data': data}), 200
    except Exception as e:
        logging.error(f"Error retrieving works by DOI {doi}: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400
      
      
def save_metadata(doi, metadata):
    existing_entry = db.session.query(CrossrefMetadata).filter_by(doi=doi).first()
    if existing_entry:
        # Update existing entry if necessary
        existing_entry.title = metadata['title']
        existing_entry.authors = ', '.join(metadata['authors'])
        existing_entry.publisher = metadata['publisher']
        db.session.commit()
    else:
        new_entry = CrossrefMetadata(
            doi=doi,
            title=metadata['title'],
            authors=', '.join(metadata['authors']),
            publisher=metadata['publisher']
        )
        db.session.add(new_entry)
        db.session.commit()

@crossref_bp.route('/bulk/', methods=['POST'])
def get_bulk_doi_info():
    """
    Fetches metadata for multiple DOIs from the Crossref API.

    ---
    tags:
      - Crossref
    parameters:
      - in: body
        name: body
        required: true
        description: JSON object containing a list of DOIs.
        schema:
          type: object
          properties:
            dois:
              type: array
              items:
                type: string
                description: A list of DOIs to retrieve metadata for.
    responses:
      200:
        description: Metadata for multiple DOIs from Crossref API
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Status of the request
                data:
                  type: array
                  description: List of retrieved DOI metadata
      400:
        description: No DOIs provided or error retrieving metadata from Crossref API
    """
    doi_list = request.json.get('dois', [])
    if not doi_list:
        return jsonify({'error': 'No DOIs provided'}), 400

    try:
        cr = Crossref()
        results = []
        for doi in doi_list:
            works = cr.works(ids=doi)
            results.append({
                'doi': doi,
                'title': works['message'].get('title', [None])[0],
                'authors': [f"{a['given']} {a['family']}" for a in works['message'].get('author', [])],
                'publisher': works['message'].get('publisher', 'Unknown')
            })
            # Save metadata to the database
            save_metadata(doi, results[-1])
        return jsonify({'status': 'success', 'data': results}), 200
    except Exception as e:
        logging.error(f"Error retrieving works for DOIs: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


@crossref_bp.route('/search/', methods=['GET'])
def search_works():
    """
    Searches works using the Crossref API based on a query.

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: query
        type: string
        required: true
        description: The search query to find works in Crossref.
    responses:
      200:
        description: Search results from Crossref API
        content:
          application/json:
            schema:
              type: object
              properties:
                status:
                  type: string
                  description: Status of the request
                data:
                  type: array
                  description: List of search results
      400:
        description: Missing search query or error searching works in Crossref API
    """
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'Missing search query'}), 400

    try:
        cr = Crossref()
        results = cr.works(query=query)
        return jsonify({'status': 'success', 'data': results['message']['items']}), 200
    except Exception as e:
        logging.error(f"Error searching works: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@crossref_bp.route('/works/',methods=['GET'])
def get_doi_works():

    """
    Fetches DOI works from Crossref API

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve works metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
     # Initialize Crossref client
     cr = Crossref()
     works = cr.works(ids= doi)
     return works
    except Exception as e:
        # Catch any exceptions (including potential 500 errors)
         return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

@crossref_bp.route('/members/',methods=['GET'])
def get_doi_members():

    """
    Fetches DOI members from Crossref API

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve members metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
     # Initialize Crossref client
        cr = Crossref()
        members = cr.members(ids= doi)
        return members
    except Exception as e:
        # Catch any exceptions (including potential 500 errors)
         return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

@crossref_bp.route('/funders/',methods=['GET'])
def get_doi_funders():

    """
    Fetches DOI funders from Crossref API

    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve funders metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400
    try:
     # Initialize Crossref client
        cr = Crossref()
        funders = cr.funders(ids= doi)
        return funders
    except Exception as e:
        # Catch any exceptions (including potential 500 errors)
         return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

"""
http://127.0.0.1:5001//api/v1/crossref/journals/?doi=10.1016/8756-3282(95)91695-4
"""
@crossref_bp.route('/journals/',methods=['GET'])
def get_doi_journals():

    """
    Fetches DOI journals from Crossref API
    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to retrieve journals metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
        # Initialize Crossref client
        cr = Crossref()
        journals = cr.journals(ids= doi)
        return journals
    except Exception as e:
     # Catch any exceptions (including potential 500 errors)
     return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

@crossref_bp.route('/types/',methods=['GET'])
def get_doi_types():

    """
    Fetches DOI types from Crossref API
    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to  retrieve types metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
        # Initialize Crossref client
        cr = Crossref()
        types = cr.types(ids= doi)
        return types
    except Exception as e:
     # Catch any exceptions (including potential 500 errors)
     return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

@crossref_bp.route('/licenses/',methods=['GET'])
def get_doi_licenses():

    """
    Fetches DOI licenses from Crossref API
    ---
    tags:
      - Crossref
    parameters:
      - in: query
        name: doi
        type: string
        required: true
        description: The Digital Object Identifier (DOI) to  retrieve licenses metadata for.
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
    """

    doi = request.args.get('doi')  # Get DOI from query string
    if not doi:
        return jsonify({'error': 'Missing DOI parameter'}), 400

    try:
        # Initialize Crossref client
        cr = Crossref()
        licenses = cr.licenses(ids= doi)
        return licenses
    except Exception as e:
        # Catch any exceptions (including potential 500 errors)
        return jsonify({'error':  f"Error retrieving works by DOI {doi}: {e}" }), 400

@crossref_bp.route('/submit-crossref-xml',methods=['GET'])
def do_submit_crossref_xml():
  
  """
    submit-crossref-xml
    ---
    tags:
      - Crossref
    responses:
      200:
        description: Fetches DOI metadata from Crossref API
        schema:
          type: array
          items:
            type: string
  """
  
  try:
          
    # Example metadata for  report
    # metadata = {
    #       "depositor_name": "Crossref",
    #       "email_address": "test@africapidalliance.org",
    #       "title": "Example Title",
    #       "doi": "10.1234/example.doi",
    #       "resource_url": "https://docid.africapidalliance.org/resource",
    #       "grant_metadata": "Grant information",
    #       "dataset_metadata": "Dataset information",
    #       "book_metadata": "Book metadata",
    #       "dissertation_metadata": "Dissertation metadata",
    #       "conference_metadata": "Conference metadata"
    # }
      
    metadata_journal_article = {
      'depositor_name': 'Example Depositor',
      'email_address': 'depositor@africapidalliance.org',
      'registrant': 'Example Journal',
      'journal_full_title': 'Journal of Crossref Test Data',
      'journal_issn': '1942-4027',
      'title': 'This is a journal article title',
      'doi': '10.5555/n0HRokm',
      'resource_url': 'https://www.crossref.org/xml-samples',
      'authors': [
          {'sequence': 'first', 'given_name': 'Minerva', 'surname': 'Housecat', 'orcid': 'https://orcid.org/0000-0002-4011-3590'},
          {'sequence': 'additional', 'given_name': 'Josiah', 'surname': 'Carberry', 'orcid': 'https://orcid.org/0000-0002-1825-0097'}
      ]
    }

    response = deposit_metadata(metadata_journal_article, 'journal_article', 'info@africapidalliance.org/apida_test', 'Dd01~2o24')

    return response
  
  except Exception as e:
      # Catch any exceptions (including potential 500 errors)
      return jsonify({'error':  f"Error depositing crossref  xml: {e}" }), 400
