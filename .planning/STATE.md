# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.
**Current focus:** Phase 1 — Database Foundation

## Current Position

Phase: 1 of 8 (Database Foundation)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-02-24 — Roadmap created, 56 requirements mapped across 8 phases

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

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
Stopped at: Roadmap created, STATE.md initialized, REQUIREMENTS.md traceability updated
Resume file: None
