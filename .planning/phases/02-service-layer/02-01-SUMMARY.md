---
phase: 02-service-layer
plan: 01
subsystem: api
tags: [scicrunch, rrid, elasticsearch, requests, validation]

# Dependency graph
requires:
  - phase: 01-database-foundation
    provides: DocidRrid model with entity_type/entity_id polymorphic FK
provides:
  - RRID format validation (validate_rrid) for SCR_, AB_, CVCL_ prefixes
  - SciCrunch Elasticsearch search (search_rrid_resources) with normalized results
  - SCICRUNCH_API_KEY Flask config entry
  - Resilient HTTP session with retry/backoff for SciCrunch API
  - RESOURCE_TYPE_MAP for core_facility, software, antibody, cell_line
affects: [02-service-layer, 03-api-blueprint, 04-integration-testing]

# Tech tracking
tech-stack:
  added: [requests, urllib3.util.retry.Retry, requests.adapters.HTTPAdapter]
  patterns: [(data, error) tuple return pattern, module-level requests.Session with retry adapter, term query for RRID vs query_string for keywords]

key-files:
  created:
    - backend/app/service_scicrunch.py
  modified:
    - backend/config.py

key-decisions:
  - "Use term queries for exact RRID lookups to avoid colon-escaping failures in query_string"
  - "Two separate URL constants (SCICRUNCH_SEARCH_BASE vs SCICRUNCH_RESOLVER_BASE) per project decision"
  - "Module-level requests.Session with Retry(total=3, backoff_factor=0.5) for resilient HTTP calls"
  - "(data, error) tuple pattern for all return values -- consistent with project convention"

patterns-established:
  - "(data, error) tuple: All service functions return (result, None) on success or (None, error_dict) on failure"
  - "Module-level HTTP session: Shared requests.Session with retry adapters mounted for both https:// and http://"
  - "RRID normalization: Auto-prepend RRID: prefix, uppercase identifier portion, strip whitespace"

requirements-completed: [INFRA-05, INFRA-06, SEARCH-07, SEARCH-08]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 2 Plan 1: SciCrunch Service Foundation Summary

**RRID validation with auto-prepend normalization and SciCrunch Elasticsearch search using term queries for exact RRID lookups and resilient HTTP session with retry backoff**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T18:07:03Z
- **Completed:** 2026-02-24T18:08:48Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Created `service_scicrunch.py` with RRID validation supporting SCR_, AB_, CVCL_ prefix families
- Implemented `search_rrid_resources` with dual query strategy: `term` for RRID lookups, `query_string` for keywords
- Added SCICRUNCH_API_KEY to Flask config with no NEXT_PUBLIC_ exposure
- Configured resilient HTTP session with retry on 502/503/504 and exponential backoff

## Task Commits

Each task was committed atomically:

1. **Task 1: Add SCICRUNCH_API_KEY to config and create service_scicrunch.py** - `ebfb1e5` (feat)

## Files Created/Modified
- `backend/app/service_scicrunch.py` - RRID validation and SciCrunch Elasticsearch search service (240+ lines)
- `backend/config.py` - Added SCICRUNCH_API_KEY config entry after CSTR block

## Decisions Made
- Used `term` query for exact RRID lookups instead of `query_string` to avoid SciCrunch colon-escaping failures (per SEARCH-08 requirement)
- Kept `SCICRUNCH_SEARCH_BASE` and `SCICRUNCH_RESOLVER_BASE` as separate constants since they point to different domains with different auth requirements
- Set `REQUEST_TIMEOUT = 30` seconds to accommodate SciCrunch variable latency (observed up to 25s)
- Used module-level `requests.Session()` rather than per-call sessions for connection pooling

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

Environment variable needed for SciCrunch API access:
- `SCICRUNCH_API_KEY` - Obtain from SciCrunch account settings at https://scicrunch.org

## Next Phase Readiness
- `validate_rrid` and `search_rrid_resources` are ready to be called from Phase 3 blueprint
- Plan 02 (resolver service) can build on the same module, adding resolver functions using `SCICRUNCH_RESOLVER_BASE`
- `RESOURCE_TYPE_MAP` ready for blueprint route parameter validation

## Self-Check: PASSED

- FOUND: backend/app/service_scicrunch.py
- FOUND: commit ebfb1e5
- FOUND: 02-01-SUMMARY.md

---
*Phase: 02-service-layer*
*Completed: 2026-02-24*
