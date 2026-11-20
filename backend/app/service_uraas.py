"""Client for the URAAS partner API (UNILAG research aggregator).

Only the keyword-overlap "related papers" lookup is used so far. The API key
stays on the server; browsers never see it.
"""
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

# (connect, read) seconds. The Hugging Face Space can be slow to wake up.
REQUEST_TIMEOUT = (5, 20)


class UraasUnavailable(Exception):
    """URAAS is not configured, unreachable, or answered with an error."""


def fetch_related_paper_ids(paper_id):
    """Return the ids URAAS lists as keyword-related to paper_id, best first.

    A paper URAAS doesn't know gives an empty list. Raises UraasUnavailable
    when the key is missing or the call fails.
    """
    api_key = current_app.config.get('URAAS_API_KEY')
    if not api_key:
        raise UraasUnavailable('URAAS_API_KEY is not set')
    base_url = current_app.config.get('URAAS_BASE_URL', '').rstrip('/')

    try:
        response = requests.get(
            f'{base_url}/api/keywords/{paper_id}/related',
            headers={'X-API-Key': api_key},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise UraasUnavailable(f'request failed: {exc.__class__.__name__}') from exc

    if response.status_code == 404:
        return []
    if response.status_code != 200:
        raise UraasUnavailable(f'HTTP {response.status_code}')

    try:
        body = response.json()
    except ValueError as exc:
        raise UraasUnavailable('response is not JSON') from exc
    related = body.get('related') if isinstance(body, dict) else None
    if not isinstance(related, list):
        raise UraasUnavailable('response has no "related" list')

    paper_ids = []
    for item in related:
        try:
            related_id = int(item.get('id'))
        except (AttributeError, TypeError, ValueError):
            continue
        if related_id not in paper_ids:
            paper_ids.append(related_id)
    return paper_ids
