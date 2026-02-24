# Roadmap: DOCiD — v1.0 RRID Integration

## Overview

This milestone integrates RRID (Research Resource Identifier) from SciCrunch into DOCiD, following the same backend-proxy pattern used by ROR, ORCID, and RAiD. The dependency chain is strict: the database table must exist before service code can write to it, the service module must exist before the blueprint can call it, the blueprint must be registered before Next.js can proxy to it, and both backend and proxy must be validated before the frontend modal is wired in. Eight granular phases follow this chain exactly, each delivering one independently verifiable layer.

## Phases

**Phase Numbering:**
- Integer phases (1–8): Planned v1.0 milestone work
- Decimal phases (e.g., 2.1): Urgent insertions, created via `/gsd:insert-phase`

- [x] **Phase 1: Database Foundation** - Alembic migration, DocidRrid SQLAlchemy model, unique constraint, composite index *(completed 2026-02-24)*
- [x] **Phase 2: Service Layer** - `service_scicrunch.py` module, API key env var, RRID validation, ES query logic, resolver cache schema *(completed 2026-02-24)*
- [ ] **Phase 3: Flask Blueprint — Search & Resolve** - Blueprint registration, search endpoint, resolve endpoint, entity allowlist
- [ ] **Phase 4: Flask Blueprint — Attach, List, Detach** - attach/list/detach endpoints, duplicate prevention, cascade deletion
- [ ] **Phase 5: Backend Test Suite** - pytest/responses dependency upgrade, 9 test cases covering all endpoint behaviors
- [ ] **Phase 6: Frontend Proxy Routes** - 5 Next.js proxy routes forwarding to Flask, no SciCrunch keys in frontend
- [ ] **Phase 7: Frontend Search Modal** - RridSearchModal component, dual-tab layout, debounced search, AJAX interactions
- [ ] **Phase 8: Frontend Integration & Display** - Attach modal to publication detail page and organization rows, RRID chip display

## Phase Details

### Phase 1: Database Foundation
**Goal**: The `docid_rrids` table exists in PostgreSQL with all columns, constraints, and indexes that every subsequent layer depends on
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Running `flask db upgrade` creates a `docid_rrids` table with all 12 columns (id, entity_type, entity_id, rrid, rrid_name, rrid_description, rrid_resource_type, rrid_url, resolved_json, last_resolved_at, created_at, updated_at)
  2. Attempting to insert two rows with identical (entity_type, entity_id, rrid) raises a database-level UniqueConstraint violation
  3. A query plan for `SELECT * FROM docid_rrids WHERE entity_type = 'publication' AND entity_id = 1` uses the composite index (visible via `EXPLAIN`)
  4. `DocidRrid.serialize()` returns a Python dict with all model fields accessible from application code
**Plans:** 1 plan
Plans:
- [x] 01-01-PLAN.md — DocidRrid model + Alembic migration with constraints, indexes, and seed data (completed 2026-02-24)

### Phase 2: Service Layer
**Goal**: A self-contained Python module isolates all SciCrunch HTTP calls, RRID validation, and resolver cache logic behind a clean API — with the SciCrunch API key never leaving the server
**Depends on**: Phase 1
**Requirements**: INFRA-05, INFRA-06, SEARCH-07, SEARCH-08, CACHE-01, CACHE-02, CACHE-03
**Success Criteria** (what must be TRUE):
  1. `SCICRUNCH_API_KEY` is readable from the Flask app context but does not appear in any file with a `NEXT_PUBLIC_` prefix anywhere in the frontend codebase
  2. `service_scicrunch.py` defines two separate URL constants — one for `api.scicrunch.io` (search) and one for `scicrunch.org` (resolver) — and calling the search function sends the `apikey` header only to the search domain
  3. The RRID validator accepts `RRID:SCR_012345`, `RRID:AB_123456789`, `RRID:CVCL_0001` and auto-prepends `RRID:` when the prefix is absent; it rejects strings that do not match the known patterns
  4. Elasticsearch queries for exact RRID lookups use `term` queries (not `query_string`), preventing silent colon-escaping failures
  5. After a resolve call, `resolved_json` stores only the normalized subset (name, rrid, description, url, resource_type, properCitation, mentions) — not the raw ES blob
**Plans:** 2 plans

Plans:

- [ ] 02-01-PLAN.md — Config + RRID validation + SciCrunch search function
- [ ] 02-02-PLAN.md — RRID resolver with 30-day DB cache and stale fallback

### Phase 3: Flask Blueprint — Search & Resolve
**Goal**: Two working Flask endpoints let authenticated code search SciCrunch by keyword/type and resolve any known RRID to canonical metadata — all routed through the `/api/v1/rrid` blueprint
**Depends on**: Phase 2
**Requirements**: INFRA-07, INFRA-08, SEARCH-01, SEARCH-02, SEARCH-03, SEARCH-04, SEARCH-05, SEARCH-06
**Success Criteria** (what must be TRUE):
  1. `GET /api/v1/rrid/search?q=flow+cytometry` returns a JSON list where each item has `scicrunch_id`, `name`, `description`, `url`, `types`, and `rrid` fields
  2. `GET /api/v1/rrid/search?q=flow+cytometry&type=software` returns only software resources; omitting `type` defaults results to core facility resources
  3. `GET /api/v1/rrid/resolve?rrid=RRID:SCR_012345` returns `properCitation`, `mentions`, `name`, `description`, `url`, and `resource_type` extracted from the SciCrunch resolver
  4. Passing `entity_type=user_account` to any endpoint that accepts the parameter returns HTTP 400; only `publication` and `organization` are accepted
  5. The blueprint is registered in `app/__init__.py` so all `/api/v1/rrid/*` routes respond without 404
**Plans**: TBD

### Phase 4: Flask Blueprint — Attach, List, Detach
**Goal**: Three endpoints complete the RRID lifecycle — attaching an RRID to a publication or organization, listing attached RRIDs for any entity, and removing a specific RRID — with data integrity enforced at every step
**Depends on**: Phase 3
**Requirements**: ATTACH-01, ATTACH-02, ATTACH-03, ATTACH-04, ATTACH-05, ATTACH-06, ATTACH-07, ATTACH-08
**Success Criteria** (what must be TRUE):
  1. `POST /api/v1/rrid/attach` with `entity_type=publication`, a valid `entity_id`, and a valid RRID creates a row in `docid_rrids` storing the rrid value, name, description, resource_type, url, and resolved_json
  2. Posting the same RRID to the same entity a second time returns HTTP 409 Conflict with a human-readable error message (not a 500 database error)
  3. `GET /api/v1/rrid/entity?entity_type=publication&entity_id=42` returns only the RRIDs attached to publication 42
  4. `DELETE /api/v1/rrid/<rrid_id>` removes the row and returns HTTP 200; a subsequent GET for that entity no longer includes the deleted RRID
  5. Deleting a publication record from the database results in zero orphaned `docid_rrids` rows for that publication's entity_id
  6. Deleting a publication_organizations row cascades to remove its associated `docid_rrids` rows
**Plans**: TBD

### Phase 5: Backend Test Suite
**Goal**: An automated pytest suite validates every Phase 1–4 behavior with mocked SciCrunch HTTP responses, catching the non-obvious API pitfalls (colon escaping, resolver domain split, orphan rows) before any frontend code is written
**Depends on**: Phase 4
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04, TEST-05, TEST-06, TEST-07, TEST-08, TEST-09, TEST-10, TEST-11
**Success Criteria** (what must be TRUE):
  1. `pytest backend/tests/test_rrid.py` runs to completion with no import errors (requires pytest >=7.4, pytest-flask 1.3.0, responses 0.26.0)
  2. The search test mocks a SciCrunch Elasticsearch response and asserts the normalized output contains `scicrunch_id`, `name`, `description`, `url`, `types`, and `rrid` keys
  3. The resolve test mocks the resolver response and asserts `properCitation`, `mentions`, and `name` are extracted correctly
  4. The attach test verifies a `docid_rrids` row is created; the duplicate test verifies HTTP 409 is returned; the cascade test verifies rows are removed when the parent publication is deleted
  5. The validation tests confirm that invalid RRID formats and invalid `entity_type` values are rejected with appropriate error responses
**Plans**: TBD

### Phase 6: Frontend Proxy Routes
**Goal**: Five thin Next.js API routes complete the proxy chain from browser to Flask, ensuring no SciCrunch API key or direct SciCrunch URL ever appears in frontend-accessible code
**Depends on**: Phase 5
**Requirements**: PROXY-01, PROXY-02, PROXY-03, PROXY-04, PROXY-05, PROXY-06
**Success Criteria** (what must be TRUE):
  1. A browser request to `/api/rrid/search?q=flow+cytometry` returns the same normalized JSON that `GET /api/v1/rrid/search` returns from Flask
  2. A browser request to `/api/rrid/resolve?rrid=RRID:SCR_012345` returns resolver metadata from Flask
  3. A browser POST to `/api/rrid/attach` and GET to `/api/rrid/entity` and DELETE to `/api/rrid/[id]` each reach the corresponding Flask endpoint and return the same response
  4. `grep -r "NEXT_PUBLIC_SCICRUNCH" frontend/` returns zero results; `grep -r "api.scicrunch.io" frontend/` returns zero results
**Plans**: TBD

### Phase 7: Frontend Search Modal
**Goal**: A reusable `RridSearchModal` React component delivers the complete RRID search-and-attach interaction — dual-tab layout, debounced search, type filtering, and direct RRID entry with metadata preview — ready to be embedded anywhere in the app
**Depends on**: Phase 6
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05, UI-11, UI-12
**Success Criteria** (what must be TRUE):
  1. The modal renders an MUI Dialog with two tabs: "Search by Name" (keyword input, type dropdown, results list) and "Enter RRID" (text field, resolve button, metadata preview area)
  2. Typing in the search field triggers an AJAX call no sooner than 400ms after the last keystroke; rapid typing does not fire multiple simultaneous requests
  3. The type dropdown shows Core Facility, Software, Antibody, and Cell Line; Core Facility is selected by default on modal open
  4. Each search result row displays the resource name, description, resource type, and an "Attach" button; clicking "Attach" fires an AJAX POST without reloading the page
  5. On the "Enter RRID" tab, resolving a known RRID displays the name, properCitation, and mentions count before the user confirms attachment
**Plans**: TBD

### Phase 8: Frontend Integration & Display
**Goal**: The RRID search modal is wired into the publication detail page and organization rows, and attached RRIDs are displayed as interactive, type-colored chip badges that users can click to visit the SciCrunch resolver or remove from the entity
**Depends on**: Phase 7
**Requirements**: UI-06, UI-07, UI-08, UI-09, UI-10
**Success Criteria** (what must be TRUE):
  1. An "Add RRID" button appears on the publication detail page (`docid/[id]/page.jsx`); clicking it opens the RRID search modal in the publication context
  2. An "Add RRID" button appears on each organization row in the assign-docid form; clicking it opens the modal passing `entity_type=organization` and the correct `publication_organizations.id`
  3. RRIDs attached to a publication are displayed as MUI Chip badges; each badge links to `https://scicrunch.org/resolver/<RRID>` and opens in a new tab
  4. Chip badge color reflects resource type: blue for `SCR_` (software/tools), red for `AB_` (antibodies), green for `CVCL_` (cell lines)
  5. Each chip has a remove action; clicking it fires an AJAX DELETE and removes the chip from the page without a full reload
**Plans**: TBD

## Progress

**Execution Order:** 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Database Foundation | 1/1 | Complete | 2026-02-24 |
| 2. Service Layer | 2/2 | Complete | 2026-02-24 |
| 3. Flask Blueprint — Search & Resolve | 0/TBD | Not started | - |
| 4. Flask Blueprint — Attach, List, Detach | 0/TBD | Not started | - |
| 5. Backend Test Suite | 0/TBD | Not started | - |
| 6. Frontend Proxy Routes | 0/TBD | Not started | - |
| 7. Frontend Search Modal | 0/TBD | Not started | - |
| 8. Frontend Integration & Display | 0/TBD | Not started | - |
