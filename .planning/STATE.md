# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.
**Current focus:** Phase 2 — Service Layer

## Current Position

Phase: 2 of 8 (Service Layer)
Plan: 1 of 2 in current phase
Status: Executing
Last activity: 2026-02-24 — Completed 02-01-PLAN.md (SciCrunch RRID validation and search service)

Progress: [██░░░░░░░░] 18%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 3min
- Total execution time: 6min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-database-foundation | 1 | 4min | 4min |
| 02-service-layer | 1 | 2min | 2min |

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

### Critical Pitfalls

- Use `term` queries in Elasticsearch, not `query_string` (RRID colons cause silent 0-hit failures)
- Two separate URL constants: `SCICRUNCH_SEARCH_BASE` (api.scicrunch.io) and `SCICRUNCH_RESOLVER_BASE` (scicrunch.org)
- `SCICRUNCH_API_KEY` must never have `NEXT_PUBLIC_` prefix
- Polymorphic FK has no DB-level referential integrity — cascade must be application-level
- `resolved_json` stores normalized subset only, not raw ES blob

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-02-24
Stopped at: Completed 02-01-PLAN.md
Resume file: .planning/phases/02-service-layer/02-01-SUMMARY.md
