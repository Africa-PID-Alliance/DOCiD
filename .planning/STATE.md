# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.
**Current focus:** Phase 1 — Database Foundation

## Current Position

Phase: 1 of 8 (Database Foundation)
Plan: 1 of 1 in current phase
Status: Phase 1 complete
Last activity: 2026-02-24 — Completed 01-01-PLAN.md (DocidRrid model and migration)

Progress: [█░░░░░░░░░] 12%

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 4min
- Total execution time: 4min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-database-foundation | 1 | 4min | 4min |

*Updated after each plan completion*

## Accumulated Context

### Decisions

- [Roadmap]: Dedicated `docid_rrids` table (Option B) — strict RRID separation, not generic external_identifiers
- [Roadmap]: 8 granular phases following strict DB → service → blueprint → tests → proxy → UI chain
- [Roadmap]: RRID attachment scoped to publications and organizations only (no creators/projects)
- [Roadmap]: DB-level JSONB cache for resolver results (not Redis), normalized subset only
- [Infra]: Backend port is 5001 (macOS AirPlay conflict on 5000)
- [Pattern]: ROR integration (`routes/ror.py`) is the closest pattern to follow for RRID

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
Stopped at: Completed 01-01-PLAN.md
Resume file: .planning/phases/01-database-foundation/01-01-SUMMARY.md
