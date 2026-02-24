# app/service_scicrunch.py
#
# SciCrunch RRID validation and Elasticsearch search service.
# Provides RRID format validation and resource search via the
# SciCrunch API (api.scicrunch.io).

import re
import logging

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import current_app

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL constants -- two separate domains per project decision
# ---------------------------------------------------------------------------
SCICRUNCH_SEARCH_BASE = "https://api.scicrunch.io/elastic/v1"
SCICRUNCH_RESOLVER_BASE = "https://scicrunch.org"

# Elasticsearch index used by SciCrunch for resource registry
SCICRUNCH_ES_INDEX = "RIN_Tool_pr"

# ---------------------------------------------------------------------------
# RRID validation pattern
# Accepts optional "RRID:" prefix followed by SCR_, AB_, or CVCL_ identifiers
# ---------------------------------------------------------------------------
RRID_PATTERN = re.compile(
    r'^(RRID:)?(SCR_\d+|AB_\d+|CVCL_\d+)$',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Resource type mapping -- user-friendly keys to SciCrunch type filter values
# ---------------------------------------------------------------------------
RESOURCE_TYPE_MAP = {
    "core_facility": "Resource:CoreFacility",
    "software": "Resource:Software",
    "antibody": "Resource:Antibody",
    "cell_line": "Resource:CellLine",
}

DEFAULT_RESOURCE_TYPE = "core_facility"

# ---------------------------------------------------------------------------
# HTTP / search limits
# ---------------------------------------------------------------------------
SEARCH_RESULT_LIMIT = 20
REQUEST_TIMEOUT = 30  # seconds -- accommodates SciCrunch variable latency

# ---------------------------------------------------------------------------
# Resilient HTTP session with automatic retries on transient errors
# ---------------------------------------------------------------------------
retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[502, 503, 504],
)
http_adapter = HTTPAdapter(max_retries=retry_strategy)

scicrunch_http_session = requests.Session()
scicrunch_http_session.mount("https://", http_adapter)
scicrunch_http_session.mount("http://", http_adapter)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _get_api_key():
    """Retrieve the SciCrunch API key from Flask app config.

    Returns the key string or ``None`` when not configured / empty.
    """
    api_key = current_app.config.get("SCICRUNCH_API_KEY")
    if not api_key:
        return None
    return api_key


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_rrid(rrid_string):
    """Validate and normalize an RRID string.

    Accepts formats like ``RRID:SCR_012345``, ``SCR_012345``, or
    case-insensitive variants (``rrid:scr_012345``).

    Returns:
        tuple: ``(normalized_rrid, None)`` on success, or
               ``(None, error_dict)`` on failure.
    """
    cleaned_input = rrid_string.strip() if rrid_string else ""

    match = RRID_PATTERN.match(cleaned_input)

    if not match:
        return (
            None,
            {
                "error": "Invalid RRID format",
                "detail": (
                    f"'{rrid_string}' does not match "
                    "RRID:SCR_*, RRID:AB_*, or RRID:CVCL_* patterns"
                ),
            },
        )

    # Group 2 is the identifier portion (SCR_xxx, AB_xxx, CVCL_xxx)
    identifier_portion = match.group(2).upper()
    normalized_rrid = f"RRID:{identifier_portion}"

    return (normalized_rrid, None)


def search_rrid_resources(query, resource_type=None):
    """Search SciCrunch Elasticsearch for RRID resources.

    Uses ``term`` queries for exact RRID lookups and ``query_string``
    for free-text keyword searches.

    Args:
        query: Search term -- either an RRID string or free-text keywords.
        resource_type: Optional key from ``RESOURCE_TYPE_MAP``. Defaults to
            ``DEFAULT_RESOURCE_TYPE``.

    Returns:
        tuple: ``(results_list, None)`` on success, or
               ``(None, error_dict)`` on failure.
    """
    # --- Resource type resolution ---
    if resource_type is None:
        resource_type = DEFAULT_RESOURCE_TYPE

    if resource_type not in RESOURCE_TYPE_MAP:
        valid_types = ", ".join(RESOURCE_TYPE_MAP.keys())
        return (
            None,
            {
                "error": "Invalid resource type",
                "detail": (
                    f"'{resource_type}' is not a valid resource type. "
                    f"Valid types: {valid_types}"
                ),
            },
        )

    resource_type_filter_value = RESOURCE_TYPE_MAP[resource_type]

    # --- API key ---
    api_key = _get_api_key()
    if api_key is None:
        return (None, {"error": "SciCrunch API key not configured"})

    # --- Build Elasticsearch query body ---
    is_rrid_lookup = bool(RRID_PATTERN.match(query.strip()))

    if is_rrid_lookup:
        # Exact RRID lookup -- use term query to avoid colon-escaping issues
        validated_rrid, validation_error = validate_rrid(query)
        if validation_error:
            return (None, validation_error)

        # Strip the "RRID:" prefix for the term lookup on the curie field
        rrid_identifier = validated_rrid.replace("RRID:", "")

        elasticsearch_query_body = {
            "size": SEARCH_RESULT_LIMIT,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"item.curie": rrid_identifier}},
                    ],
                    "filter": [
                        {"term": {"item.types.curie": resource_type_filter_value}},
                    ],
                }
            },
        }
    else:
        # Free-text keyword search
        elasticsearch_query_body = {
            "size": SEARCH_RESULT_LIMIT,
            "query": {
                "bool": {
                    "must": [
                        {"query_string": {"query": query}},
                    ],
                    "filter": [
                        {"term": {"item.types.curie": resource_type_filter_value}},
                    ],
                }
            },
        }

    # --- Execute search request ---
    search_url = f"{SCICRUNCH_SEARCH_BASE}/{SCICRUNCH_ES_INDEX}/_search"
    request_headers = {
        "apikey": api_key,
        "Content-Type": "application/json",
    }

    try:
        response = scicrunch_http_session.post(
            search_url,
            headers=request_headers,
            json=elasticsearch_query_body,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as request_error:
        logger.error(
            "SciCrunch search request failed: %s", request_error
        )
        return (
            None,
            {
                "error": "SciCrunch search request failed",
                "detail": str(request_error),
            },
        )

    if response.status_code != 200:
        logger.warning(
            "SciCrunch search returned HTTP %d: %s",
            response.status_code,
            response.text[:500],
        )
        return (
            None,
            {
                "error": "SciCrunch search failed",
                "status_code": response.status_code,
                "detail": response.text[:500],
            },
        )

    # --- Parse and normalize results ---
    try:
        response_json = response.json()
    except ValueError:
        logger.error("Failed to parse SciCrunch JSON response")
        return (
            None,
            {
                "error": "SciCrunch search failed",
                "detail": "Invalid JSON in response",
            },
        )

    raw_hits = response_json.get("hits", {}).get("hits", [])

    normalized_results = []
    for hit in raw_hits:
        source_item = hit.get("_source", {}).get("item", {})
        normalized_results.append(
            {
                "scicrunch_id": hit.get("_id", ""),
                "name": source_item.get("name", ""),
                "description": source_item.get("description", ""),
                "url": source_item.get("url", ""),
                "types": source_item.get("types", []),
                "rrid": f"RRID:{source_item.get('curie', '')}",
            }
        )

    logger.info(
        "SciCrunch search for '%s' returned %d results",
        query,
        len(normalized_results),
    )

    return (normalized_results, None)
