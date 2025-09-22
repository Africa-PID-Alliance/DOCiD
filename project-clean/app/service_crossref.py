# app/service_crossref.py

import requests
from requests.auth import HTTPBasicAuth
from flask import Blueprint, request, jsonify
from xml.etree import ElementTree as ET
from config import Config
import os
import logging

# Set up logging
logging.basicConfig(level=logging.ERROR)

# Crossref Deposit URL
DEPOSIT_URL = 'https://test.crossref.org/servlet/deposit'

# Common XML namespaces
NAMESPACE = {
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'jats': 'http://www.ncbi.nlm.nih.gov/JATS1',
    'fr': 'http://www.crossref.org/fundref.xsd',
    'mml': 'http://www.w3.org/1998/Math/MathML',
    'xmlns': "http://www.crossref.org/schema/5.3.0"
}

# Configure Crossref API details (replace with your credentials)
CROSSREF_API_URL = os.getenv('CROSSREF_API_URL')
CROSSREF_API_KEY = os.getenv('CROSSREF_API_KEY')

if not CROSSREF_API_URL or not CROSSREF_API_KEY:
    raise ValueError("Crossref API URL or API Key not set in environment variables")

HEADERS = {}
if CROSSREF_API_KEY:
    HEADERS["Authorization"] = f"Bearer {CROSSREF_API_KEY}"
    
def convert_crossref_xml_to_json(xml_string):
    try:
        root = ET.fromstring(xml_string)
        json_data = {}
        body = root.find("body")
        if body is not None:
            message = body.find("message")
            if message is not None:
                doi_element = message.find("doi-body/doi")
                if doi_element is not None:
                    json_data["doi"] = doi_element.text
        else:
            json_data["message"] = "No results found"
        return json_data
    except Exception as e:
        return {"error": f"Error converting XML to JSON: {str(e)}"}


def get_crossref_doi(doi):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "Missing data in request body"}), 400
        doi = data.get("doi")
        if not doi:
            return jsonify({"success": False, "message": "Missing 'doi' field"}), 400

        url = CROSSREF_API_URL + doi
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            xml_string = response.content
            json_data = convert_crossref_xml_to_json(xml_string)
            return jsonify({"success": True, "doi": doi, "metadata": json_data})
        else:
            return jsonify({"success": False, "message": f"Crossref API error: {response.status_code}"}), response.status_code

    except Exception as e:
        logging.error(f"Internal server error: {str(e)}")
        return jsonify({"success": False, "message": f"Internal server error: {str(e)}"}), 500

def deposit_to_crossref(xml_data, username, password):
    files = {
        'operation': (None, 'doMDUpload'),
        'login_id': (None, username),
        'login_passwd': (None, password),
        'fname': ('crossref_submission.xml', xml_data, 'application/xml')
    }

    headers = {
        'Content-Type': 'application/xml',
        'Pragma': 'no-cache'
    }

    try:
        response = requests.post(DEPOSIT_URL, files=files, headers=headers)
        logging.error(f"Response status: {response.status_code}, Response content: {response.text}")

        if response.status_code == 200:
            return jsonify({"status": "success", "message": "XML deposited successfully", "response": response.text})
        else:
            return jsonify({"status": "error", "message": f"Failed to deposit XML: {response.text}", "response": response.text}), response.status_code
    except Exception as e:
        logging.error(f"Exception occurred during deposit: {str(e)}")
        return jsonify({"status": "error", "message": f"Exception occurred: {str(e)}"}), 500


# Function to build XML for Reports and Working Papers
def build_report_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    batch_id = ET.SubElement(head, 'doi_batch_id')
    batch_id.text = 'test_batch_id'
    
    # Other head and depositor info
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']
    ET.SubElement(head, 'registrant').text = metadata['registrant']

    # Body with posted content
    body = ET.SubElement(root, 'body')
    posted_content = ET.SubElement(body, 'posted_content', {'type': 'report'})
    titles = ET.SubElement(posted_content, 'titles')
    ET.SubElement(titles, 'title').text = metadata['title']
    
    doi_data = ET.SubElement(posted_content, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")

# Function to build XML for Preprints (Posted Content)
def build_preprint_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'preprint_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Preprint content
    body = ET.SubElement(root, 'body')
    posted_content = ET.SubElement(body, 'posted_content', {'type': 'preprint'})
    titles = ET.SubElement(posted_content, 'titles')
    ET.SubElement(titles, 'title').text = metadata['title']
    
    doi_data = ET.SubElement(posted_content, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")

# Function to build XML for Peer Reviews
def build_peer_review_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'peer_review_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Peer review content
    body = ET.SubElement(root, 'body')
    peer_review = ET.SubElement(body, 'peer_review')
    ET.SubElement(peer_review, 'peer_review_metadata').text = metadata['review_metadata']
    
    doi_data = ET.SubElement(peer_review, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")

# Function to build XML for Journal Articles
def build_journal_article_xml(metadata):
    
    # Root element
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': NAMESPACE['xmlns'],
        'version': "5.3.0"
    })
  
    # Head element
    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'journal_article_batch'
    ET.SubElement(head, 'timestamp').text = '2021010100000000'  # Example timestamp

    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    ET.SubElement(head, 'registrant').text = metadata['registrant']

    # Body element
    body = ET.SubElement(root, 'body')
    journal = ET.SubElement(body, 'journal')
    
    # Journal metadata
    journal_metadata = ET.SubElement(journal, 'journal_metadata', {'language': 'en'})
    ET.SubElement(journal_metadata, 'full_title').text = metadata['journal_full_title']
    ET.SubElement(journal_metadata, 'issn', {'media_type': 'electronic'}).text = metadata['journal_issn']

    # Journal Article
    journal_article = ET.SubElement(journal, 'journal_article', {'publication_type': 'full_text'})
    
    # Article Titles
    titles = ET.SubElement(journal_article, 'titles')
    ET.SubElement(titles, 'title').text = metadata['title']

    # Contributors (Authors)
    contributors = ET.SubElement(journal_article, 'contributors')
    for author in metadata['authors']:
        person_name = ET.SubElement(contributors, 'person_name', {
            'sequence': author['sequence'],
            'contributor_role': 'author'
        })
        ET.SubElement(person_name, 'given_name').text = author['given_name']
        ET.SubElement(person_name, 'surname').text = author['surname']
        if 'orcid' in author:
            ET.SubElement(person_name, 'ORCID', {'authenticated': 'true'}).text = author['orcid']

    # DOI Data
    doi_data = ET.SubElement(journal_article, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']
    
    # Return the XML string
    return ET.tostring(root, encoding="unicode")


# Function to build XML for Grants
def build_grants_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'grants_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Grant content
    body = ET.SubElement(root, 'body')
    grant = ET.SubElement(body, 'grant')
    ET.SubElement(grant, 'grant_metadata').text = metadata['grant_metadata']
    
    doi_data = ET.SubElement(grant, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")


# Function to build XML for Datasets
def build_datasets_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'dataset_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Dataset content
    body = ET.SubElement(root, 'body')
    dataset = ET.SubElement(body, 'dataset')
    ET.SubElement(dataset, 'dataset_metadata').text = metadata['dataset_metadata']
    
    doi_data = ET.SubElement(dataset, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")


# Function to build XML for Books
def build_books_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'book_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Book content
    body = ET.SubElement(root, 'body')
    book = ET.SubElement(body, 'book')
    ET.SubElement(book, 'book_metadata').text = metadata['book_metadata']
    
    doi_data = ET.SubElement(book, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")


# Function to build XML for Dissertations
def build_dissertation_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'dissertation_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Dissertation content
    body = ET.SubElement(root, 'body')
    dissertation = ET.SubElement(body, 'dissertation')
    ET.SubElement(dissertation, 'dissertation_metadata').text = metadata['dissertation_metadata']
    
    doi_data = ET.SubElement(dissertation, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")


# Function to build XML for Conference Proceedings
def build_conference_xml(metadata):
    root = ET.Element('doi_batch', {
        'xmlns:xsi': NAMESPACE['xsi'],
        'xsi:schemaLocation': "http://www.crossref.org/schema/5.3.0 https://www.crossref.org/schemas/crossref5.3.0.xsd",
        'xmlns': "http://www.crossref.org/schema/5.3.0",
        'version': "5.3.0"
    })

    head = ET.SubElement(root, 'head')
    ET.SubElement(head, 'doi_batch_id').text = 'conference_batch'
    depositor = ET.SubElement(head, 'depositor')
    ET.SubElement(depositor, 'depositor_name').text = metadata['depositor_name']
    ET.SubElement(depositor, 'email_address').text = metadata['email_address']

    # Conference content
    body = ET.SubElement(root, 'body')
    conference = ET.SubElement(body, 'conference_paper')
    ET.SubElement(conference, 'conference_metadata').text = metadata['conference_metadata']
    
    doi_data = ET.SubElement(conference, 'doi_data')
    ET.SubElement(doi_data, 'doi').text = metadata['doi']
    ET.SubElement(doi_data, 'resource').text = metadata['resource_url']

    return ET.tostring(root, encoding="unicode")


# Function to deposit each XML type


# Function to deposit each XML type
def deposit_metadata(metadata, xml_type, username, password):
  
    if xml_type == 'report':
        xml_data = build_report_xml(metadata)
    elif xml_type == 'preprint':
        xml_data = build_preprint_xml(metadata)
    elif xml_type == 'peer_review':
        xml_data = build_peer_review_xml(metadata)
    elif xml_type == 'journal_article':
        xml_data = build_journal_article_xml(metadata)
    elif xml_type == 'grants':
        xml_data = build_grants_xml(metadata)
    elif xml_type == 'datasets':
        xml_data = build_datasets_xml(metadata)
    elif xml_type == 'books':
        xml_data = build_books_xml(metadata)
    elif xml_type == 'dissertation':
        xml_data = build_dissertation_xml(metadata)
    elif xml_type == 'conference':
        xml_data = build_conference_xml(metadata)
    else:
        return jsonify({"status": "error", "message": "Unsupported XML type"})
    
    return deposit_to_crossref(xml_data, username, password)
  
  