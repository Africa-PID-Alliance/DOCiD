# Project Research Summary

**Project:** RRID/SciCrunch Integration — DOCiD PID Platform
**Domain:** Research Resource Identifier (RRID) integration into existing Flask + Next.js scholarly PID platform
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

DOCiD is adding RRID (Research Resource Identifier) support to its existing PID platform, following the same backend-proxy pattern already in place for ORCID, ROR, and RAiD. RRIDs are persistent identifiers for research resources (software tools, antibodies, cell lines, core facilities) managed by the SciCrunch registry. The primary use case for this milestone is the Africa PID Alliance partnership: African core facilities need to be credited in publications via RRIDs. The recommended approach follows the established DOCiD integration pattern exactly — a Flask Blueprint proxying SciCrunch API calls with server-side API key injection, a dedicated `docid_rrids` PostgreSQL table with polymorphic entity references, and a React modal component following the existing ORCID/ROR search-and-attach UX pattern.

The recommended stack requires only one new Python dependency (`responses` for HTTP mocking in tests) and zero new frontend packages. All other needs are satisfied by the existing stack: `requests` for SciCrunch HTTP calls, `flask-caching` for search result caching, PostgreSQL JSONB for resolver metadata caching, SQLAlchemy for the model, and Flask-Migrate for the table migration. The implementation is scoped to four phases: backend foundation (model + migration + service + blueprint + tests), frontend proxy routes, frontend UI (modal component + publication detail page integration), and enhancement features (citation display, type badges, mention counts).

The principal risks are security (API key exposure via `NEXT_PUBLIC_` prefix or direct browser-to-SciCrunch calls) and data integrity (orphan `docid_rrids` rows when parent entities are deleted, due to the polymorphic FK design). Both are avoidable with established patterns from the existing codebase. SciCrunch API behavior introduces two non-obvious pitfalls: colon escaping in Elasticsearch `query_string` clauses, and a domain split between the search API (`api.scicrunch.io`) and the resolver (`scicrunch.org`) that must be treated as separate services.

---

## Key Findings

### Recommended Stack

The integration requires no new infrastructure. All SciCrunch HTTP calls use the existing `requests` library directly — no SciCrunch Python SDK exists on PyPI. RRID format validation uses a three-line Python `re` stdlib regex covering the `SCR_`, `AB_`, and `CVCL_` prefixes relevant to this milestone. Resolver metadata is cached in a PostgreSQL JSONB column (per the project's explicit Option B decision), keeping infrastructure simple. Search result caching uses the already-installed `flask-caching`, with a recommended upgrade from `CACHE_TYPE = 'simple'` to Redis in production.

The one concrete version conflict to resolve before starting: `requests==2.28.0` in `requirements.txt` is incompatible with `responses>=0.26.0` (test mock library). The recommended fix is upgrading `requests` to `2.32.3` (safe, backwards-compatible API). The existing `pytest==2.6.0` (from 2014) must also be upgraded to `>=7.4,<9` to support modern fixtures.

**Core technologies:**
- `requests` (existing, upgrade to 2.32.3): SciCrunch HTTP calls — no SDK exists; plain `requests.post/get` matches all other integrations in DOCiD
- `sqlalchemy.dialects.postgresql.JSONB` (existing): resolver metadata cache column — PostgreSQL JSONB over Redis for long-lived, per-RRID data
- `flask-caching` (existing, upgrade `CACHE_TYPE` to Redis for prod): search result caching — already initialized in `__init__.py`; upgrade is config-only
- `re` stdlib: RRID format validation — no external package exists; regex is sufficient for all milestone-scoped prefixes
- `responses==0.26.0` (new, test-only): HTTP mocking — cleaner DSL than `unittest.mock.patch` for URL-specific mocks
- `pytest>=7.4,<9` + `pytest-flask==1.3.0` (new, test-only): test infrastructure — existing `pytest==2.6.0` is too old for modern fixtures

### Expected Features

The feature set follows the same attach/search/display lifecycle as existing DOCiD identifiers (ORCID, ROR, RAiD). Core facility resources are the default search type. The distinction between RRID (resource acknowledgement) and ROR (organizational affiliation) must be preserved in the UI — they serve different metadata slots even when applied to the same facility.

**Must have (table stakes — v1):**
- `docid_rrids` Alembic migration with `entity_type`, `entity_id`, `rrid`, `resolved_json`, `last_resolved_at`, and `UniqueConstraint(entity_type, entity_id, rrid)` — everything else depends on this
- Flask search endpoint proxying `RIN_Tool_pr/_search` with keyword + type filter (default: core facility)
- Flask resolve endpoint proxying `scicrunch.org/resolver/<RRID>.json` with DB cache write
- Flask attach, list, and detach endpoints
- Duplicate prevention via DB-level `UniqueConstraint` returning 409 Conflict
- Next.js API proxy routes for all five Flask endpoints
- RRID search modal on publication detail page (dual-tab: search by name + enter RRID directly)
- RRID search modal on organization rows in assign-docid form
- RRID display on `docid/[id]/page.jsx` as linked, type-colored MUI chip badges
- RRID format validation (server-side regex; normalize by auto-prepending `RRID:` prefix if absent)
- Backend tests: mock SciCrunch responses, assert normalized output shape, assert schema validation

**Should have (competitive — add within this milestone if time allows):**
- Dual-tab modal UX (search by name / enter RRID directly) — low effort, follows `OrganizationsForm.jsx` pattern exactly
- Type-colored badge on display (`SCR_` = blue, `AB_` = red, `CVCL_` = green)
- `properCitation` shown at attach confirmation time — teaches correct methods-section citation format
- RRID display on organization management pages

**Defer (v2+):**
- Bulk RRID sync for local fast search — requires Elasticsearch scroll, background jobs, sync scheduling
- RRID attachment to creators (ORCID records) or projects (RAiD records) — no concrete user story yet
- Model Organism RRID support (MGI, ZFIN, RGSC) — different indices, different resolver patterns

### Architecture Approach

The architecture is a strict extension of the existing DOCiD layered pattern: Next.js page components fire AJAX calls to Next.js proxy routes, which forward to Flask Blueprint endpoints, which call a dedicated service module for external API calls. The `DocidRrid` model lives in the single `app/models.py` file (project convention — no separate models file). All SciCrunch credentials stay on the Flask server; the Next.js layer never sees the API key.

**Major components:**
1. `backend/app/routes/rrid.py` (new) — Flask Blueprint `/api/v1/rrid/*`; request validation, response shaping; thin layer delegating to service
2. `backend/app/service_scicrunch.py` (new) — SciCrunch HTTP wrapper; injects `apikey` header on search calls; separate URL constants for search vs resolver; follows `service_crossref.py` pattern
3. `DocidRrid` in `backend/app/models.py` (new model) — polymorphic association table (`entity_type` + `entity_id`); `resolved_json` JSONB cache; `UniqueConstraint`; composite index on `(entity_type, entity_id)`
4. `backend/migrations/versions/<hash>_add_docid_rrids_table.py` (new) — Alembic migration; must include index and unique constraint
5. `frontend/src/app/api/rrid/*/route.js` (new) — Next.js proxy routes; thin pass-through identical to existing `api/ror/` routes
6. `frontend/src/app/components/RridSearchModal.jsx` (new) — reusable MUI Dialog; dual-tab (search + direct entry); shared between publication detail page and organization rows

**Build order (dependency-driven):**
1. Model + migration (DB foundation)
2. Service module (SciCrunch HTTP isolation)
3. Flask blueprint + blueprint registration
4. Backend tests
5. Next.js proxy routes
6. `RridSearchModal.jsx` component
7. Modify `docid/[id]/page.jsx` for display + attach

### Critical Pitfalls

1. **Colon escaping in Elasticsearch `query_string`** — `RRID:SCR_012345` is silently parsed as `field:value` by ES, returning 0 hits with no error. Use `term` queries for exact RRID lookups: `{"term": {"rrid.curie": "RRID:SCR_012345"}}`. For free-text search, use `match` on `item.name`, not `query_string` on `rrid.curie`.

2. **Search and resolver on different domains** — `api.scicrunch.io` (search, requires `apikey` header) and `scicrunch.org` (resolver, no API key needed) must be defined as two separate URL constants. Constructing the resolver URL from the search base produces a 404. Define `SCICRUNCH_SEARCH_BASE` and `SCICRUNCH_RESOLVER_BASE` separately in `service_scicrunch.py`.

3. **Polymorphic FK — no DB-level referential integrity** — PostgreSQL cannot enforce a FK constraint across two parent tables from a single `entity_id` column. Orphan `docid_rrids` rows accumulate silently when publications are deleted. Mitigate with SQLAlchemy `relationship()` + `cascade="all, delete-orphan"` on `Publications` and `PublicationOrganization`, or a cleanup migration. Verify with a test: delete publication → confirm RRID rows are removed.

4. **API key exposure via `NEXT_PUBLIC_` prefix** — if `SCICRUNCH_API_KEY` is set as `NEXT_PUBLIC_SCICRUNCH_API_KEY`, the key is embedded in the Next.js JavaScript bundle and visible in DevTools. The key must only live in the Flask backend `.env`. Add `grep -r "NEXT_PUBLIC_SCICRUNCH" frontend/` to the pre-deploy checklist.

5. **`entity_type` allowlist missing** — user-supplied `entity_type` without an allowlist allows `entity_type=user_accounts` in attach/detach queries. Enforce `ALLOWED_ENTITY_TYPES = {"publication", "organization"}` before any DB operation in the Flask blueprint.

---

## Implications for Roadmap

Based on the dependency chain identified in research, four phases are recommended. The ordering is strictly dependency-driven: database before service before routes before UI, with tests validating the backend before the frontend is built.

### Phase 1: Backend Foundation

**Rationale:** Every other component depends on the `docid_rrids` table and Flask endpoints. The DB migration must run before any endpoint can write records. The service module and blueprint must exist before Next.js proxies can forward to them. Building backend-first also prevents the critical API key exposure pitfall — the proxy chain is established before any frontend line is written.

**Delivers:** Working Flask API for RRID search, resolve, attach, list, and detach. `docid_rrids` table with unique constraint and index. `SCICRUNCH_API_KEY` wired server-side only.

**Addresses features:** Alembic migration, search endpoint, resolve endpoint with DB cache write, attach endpoint, list endpoint, detach endpoint, duplicate prevention (UniqueConstraint), RRID format validation, `entity_type` allowlist.

**Avoids pitfalls:** Colon escaping (tested in unit tests), domain split (two URL constants), polymorphic FK orphans (cascade defined), API key exposure (backend-only env var), `entity_type` injection (allowlist enforced).

**Files:** `backend/app/models.py` (DocidRrid model), `backend/migrations/versions/<hash>_add_docid_rrids_table.py`, `backend/app/service_scicrunch.py`, `backend/app/routes/rrid.py`, `backend/app/__init__.py` (blueprint registration), `backend/.env` / `.env.example`.

### Phase 2: Backend Tests

**Rationale:** Tests validate the Phase 1 foundation before any frontend work begins. This ordering catches integration bugs (colon escaping, resolver URL suffix, duplicate constraint) at the lowest-cost point — before they propagate into UI code.

**Delivers:** Pytest test suite covering service request/parse (with `responses` mock), endpoint schema validation (with Flask test client), model constraint verification (unique RRID per entity), and cascade deletion verification.

**Addresses features:** Backend tests (P1 acceptance criterion in PROJECT.md).

**Avoids pitfalls:** Resolver URL missing `.json` suffix, colon escaping in query_string, orphan rows on parent deletion, missing auth on attach/detach endpoints.

**Files:** `backend/tests/test_rrid.py`, `requirements.txt` updates (`requests==2.32.3`, `responses==0.26.0`, `pytest>=7.4,<9`, `pytest-flask==1.3.0`).

**Research flag:** Standard pytest patterns — no additional phase research needed. The `responses` library version conflict resolution (upgrade `requests` to 2.32.3) is well-documented.

### Phase 3: Frontend Proxy Routes

**Rationale:** Next.js proxy routes are the bridge between the UI and the validated Flask API. They must exist before any UI component can be tested end-to-end. The proxy layer is thin (identical to the existing `api/ror/` routes) and should be built as a discrete step to verify the full request chain before building the modal.

**Delivers:** Working end-to-end HTTP path from browser to SciCrunch via Next.js proxy and Flask backend.

**Addresses features:** Next.js API proxy routes for all five Flask endpoints.

**Avoids pitfalls:** Missing `/api/v1/` prefix in proxy URL (align with Flask blueprint URL convention), debug verification of no direct `api.scicrunch.io` calls from browser.

**Files:** `frontend/src/app/api/rrid/search/route.js`, `frontend/src/app/api/rrid/resolve/route.js`, `frontend/src/app/api/rrid/attach/route.js`, `frontend/src/app/api/rrid/[entity_type]/[entity_id]/route.js`.

**Research flag:** Established Next.js App Router proxy pattern — follow `frontend/src/app/api/ror/search-organization/route.js` exactly. No additional research needed.

### Phase 4: Frontend UI

**Rationale:** UI components are built last because they depend on working proxy routes and a validated Flask API. The `RridSearchModal.jsx` component is extracted as a reusable component (needed on publication detail page and organization rows) before modifying existing pages. The publication detail page modification is the final integration step.

**Delivers:** End-to-end RRID search, attach, and display flow visible to users. Type-colored RRID chip badges on publication detail page.

**Addresses features:** RRID search modal on publication detail page, RRID search modal on organization rows in assign-docid form, RRID display on `docid/[id]/page.jsx`, dual-tab modal UX (search + direct RRID entry), type-colored badge display.

**Avoids pitfalls:** Full page reload on attach (AJAX-only per project CLAUDE.md), search modal state reset between Publications and Organizations tabs (preserve state in component), no debounce on search input (400-500ms debounce before firing AJAX).

**Files:** `frontend/src/app/components/RridSearchModal.jsx`, `frontend/src/app/docid/[id]/page.jsx` (modified).

**Research flag:** The dual-tab MUI modal pattern is already implemented in `OrganizationsForm.jsx` — follow that pattern directly. No additional research needed.

### Phase Ordering Rationale

- **DB before code:** The `docid_rrids` table must exist before any Flask endpoint can write. Migration is the single hard dependency for everything above it.
- **Backend before frontend:** The Flask blueprint must be operational before Next.js proxies have anything to forward to. Building frontend first creates untestable code.
- **Tests before proxy:** Backend tests catch the non-obvious SciCrunch API pitfalls (colon escaping, resolver domain split, resolver URL suffix) at the cheapest point.
- **Proxy before modal:** The proxy routes are thin and fast to build; verifying the full request chain before building the modal reduces debugging surface area.
- **Modal before page modification:** Extracting `RridSearchModal.jsx` as a standalone component first ensures the reusable component is correct before wiring it into existing pages.

### Research Flags

Phases needing no additional research — established patterns throughout:
- **Phase 1:** ROR blueprint (`backend/app/routes/ror.py`) and service modules (`service_crossref.py`, `service_codra.py`) are direct references for the implementation pattern. SciCrunch API Handbook (docs.scicrunch.io) documents all endpoint shapes.
- **Phase 2:** `responses` and `pytest-flask` are well-documented. The version conflict fix (requests 2.32.3) is straightforward.
- **Phase 3:** `frontend/src/app/api/ror/search-organization/route.js` is a direct reference template.
- **Phase 4:** `OrganizationsForm.jsx` dual-tab pattern and MUI Dialog are direct references.

No phase requires a `gsd:research-phase` call. All external dependencies are fully documented in the SciCrunch API Handbook and the existing DOCiD codebase provides implementation references for every new component.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All existing package versions verified directly from `requirements.txt`. New dependencies (`responses`, `pytest-flask`) verified on PyPI. Version conflict identified and resolution confirmed. |
| Features | HIGH | Feature set derived from official SciCrunch API Handbook, rrids.org documentation, and direct inspection of existing DOCiD integration patterns (ROR, ORCID, RAiD, LocalContext). |
| Architecture | HIGH | Architecture is an extension of verified existing codebase patterns. All component boundaries confirmed by direct inspection of `routes/ror.py`, `models.py`, `__init__.py`, and Next.js proxy routes. |
| Pitfalls | HIGH (codebase) / MEDIUM (SciCrunch API limits) | All codebase-level pitfalls verified against actual code. SciCrunch API rate limits are undocumented; behavior under load is inferred from timeout settings in the API spec. |

**Overall confidence:** HIGH

### Gaps to Address

- **SciCrunch rate limits:** The SciCrunch API Handbook does not publish rate limit thresholds for the Africa PID Alliance key. The 400-500ms debounce and `size=10` cap are defensive measures. If rate limiting is encountered during testing, add `@cache.cached(timeout=300)` on the search endpoint as the first mitigation.
- **`entity_type` string vs DB CHECK constraint:** PITFALLS.md recommends a DB-level `CHECK` constraint or Python `Enum` for `entity_type` to prevent typo-driven silent bugs. The migration phase should decide between a `CHECK` constraint in the Alembic migration vs. Python-level `Enum` validation. Either is acceptable; the Python allowlist in the blueprint is the minimum viable safety net.
- **Resolver cache TTL:** The 30-day resolver cache TTL is stated in PROJECT.md but not validated against SciCrunch resolver update frequency. If resolver metadata changes significantly (resource name corrections, RRID status changes), cache staleness could surface. Acceptable risk for v1; revisit if users report stale data.
- **`resolved_json` storage strategy:** PITFALLS.md flags storing the full ES `_source` blob (50-200 KB per RRID) as a performance risk when fetching publications with multiple RRIDs. For MVP, store the normalized subset `{name, rrid, description, url, resource_type}` in `resolved_json` rather than the raw blob. This decision should be explicit in the Phase 1 implementation.

---

## Sources

### Primary (HIGH confidence)

- SciCrunch API Handbook (docs.scicrunch.io) — search endpoint format, `RIN_Tool_pr` index, resolver URL, authentication, field paths, `_source` schema
- DOCiD codebase — `backend/app/routes/ror.py`, `backend/app/models.py`, `backend/app/__init__.py`, `backend/app/routes/comments.py`, `frontend/src/app/api/ror/search-organization/route.js`, `frontend/src/app/assign-docid/components/OrganizationsForm.jsx`, `backend/requirements.txt`
- DOCiD integration spec — `backend/temp/DOCID_Add_RRID_Integration.md`
- DOCiD planning — `.planning/PROJECT.md`
- PyPI: `responses==0.26.0`, `pytest-flask==1.3.0` — release notes and compatibility verified
- SQLAlchemy 2.0 docs — JSONB dialect import, cascade patterns

### Secondary (MEDIUM confidence)

- rrids.org (2024) — RRID vs ROR distinction for facilities; RRID system documentation
- INCF — Research Resource Identifier background
- NIH ORIP — RRID context
- SciCrunch GitHub API-Handbook — basic-rin-search-examples.md (Elasticsearch query patterns)

### Tertiary (LOW confidence — confirm during implementation)

- SciCrunch rate limits — undocumented; defensive assumptions from timeout settings in integration spec
- RRID digit ranges for `SCR_` and `AB_` prefixes — confirmed from resolver sample data but full range spec not published

---

*Research completed: 2026-02-24*
*Ready for roadmap: yes*
