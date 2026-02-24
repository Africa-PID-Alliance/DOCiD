# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.
**Current focus:** Phase 4 — Flask Blueprint: Attach, List, Detach

## Current Position

Phase: 4 of 8 (Flask Blueprint — Attach, List, Detach)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-02-25 — Phase 3 complete (verified 7/7 must-haves)

Progress: [████░░░░░░] 38%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 3min
- Total execution time: 10min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-database-foundation | 1 | 4min | 4min |
| 02-service-layer | 2 | 4min | 2min |
| 03-flask-blueprint-search-resolve | 1 | 2min | 2min |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- [Roadmap]: Dedicated `docid_rrids` table (Option B) — strict RRID separation, not generic external_identifiers
- [Roadmap]: 8 granular phases following strict DB → service → blueprint → tests → proxy → UI chain
- [Roadmap]: RRID attachment scoped to publications and organizations only (no creators/projects)
- [Roadmap]: DB-level JSONB cache for resolver results (not Redis), normalized subset only
- [Infra]: Backend port is 5001 (macOS AirPlay conflict on 5000)
- [Pattern]: ROR integration (`routes/ror.py`) is the closest pattern to follow for RRID
- [02-01]: Use `term` queries for exact RRID lookups, `query_string` only for keyword searches
- [02-01]: Module-level `requests.Session` with Retry(total=3, backoff_factor=0.5) for SciCrunch HTTP calls
- [02-01]: (data, error) tuple pattern for all service function return values
- [02-02]: No apikey header sent to resolver domain -- only search domain gets apikey
- [02-02]: DB operations in try/except so resolver data returned even if cache write fails
- [02-02]: Stale cache returned with `stale: True` flag for caller awareness
- [02-02]: resolved_json stores only 7 normalized fields (name, rrid, description, url, resource_type, properCitation, mentions)
- [Phase 03-01]: DocidRrid.ALLOWED_ENTITY_TYPES as single source of truth for entity type validation, matching DB-level CHECK constraint
- [Phase 03-01]: Resolve endpoint flattens nested service response using dict spread operator into single-level JSON
- [Phase 03-01]: Generic 502 error messages for all SciCrunch failures — internals never exposed to API consumers

### Critical Pitfalls

- Use `term` queries in Elasticsearch, not `query_string` (RRID colons cause silent 0-hit failures)
- Two separate URL constants: `SCICRUNCH_SEARCH_BASE` (api.scicrunch.io) and `SCICRUNCH_RESOLVER_BASE` (scicrunch.org)
- `SCICRUNCH_API_KEY` must never have `NEXT_PUBLIC_` prefix
- Polymorphic FK has no DB-level referential integrity — cascade must be application-level
- `resolved_json` stores normalized subset only, not raw ES blob
- No apikey header to resolver domain (scicrunch.org) -- only to search domain (api.scicrunch.io)

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

### Phase 3 Decisions

- [03]: Flat JSON array response for search, no wrapper/metadata
- [03]: Empty search → 200 with `[]`, not 204
- [03]: Resolve response includes `last_resolved_at` + `stale` flag alongside 7 canonical fields
- [03]: Hard cap 20 results, no pagination
- [03]: SciCrunch failures → HTTP 502 with generic error messages
- [03]: RRID not found → 404, invalid format → 400, missing `q` → 400
- [03]: Strict `@jwt_required()` on both endpoints, any authenticated user
- [03]: entity_type/entity_id optional on resolve, rejected if partial (both or neither)
- [03]: Entity type allowlist imported from DocidRrid model (single source of truth)
- [03]: Search does NOT accept entity params — only `q` and `type`

## Session Continuity

Last session: 2026-02-25
Stopped at: Phase 3 complete (verified)
Resume file: .planning/phases/03-flask-blueprint-search-resolve/03-01-SUMMARY.md
