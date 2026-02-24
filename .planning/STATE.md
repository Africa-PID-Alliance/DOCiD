# GSD State

## Current Position

Phase: Not started (defining requirements)
Plan: --
Status: Defining requirements
Last activity: 2026-02-24 -- Milestone v1.0 RRID Integration started

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-24)

**Core value:** Researchers and institutions can assign, resolve, and manage persistent identifiers for African scholarly publications through a single unified platform.
**Current focus:** RRID (SciCrunch) integration

## Accumulated Context

- DOCiD has 13+ external service integrations already working
- ROR integration (`routes/ror.py`) is the closest pattern to follow for RRID
- SciCrunch API uses `apikey` header authentication (not OAuth)
- Existing identifier pattern: `identifier` (String 500) + `identifier_type` (String 50)
- User chose dedicated `docid_rrids` table (Option B) over generic external_identifiers
- Scope: Publications + Organizations, full features except bulk sync
- Frontend uses Next.js API proxy pattern (never calls backend directly from browser)
- Backend port: 5001 (macOS AirPlay conflict on 5000)
