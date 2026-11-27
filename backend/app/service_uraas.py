"""Client for the URAAS partner API (UNILAG research aggregator).

Only the related-papers lookup is used so far. URAAS keeps its own copy of
every docid-demo record (synced hourly) and answers in DOCiD terms: each
related paper carries the DOCiD publication id and DOCiD handle it was
ingested from. The API key stays on the server; browsers never see it.
"""
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

# (connect, read) seconds. The Hugging Face Space can be slow to wake up.
REQUEST_TIMEOUT = (5, 20)
RELATED_LIMIT = 10


class UraasUnavailable(Exception):
    """URAAS is not configured, unreachable, or answered with an error."""


def fetch_related_docids(publication_id):
    """Ask URAAS which DOCiD records are related to DOCiD publication_id.

    Returns (page_docid, related): page_docid is the DOCiD URAAS holds for
    publication_id, and related is a list of (publication_id, docid) pairs,
    best first. A record URAAS hasn't ingested gives (None, []). Raises
    UraasUnavailable when the key is missing or the call fails.
    """
    api_key = current_app.config.get('URAAS_API_KEY')
    if not api_key:
        raise UraasUnavailable('URAAS_API_KEY is not set')
    base_url = current_app.config.get('URAAS_BASE_URL', '').rstrip('/')

    try:
        response = requests.get(
            f'{base_url}/api/docid/enrichment/{publication_id}/related',
            params={'limit': RELATED_LIMIT, 'docid_only': 1},
            headers={'X-API-Key': api_key},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise UraasUnavailable(f'request failed: {exc.__class__.__name__}') from exc

    if response.status_code == 404:
        return None, []
    if response.status_code != 200:
        raise UraasUnavailable(f'HTTP {response.status_code}')

    try:
        body = response.json()
    except ValueError as exc:
        raise UraasUnavailable('response is not JSON') from exc
    related = body.get('related') if isinstance(body, dict) else None
    if not isinstance(related, list):
        raise UraasUnavailable('response has no "related" list')

    page_docid = _clean_docid(body.get('docid'))
    pairs = []
    seen_ids = set()
    for item in related:
        if not isinstance(item, dict):
            continue
        # docid_publication_id arrives as a string ("4167"); "id" is URAAS's own.
        try:
            related_id = int(item.get('docid_publication_id'))
        except (TypeError, ValueError):
            continue
        docid = _clean_docid(item.get('docid'))
        if docid is None or related_id in seen_ids:
            continue
        seen_ids.add(related_id)
        pairs.append((related_id, docid))
    return page_docid, pairs


def _clean_docid(value):
    return value.strip() if isinstance(value, str) and value.strip() else None
