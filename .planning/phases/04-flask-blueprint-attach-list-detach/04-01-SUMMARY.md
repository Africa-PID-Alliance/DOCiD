---
phase: 04-flask-blueprint-attach-list-detach
plan: 01
subsystem: api
tags: [flask, rrid, scicrunch, sqlalchemy, jwt, cascade-delete]

# Dependency graph
requires:
  - phase: 03-flask-blueprint-search-resolve
    provides: rrid_bp blueprint, DocidRrid model with ALLOWED_ENTITY_TYPES and get_rrids_for_entity, validate_rrid service function
  - phase: 01-database-foundation
    provides: DocidRrid table with unique constraint uq_docid_rrids_entity_rrid (triggers 409 on duplicate attach)
provides:
  - POST /api/v1/rrid/attach — attaches RRID to entity with SciCrunch resolution, returns 201 with serialized row
  - GET /api/v1/rrid/entity — lists all RRIDs for a given entity_type/entity_id, returns flat JSON array
  - DELETE /api/v1/rrid/<rrid_id> — removes RRID record by PK, returns 200
  - Cascade deletion of docid_rrids rows in delete_publication (publication + organization entity types)
affects:
  - 05-integration-tests
  - 06-frontend-proxy
  - 07-ui-rrid-management

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "IntegrityError catch for duplicate detection: try db.session.add/commit, except IntegrityError rollback + 409"
    - "Application-level cascade delete (polymorphic FK): fetch child IDs before parent delete, filter().delete(synchronize_session='fetch')"
    - "Fresh SciCrunch resolve on attach (no entity context): fail the request with 502 if SciCrunch unavailable"

key-files:
  created: []
  modified:
    - backend/app/routes/rrid.py
    - backend/app/routes/publications.py

key-decisions:
  - "On duplicate attach, IntegrityError from DB unique constraint (uq_docid_rrids_entity_rrid) is caught at application layer and mapped to 409 with human-readable message: '<RRID> is already attached to this <entity_type>'"
  - "attach endpoint calls resolve_rrid() WITHOUT entity context — fresh resolve only, no cache reuse — per prior user decision"
  - "If SciCrunch is down during attach, request fails with 502 — no row created without metadata, per user decision"
  - "list endpoint returns 200 with [] for empty results (consistent with Phase 3 search pattern), no 204"
  - "detach endpoint has no ownership check — any authenticated user can delete any RRID record, per user decision"
  - "Publication cascade deletes organization RRID rows by first collecting publication_organization IDs then using .in_() filter with synchronize_session='fetch'"

patterns-established:
  - "RRID attach pattern: validate inputs -> validate RRID format -> resolve RRID -> create row -> catch IntegrityError for 409"
  - "Application cascade order: delete leaf entity rows (RRID for pub, RRID for org) before deleting join table rows (PublicationOrganization)"

requirements-completed: [ATTACH-01, ATTACH-02, ATTACH-03, ATTACH-04, ATTACH-05, ATTACH-06, ATTACH-07, ATTACH-08]

# Metrics
duration: 2min
completed: 2026-02-24
---

# Phase 4 Plan 01: RRID Lifecycle Endpoints Summary

**Three RRID lifecycle endpoints (attach, list, detach) added to rrid_bp blueprint plus application-level cascade deletion in delete_publication covering both publication and organization RRID rows**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-24T21:57:54Z
- **Completed:** 2026-02-24T21:59:44Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- POST /api/v1/rrid/attach endpoint resolves RRID via SciCrunch, creates DocidRrid row with full metadata, returns 201; duplicate returns 409 with readable message
- GET /api/v1/rrid/entity endpoint lists all RRIDs for a given entity as a flat JSON array (200 with [] for empty)
- DELETE /api/v1/rrid/<rrid_id> endpoint removes RRID record by PK, returns 200; 404 if not found
- delete_publication now cascades to remove associated docid_rrids rows for both publication and organization entity types before deleting PublicationOrganization rows

## Task Commits

Each task was committed atomically:

1. **Task 1: Add attach, list, and detach endpoints to rrid.py** - `0dbd7a8` (feat)
2. **Task 2: Add RRID cascade deletion to publication and organization delete flows** - `499ac5c` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `backend/app/routes/rrid.py` - Added attach_rrid (POST /attach), list_entity_rrids (GET /entity), detach_rrid (DELETE /<rrid_id>) endpoints with full Flasgger docstrings; added imports for db, IntegrityError, validate_rrid, datetime
- `backend/app/routes/publications.py` - Added DocidRrid import; inserted RRID cascade deletion (publication + organization) before PublicationOrganization deletion in delete_publication transaction

## Decisions Made
- Followed plan as specified. No deviations required.
- Confirmed: attach endpoint uses fresh resolve (no entity context passed to resolve_rrid) per prior user decision
- Confirmed: 409 message format is `"{RRID} is already attached to this {entity_type}"` — human-readable and entity-aware
- Confirmed: list endpoint returns 200+[] for empty results, no 204
- Confirmed: detach has no ownership check — any authenticated user can remove any RRID

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - both tasks completed cleanly on first attempt.

## User Setup Required

None - no external service configuration required. All RRID endpoints rely on existing SCICRUNCH_API_KEY env var configured in Phase 2.

## Next Phase Readiness
- All 5 RRID endpoints (search, resolve, attach, entity, delete) are live under /api/v1/rrid with JWT protection
- RRID data lifecycle is complete: create, query, delete, with cascade on publication deletion
- Ready for Phase 5 (integration tests) and Phase 6 (frontend proxy)
- No blockers

---
*Phase: 04-flask-blueprint-attach-list-detach*
*Completed: 2026-02-24*
