# app/service_scicrunch.py
#
# SciCrunch RRID validation and Elasticsearch search service.
# Provides RRID format validation and resource search via the
# SciCrunch API (api.scicrunch.io).

import re
import logging
from datetime import datetime, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from flask import current_app

from app.models import DocidRrid
from app import db

# ---------------------------------------------------------------------------
# Module-level logger
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# URL constants -- two separate domains per project decision
# ---------------------------------------------------------------------------
SCICRUNCH_SEARCH_BASE = "https://api.scicrunch.io/elastic/v1"
SCICRUNCH_RESOLVER_BASE = "https://scicrunch.org"

# ---------------------------------------------------------------------------
# Per-type Elasticsearch index mapping
# Antibodies and cell lines have dedicated indices; core facilities and
# software share RIN_Tool_pr but use different type filter values.
# ---------------------------------------------------------------------------
RESOURCE_TYPE_INDEX_MAP = {
    "core_facility": "RIN_Tool_pr",
    "software": "RIN_Tool_pr",
    "antibody": "RIN_Antibody_pr",
    "cell_line": "RIN_CellLine_pr",
}

# Indices that are inherently type-scoped — no type filter clause needed
TYPE_SCOPED_INDICES = {"RIN_Antibody_pr", "RIN_CellLine_pr"}

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
    "core_facility": "core facility",
    "software": "software resource",
    "antibody": "antibody",
    "cell_line": "cell line",
}

DEFAULT_RESOURCE_TYPE = "core_facility"

# ---------------------------------------------------------------------------
# HTTP / search limits
# ---------------------------------------------------------------------------
SEARCH_RESULT_LIMIT = 20
REQUEST_TIMEOUT = 30  # seconds -- accommodates SciCrunch variable latency

# ---------------------------------------------------------------------------
# Resolver cache TTL
# ---------------------------------------------------------------------------
CACHE_MAX_AGE_DAYS = 30

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
    query = query.strip()

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
    elasticsearch_index = RESOURCE_TYPE_INDEX_MAP[resource_type]

    # --- API key ---
    api_key = _get_api_key()
    if api_key is None:
        return (None, {"error": "SciCrunch API key not configured"})

    # --- Build Elasticsearch query body ---
    # Type-scoped indices (antibody, cell_line) don't need a type filter;
    # shared indices (RIN_Tool_pr) use the .aggregate keyword field for
    # exact type matching per SciCrunch documentation.
    if elasticsearch_index in TYPE_SCOPED_INDICES:
        filter_clauses = []
    else:
        filter_clauses = [
            {"terms": {"item.types.name.aggregate": [resource_type_filter_value]}}
        ]

    must_not_clauses = [{"term": {"recordValid": False}}]

    is_rrid_lookup = bool(RRID_PATTERN.match(query.strip()))

    if is_rrid_lookup:
        # Exact RRID lookup -- use term query to avoid colon-escaping issues
        validated_rrid, validation_error = validate_rrid(query)
        if validation_error:
            return (None, validation_error)

        # Strip the "RRID:" prefix for the term lookup on the curie field
        rrid_identifier = validated_rrid.replace("RRID:", "")

        bool_query = {
            "must": [
                {"term": {"item.curie": rrid_identifier}},
            ],
            "must_not": must_not_clauses,
        }
    else:
        # Free-text keyword search — all query terms must appear together within
        # item.name OR item.description (per-field operator:and prevents cross-field
        # false positives like "cape town" in description + "university" in name).
        bool_query = {
            "must": [
                {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "item.name": {
                                        "query": query,
                                        "operator": "and",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            },
                            {
                                "match": {
                                    "item.description": {
                                        "query": query,
                                        "operator": "and",
                                        "fuzziness": "AUTO",
                                    }
                                }
                            },
                        ],
                        "minimum_should_match": 1,
                    }
                },
            ],
            "must_not": must_not_clauses,
        }

    if filter_clauses:
        bool_query["filter"] = filter_clauses

    elasticsearch_query_body = {
        "size": SEARCH_RESULT_LIMIT,
        "query": {"bool": bool_query},
    }

    # --- Execute search request ---
    search_url = f"{SCICRUNCH_SEARCH_BASE}/{elasticsearch_index}/_search"
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


# ---------------------------------------------------------------------------
# Resolver helpers
# ---------------------------------------------------------------------------

def _normalize_resolver_response(raw_json):
    """Extract a normalized subset from SciCrunch resolver JSON.

    The resolver endpoint returns:
      {"hits": {"hits": [{"_source": {"item": {...}}}]}, "resolver": {...}}

    This function drills into hits.hits[0]._source.item to extract the
    canonical resource metadata.

    Args:
        raw_json: Parsed JSON dict from the SciCrunch resolver endpoint.

    Returns:
        dict with keys: name, rrid, description, url, resource_type.
        All values default to empty string when absent.
    """
    if not isinstance(raw_json, dict):
        logger.warning("Resolver response is not a dict; returning defaults")
        return {"name": "", "rrid": "", "description": "", "url": "", "resource_type": ""}

    try:
        item = raw_json["hits"]["hits"][0]["_source"]["item"]
    except (KeyError, IndexError):
        logger.warning("Resolver response missing expected hits structure")
        return {"name": "", "rrid": "", "description": "", "url": "", "resource_type": ""}

    # Primary type is the first entry in the types list
    types = item.get("types", [])
    resource_type = types[0].get("name", "") if types else ""

    return {
        "name": item.get("name", ""),
        "rrid": item.get("curie", ""),
        "description": item.get("description", ""),
        "url": item.get("url", ""),
        "resource_type": resource_type,
    }


# ---------------------------------------------------------------------------
# Resolver with DB cache
# ---------------------------------------------------------------------------

def resolve_rrid(rrid_string, entity_type=None, entity_id=None):
    """Resolve an RRID to canonical metadata via SciCrunch resolver.

    Transparently caches the normalized result in the ``DocidRrid`` row's
    ``resolved_json`` column when entity context is provided.  Subsequent
    calls reuse cached data if ``last_resolved_at`` is less than
    ``CACHE_MAX_AGE_DAYS`` days old.

    On SciCrunch API failure the most recent cached data is returned
    (stale-while-error strategy); an error is surfaced only when no cached
    data exists at all.

    Args:
        rrid_string: Raw RRID string to resolve (e.g. ``"RRID:SCR_012345"``).
        entity_type: Optional entity type (``"publication"`` or
            ``"organization"``) for DB cache lookup.
        entity_id: Optional entity primary-key value for DB cache lookup.

    Returns:
        tuple: ``(result_dict, None)`` on success, or
               ``(None, error_dict)`` on failure.
    """
    # --- Validate input RRID ---
    validated_rrid, validation_error = validate_rrid(rrid_string)
    if validation_error:
        return (None, validation_error)

    normalized_rrid = validated_rrid

    # --- Step 1: Check DB cache (when entity context provided) ---
    cached_row = None
    entity_context_provided = entity_type is not None and entity_id is not None

    if entity_context_provided:
        try:
            cached_row = DocidRrid.query.filter_by(
                entity_type=entity_type,
                entity_id=entity_id,
                rrid=normalized_rrid,
            ).first()
        except Exception as database_lookup_error:
            logger.error(
                "DB cache lookup failed for %s: %s",
                normalized_rrid,
                database_lookup_error,
            )
            # Continue without cache -- resolver fetch may still succeed

        if (
            cached_row is not None
            and cached_row.last_resolved_at is not None
            and cached_row.resolved_json is not None
            and (datetime.utcnow() - cached_row.last_resolved_at)
            < timedelta(days=CACHE_MAX_AGE_DAYS)
        ):
            logger.info("Fresh cache hit for %s", normalized_rrid)
            return (
                {
                    "resolved": cached_row.resolved_json,
                    "last_resolved_at": cached_row.last_resolved_at.isoformat(),
                    "cached": True,
                },
                None,
            )

    # --- Step 2: Fetch from SciCrunch resolver ---
    resolver_url = f"{SCICRUNCH_RESOLVER_BASE}/resolver/{normalized_rrid}.json"
    resolved_data = None

    try:
        resolver_response = scicrunch_http_session.get(
            resolver_url,
            timeout=REQUEST_TIMEOUT,
            # NOTE: No apikey header -- resolver domain does not use it
        )

        if resolver_response.status_code == 200:
            try:
                raw_resolver_json = resolver_response.json()
            except ValueError:
                logger.error(
                    "Failed to parse SciCrunch resolver JSON for %s",
                    normalized_rrid,
                )
                raw_resolver_json = None

            if raw_resolver_json is not None:
                resolved_data = _normalize_resolver_response(raw_resolver_json)
        else:
            logger.warning(
                "SciCrunch resolver returned HTTP %d for %s: %s",
                resolver_response.status_code,
                normalized_rrid,
                resolver_response.text[:500],
            )

    except requests.RequestException as resolver_request_error:
        logger.error(
            "SciCrunch resolver request failed for %s: %s",
            normalized_rrid,
            resolver_request_error,
        )

    # --- Step 3: Update DB cache (if entity context provided and fresh data) ---
    if entity_context_provided and resolved_data:
        try:
            if cached_row is not None:
                cached_row.resolved_json = resolved_data
                cached_row.last_resolved_at = datetime.utcnow()
                db.session.commit()
                logger.info("Updated resolver cache for %s", normalized_rrid)
        except Exception as database_update_error:
            logger.error(
                "DB cache update failed for %s: %s",
                normalized_rrid,
                database_update_error,
            )
            try:
                db.session.rollback()
            except Exception:
                pass
            # Continue -- resolved data is still useful even if cache update fails

    # --- Step 4: Return resolved data or fall back to stale cache ---
    if resolved_data:
        return (
            {
                "resolved": resolved_data,
                "last_resolved_at": datetime.utcnow().isoformat(),
                "cached": False,
            },
            None,
        )

    # Stale cache fallback -- SciCrunch resolver failed but we may have old data
    if cached_row is not None and cached_row.resolved_json is not None:
        logger.warning(
            "SciCrunch resolver failed, returning stale cache for %s",
            normalized_rrid,
        )
        return (
            {
                "resolved": cached_row.resolved_json,
                "last_resolved_at": (
                    cached_row.last_resolved_at.isoformat()
                    if cached_row.last_resolved_at
                    else None
                ),
                "cached": True,
                "stale": True,
            },
            None,
        )

    # No cache at all -- genuine error
    return (
        None,
        {
            "error": "SciCrunch resolver failed",
            "detail": f"Could not resolve {normalized_rrid} and no cached data available",
        },
    )
