# Requirements: DOCiD RRID Integration

**Defined:** 2026-02-24
**Core Value:** Researchers and institutions can search, resolve, and attach Research Resource Identifiers (RRIDs) to publications and organizations through DOCiD's unified PID platform.

## v1 Requirements

Requirements for milestone v1.0 RRID Integration. Each maps to roadmap phases.

### Backend Infrastructure

- [ ] **INFRA-01**: Alembic migration creates `docid_rrids` table with columns: `id` (integer PK), `entity_type` (varchar), `entity_id` (integer), `rrid` (varchar), `rrid_name` (varchar), `rrid_description` (text), `rrid_resource_type` (varchar), `rrid_url` (varchar), `resolved_json` (JSONB), `last_resolved_at` (datetime), `created_at` (datetime), `updated_at` (datetime)
- [ ] **INFRA-02**: `docid_rrids` table has `UniqueConstraint` on `(entity_type, entity_id, rrid)` to prevent duplicate attachments
- [ ] **INFRA-03**: `docid_rrids` table has composite index on `(entity_type, entity_id)` for fast lookups
- [ ] **INFRA-04**: `DocidRrid` SQLAlchemy model added to `backend/app/models.py` with `serialize()` method
- [ ] **INFRA-05**: `SCICRUNCH_API_KEY` environment variable configured server-side only (never exposed via `NEXT_PUBLIC_*` prefix)
- [ ] **INFRA-06**: `service_scicrunch.py` service module created with separate URL constants for search (`api.scicrunch.io`) and resolver (`scicrunch.org`)
- [ ] **INFRA-07**: Flask blueprint `rrid.py` registered in `app/__init__.py` under `/api/v1/rrid` prefix
- [ ] **INFRA-08**: `entity_type` parameter validated against allowlist `{"publication", "organization"}` on all endpoints that accept it

### RRID Search & Resolution

- [ ] **SEARCH-01**: User can search RRID resources by keyword through backend proxy endpoint `GET /api/v1/rrid/search`
- [ ] **SEARCH-02**: User can filter RRID search results by resource type (core facility, software, antibody, cell line) via `type` query parameter
- [ ] **SEARCH-03**: Search type defaults to "core facility" when no type parameter is provided
- [ ] **SEARCH-04**: Search results return normalized JSON with fields: `scicrunch_id`, `name`, `description`, `url`, `types`, `rrid` (curie format)
- [ ] **SEARCH-05**: User can resolve a known RRID to canonical metadata through backend proxy endpoint `GET /api/v1/rrid/resolve`
- [ ] **SEARCH-06**: Resolver endpoint returns `properCitation`, `mentions` count, `name`, `description`, `url`, and `resource_type` from SciCrunch resolver JSON
- [ ] **SEARCH-07**: RRID format validated server-side using regex covering `SCR_`, `AB_`, `CVCL_` prefixes; auto-prepends `RRID:` prefix if absent
- [ ] **SEARCH-08**: Elasticsearch queries use `term` queries for exact RRID lookups (not `query_string`) to avoid colon-escaping issues

### RRID Attachment

- [ ] **ATTACH-01**: User can attach an RRID to a publication via `POST /api/v1/rrid/attach` with `entity_type=publication` and `entity_id`
- [ ] **ATTACH-02**: User can attach an RRID to an organization (publication_organizations row) via `POST /api/v1/rrid/attach` with `entity_type=organization` and `entity_id`
- [ ] **ATTACH-03**: Attach endpoint stores RRID value, name, description, resource type, URL, and resolver metadata in `docid_rrids`
- [ ] **ATTACH-04**: Duplicate RRID attachment to the same entity returns HTTP 409 Conflict with a readable error message
- [ ] **ATTACH-05**: User can list all RRIDs attached to an entity via `GET /api/v1/rrid/entity` with `entity_type` and `entity_id` query params
- [ ] **ATTACH-06**: User can detach/remove an RRID from an entity via `DELETE /api/v1/rrid/<rrid_id>`
- [ ] **ATTACH-07**: Deleting a publication cascades to remove associated `docid_rrids` rows (application-level cascade)
- [ ] **ATTACH-08**: Deleting a publication_organization row cascades to remove associated `docid_rrids` rows (application-level cascade)

### Caching

- [ ] **CACHE-01**: Resolver metadata cached in `resolved_json` JSONB column on `docid_rrids` after first resolve
- [ ] **CACHE-02**: Cached resolver data reused if `last_resolved_at` is less than 30 days old
- [ ] **CACHE-03**: `resolved_json` stores normalized subset (`name`, `rrid`, `description`, `url`, `resource_type`, `properCitation`, `mentions`) not raw blob

### Frontend Proxy

- [ ] **PROXY-01**: Next.js API proxy route for RRID search (`/api/rrid/search`) forwarding to Flask backend
- [ ] **PROXY-02**: Next.js API proxy route for RRID resolve (`/api/rrid/resolve`) forwarding to Flask backend
- [ ] **PROXY-03**: Next.js API proxy route for RRID attach (`/api/rrid/attach`) forwarding to Flask backend
- [ ] **PROXY-04**: Next.js API proxy route for RRID list by entity (`/api/rrid/entity`) forwarding to Flask backend
- [ ] **PROXY-05**: Next.js API proxy route for RRID detach (`/api/rrid/[id]`) forwarding to Flask backend
- [ ] **PROXY-06**: No SciCrunch API key or direct SciCrunch URLs present in any frontend code

### Frontend UI

- [ ] **UI-01**: RRID search modal component (`RridSearchModal.jsx`) using MUI Dialog, reusable across publication and organization contexts
- [ ] **UI-02**: Modal has dual-tab layout: Tab 1 "Search by Name" (keyword input + type dropdown + results list), Tab 2 "Enter RRID" (text field + resolve button + metadata preview)
- [ ] **UI-03**: Search tab type dropdown includes options: Core Facility (default), Software, Antibody, Cell Line
- [ ] **UI-04**: Search results displayed in list with name, description, resource type, and "Attach" button per result
- [ ] **UI-05**: Direct RRID entry tab shows resolved metadata preview (name, properCitation, mentions count) before user confirms attachment
- [ ] **UI-06**: "Add RRID" button appears on publication detail page (`docid/[id]/page.jsx`) opening the search modal
- [ ] **UI-07**: "Add RRID" button appears on organization rows in the assign-docid form, passing `entity_type=organization` and `entity_id=publication_organizations.id`
- [ ] **UI-08**: Attached RRIDs displayed on publication detail page as clickable MUI Chip badges linking to `https://scicrunch.org/resolver/<RRID>`
- [ ] **UI-09**: RRID chips are color-coded by type: `SCR_` = blue (tools/software), `AB_` = red (antibody), `CVCL_` = green (cell line)
- [ ] **UI-10**: Each displayed RRID chip has a remove/detach action (icon button or menu)
- [ ] **UI-11**: All RRID interactions (search, attach, detach) use AJAX requests without full page reload
- [ ] **UI-12**: Search input has 400-500ms debounce before firing AJAX request to prevent API hammering

### Testing

- [ ] **TEST-01**: Upgrade `pytest` from 2.6.0 to >=7.4 and add `pytest-flask==1.3.0` to test dependencies
- [ ] **TEST-02**: Add `responses==0.26.0` for HTTP mocking and upgrade `requests` to 2.32.3 for compatibility
- [ ] **TEST-03**: Test RRID search endpoint with mocked SciCrunch Elasticsearch response, assert normalized output shape
- [ ] **TEST-04**: Test RRID resolve endpoint with mocked resolver response, assert metadata extraction (properCitation, mentions, name)
- [ ] **TEST-05**: Test RRID attach endpoint creates `docid_rrids` row with correct fields
- [ ] **TEST-06**: Test duplicate RRID attachment returns 409 Conflict
- [ ] **TEST-07**: Test RRID format validation rejects invalid formats and accepts valid `RRID:SCR_*`, `RRID:AB_*`, `RRID:CVCL_*`
- [ ] **TEST-08**: Test `entity_type` allowlist rejects invalid entity types
- [ ] **TEST-09**: Test cascade deletion: deleting publication removes associated `docid_rrids` rows
- [ ] **TEST-10**: Test list endpoint returns RRIDs filtered by `entity_type` and `entity_id`
- [ ] **TEST-11**: Test detach endpoint removes `docid_rrids` row by ID

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Bulk Sync

- **SYNC-01**: Periodic background job downloads all core facility records from SciCrunch for local fast search
- **SYNC-02**: Local search index for RRID resources with full-text search capability

### Extended Entity Support

- **EXT-01**: User can attach RRID to creator records (ORCID-linked researchers)
- **EXT-02**: User can attach RRID to project records (RAiD-linked projects)

### Additional Resource Types

- **TYPE-01**: Model Organism RRID support (MGI, ZFIN, RGSC prefixes) with separate index queries

### Enhanced Display

- **DISP-01**: RRID display on standalone organization management pages (not just publication context)
- **DISP-02**: RRID usage statistics and analytics dashboard

## Out of Scope

| Feature | Reason |
|---------|--------|
| Direct browser-to-SciCrunch API calls | API key would be exposed client-side; violates security constraints |
| Generic `docid_external_identifiers` table | User explicitly chose Option B (dedicated `docid_rrids` table) |
| Redis caching for search results | DOCiD uses Flask-Caching; adding Redis infrastructure is disproportionate for this milestone |
| RRID autocomplete/typeahead | SciCrunch has variable latency (up to 25s); debounced button-triggered search is the safer UX |
| Bulk RRID sync for local search | Requires Elasticsearch scroll, background jobs, sync scheduling — deferred to v2 |
| RRID attachment to creators/projects | No concrete user story; publications and organizations cover the primary use case |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INFRA-01 | — | Pending |
| INFRA-02 | — | Pending |
| INFRA-03 | — | Pending |
| INFRA-04 | — | Pending |
| INFRA-05 | — | Pending |
| INFRA-06 | — | Pending |
| INFRA-07 | — | Pending |
| INFRA-08 | — | Pending |
| SEARCH-01 | — | Pending |
| SEARCH-02 | — | Pending |
| SEARCH-03 | — | Pending |
| SEARCH-04 | — | Pending |
| SEARCH-05 | — | Pending |
| SEARCH-06 | — | Pending |
| SEARCH-07 | — | Pending |
| SEARCH-08 | — | Pending |
| ATTACH-01 | — | Pending |
| ATTACH-02 | — | Pending |
| ATTACH-03 | — | Pending |
| ATTACH-04 | — | Pending |
| ATTACH-05 | — | Pending |
| ATTACH-06 | — | Pending |
| ATTACH-07 | — | Pending |
| ATTACH-08 | — | Pending |
| CACHE-01 | — | Pending |
| CACHE-02 | — | Pending |
| CACHE-03 | — | Pending |
| PROXY-01 | — | Pending |
| PROXY-02 | — | Pending |
| PROXY-03 | — | Pending |
| PROXY-04 | — | Pending |
| PROXY-05 | — | Pending |
| PROXY-06 | — | Pending |
| UI-01 | — | Pending |
| UI-02 | — | Pending |
| UI-03 | — | Pending |
| UI-04 | — | Pending |
| UI-05 | — | Pending |
| UI-06 | — | Pending |
| UI-07 | — | Pending |
| UI-08 | — | Pending |
| UI-09 | — | Pending |
| UI-10 | — | Pending |
| UI-11 | — | Pending |
| UI-12 | — | Pending |
| TEST-01 | — | Pending |
| TEST-02 | — | Pending |
| TEST-03 | — | Pending |
| TEST-04 | — | Pending |
| TEST-05 | — | Pending |
| TEST-06 | — | Pending |
| TEST-07 | — | Pending |
| TEST-08 | — | Pending |
| TEST-09 | — | Pending |
| TEST-10 | — | Pending |
| TEST-11 | — | Pending |

**Coverage:**
- v1 requirements: 50 total
- Mapped to phases: 0
- Unmapped: 50

---
*Requirements defined: 2026-02-24*
*Last updated: 2026-02-24 after initial definition*
