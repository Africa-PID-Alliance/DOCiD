# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.
**Current focus:** Phase 3 — Flask Blueprint: Search & Resolve

## Current Position

Phase: 3 of 8 (Flask Blueprint — Search & Resolve)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-02-24 — Completed 02-02-PLAN.md (RRID resolver with DB cache)

Progress: [███░░░░░░░] 27%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 3min
- Total execution time: 8min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-database-foundation | 1 | 4min | 4min |
| 02-service-layer | 2 | 4min | 2min |

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

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 02-02-PLAN.md (Phase 2 complete)
Resume file: .planning/phases/02-service-layer/02-02-SUMMARY.md
