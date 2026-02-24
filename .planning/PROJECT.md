# DOCiD — Persistent Identifier Management Platform

## What This Is

DOCiD is a Flask + Next.js platform for managing persistent identifiers (PIDs) for scholarly publications in Africa. It assigns DOCiDs, registers DOIs, and integrates with 13+ external services (ROR, ORCID, Crossref, CORDRA, DSpace, Local Contexts, etc.) to provide comprehensive metadata management and identifier resolution for research outputs.

## Core Value

Researchers and institutions can assign, resolve, and manage persistent identifiers for African scholarly publications through a single unified platform.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ROR organization identifier lookup and attachment to publications
- ORCID researcher identifier integration with OAuth
- ISNI creator identifier lookup
- Ringgold institutional affiliation (hybrid local DB + API)
- RAiD research project identifier integration
- Crossref DOI metadata and registration
- DataCite DOI services
- CORDRA digital object repository with Handle generation
- CSTR China Science & Technology Resource platform
- DSpace 6.x and 7.x repository import/sync
- Figshare article import and metadata
- OJS Open Journal Systems integration
- Local Contexts cultural heritage labels
- Hierarchical commenting system on publications
- JWT authentication with social auth (Google, ORCID, GitHub)
- Publication lifecycle: creation, identifier assignment, external registration
- User account management with Individual/Institutional account types

### Active

<!-- Current scope: RRID/SciCrunch integration -->

- [ ] RRID (SciCrunch) integration — search, resolve, and attach Research Resource Identifiers to publications and organizations

### Out of Scope

- Bulk RRID sync for local search — deferred to future milestone, core integration first
- Direct browser-to-SciCrunch calls — API key must stay server-side
- RRID attachment to creators/projects — limited to publications and organizations for this milestone

## Current Milestone: v1.0 RRID Integration

**Goal:** Integrate RRID (Research Resource Identifier) from SciCrunch into DOCiD, enabling users to search, resolve, and attach RRIDs to publications and organizations — following the same patterns as existing ROR/ORCID integrations.

**Target features:**
- Backend Flask blueprint with SciCrunch API proxy endpoints (search, resolve)
- Dedicated `docid_rrids` database table with Alembic migration
- Frontend search modal for RRID resource discovery
- RRID attachment to publications and organizations
- Display of attached RRIDs on entity detail pages
- DB-level caching of resolver metadata
- Backend tests for request/parse and schema validation

## Context

- SciCrunch API base: `https://api.scicrunch.io` with `apikey` header auth
- RRID resolver: `https://scicrunch.org/resolver/<RRID>.json`
- RIN resources exposed via Elasticsearch gateway (index: `RIN_Tool_pr`)
- RRID formats: `RRID:SCR_########` (software), `RRID:AB_#########` (antibodies), `RRID:CVCL_####` (cell lines)
- Existing DOCiD pattern: identifier (String 500) + identifier_type (String 50) stored on entity models
- Reference implementation: `backend/app/routes/ror.py` is the closest existing pattern
- API key provided by Africa PID Alliance partnership
- Integration spec document: `backend/temp/DOCID_Add_RRID_Integration.md`

## Constraints

- **Tech stack**: Flask 3.0.3 backend, Next.js 15+ frontend, PostgreSQL, SQLAlchemy 2.0
- **Security**: SciCrunch API key must never be exposed client-side
- **DB approach**: Dedicated `docid_rrids` table (Option B from spec)
- **Entity scope**: Publications and organizations only for this milestone
- **Pattern**: Must follow existing DOCiD conventions (Blueprint routing, API proxy, AJAX interactions)
- **Commits**: No `Co-Authored-By: Claude` in git commits

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Dedicated `docid_rrids` table over generic external_identifiers | User preference for strict RRID separation | -- Pending |
| Publications + Organizations scope | Balance between flexibility and focused delivery | -- Pending |
| Full scope (endpoints + DB + UI + caching + tests) | Comprehensive delivery, skip only bulk sync | -- Pending |
| DB-level caching over Redis for resolver results | Simpler infrastructure, DOCiD already uses Flask-Caching | -- Pending |

---
*Last updated: 2026-02-24 after milestone v1.0 initialization*
