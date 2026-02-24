---
phase: 02-service-layer
plan: 02
subsystem: api
tags: [scicrunch, rrid, resolver, cache, jsonb, requests]

# Dependency graph
requires:
  - phase: 01-database-foundation
    provides: DocidRrid model with resolved_json JSONB and last_resolved_at columns
  - phase: 02-service-layer/01
    provides: service_scicrunch.py with validate_rrid, search_rrid_resources, session, constants
provides:
  - RRID resolver function (resolve_rrid) fetching from scicrunch.org/resolver/{RRID}.json
  - 30-day DB-level cache via DocidRrid.resolved_json with transparent refresh
  - Stale cache fallback on SciCrunch API failure
  - Normalized 7-field resolver response subset (_normalize_resolver_response)
  - CACHE_MAX_AGE_DAYS constant (30 days)
affects: [03-api-blueprint, 04-integration-testing, 06-frontend-ui]

# Tech tracking
tech-stack:
  added: []
  patterns: [DB-level JSONB cache with stale-while-error fallback, normalized resolver response subset (7 fields only)]

key-files:
  created: []
  modified:
    - backend/app/service_scicrunch.py

key-decisions:
  - "No apikey header sent to resolver domain -- only search domain (api.scicrunch.io) gets apikey"
  - "DB operations wrapped in try/except so resolver data is still returned even if cache write fails"
  - "Stale cache returned with 'stale: True' flag so callers can distinguish fresh vs stale data"
  - "resolved_json stores only 7 normalized fields (name, rrid, description, url, resource_type, properCitation, mentions) -- not raw blob"

patterns-established:
  - "Stale-while-error: On API failure, return cached data with stale=True flag; error only when no cache exists"
  - "Normalized resolver subset: _normalize_resolver_response extracts exactly 7 fields with safe defaults"
  - "Cache TTL check: (datetime.utcnow() - last_resolved_at) < timedelta(days=CACHE_MAX_AGE_DAYS)"

requirements-completed: [CACHE-01, CACHE-02, CACHE-03]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 2 Plan 2: SciCrunch RRID Resolver with DB Cache Summary

**RRID resolver function with 30-day JSONB cache, stale-while-error fallback, and normalized 7-field metadata subset stored in DocidRrid.resolved_json**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T18:11:49Z
- **Completed:** 2026-02-24T18:13:54Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `resolve_rrid` function with full cache-check -> fetch -> cache-update -> return flow
- Added `_normalize_resolver_response` helper extracting exactly 7 fields from SciCrunch resolver JSON
- Implemented 30-day TTL cache using `DocidRrid.resolved_json` and `last_resolved_at` columns
- Stale cache fallback on SciCrunch API failure with `stale: True` flag for caller awareness
- No apikey sent to resolver domain (only to search domain per project decision)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add resolve_rrid function with 30-day DB cache and stale fallback** - `d674760` (feat)

## Files Created/Modified
- `backend/app/service_scicrunch.py` - Added resolve_rrid, _normalize_resolver_response, CACHE_MAX_AGE_DAYS, and imports for datetime/timedelta/DocidRrid/db (+233 lines)

## Decisions Made
- No apikey header sent to resolver domain -- resolver at scicrunch.org does not require authentication (per project decision and 02-CONTEXT.md)
- DB operations wrapped in try/except with rollback so resolver data is still returned even if cache write fails
- Stale cache includes `stale: True` flag in the return dict so callers can distinguish fresh vs stale data
- Missing field warnings logged at WARNING level to surface data quality issues without breaking resolution

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no additional environment variables or external service configuration required beyond what Plan 01 already set up (SCICRUNCH_API_KEY).

## Next Phase Readiness
- `service_scicrunch.py` is now complete with all three public functions: `validate_rrid`, `search_rrid_resources`, `resolve_rrid`
- Phase 3 (API Blueprint) can call `resolve_rrid(rrid, entity_type, entity_id)` to resolve any RRID with transparent caching
- The `(data, error)` tuple pattern is consistent across all functions for uniform error handling in blueprint routes

## Self-Check: PASSED

- FOUND: backend/app/service_scicrunch.py
- FOUND: commit d674760
- FOUND: 02-02-SUMMARY.md

---
*Phase: 02-service-layer*
*Completed: 2026-02-24*
