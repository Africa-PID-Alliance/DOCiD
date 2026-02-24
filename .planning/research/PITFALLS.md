# Pitfalls Research

**Domain:** RRID/SciCrunch Integration into Existing DOCiD Platform
**Researched:** 2026-02-24
**Confidence:** HIGH (codebase verified) / MEDIUM (SciCrunch API behavior, rate limits undocumented)

---

## Critical Pitfalls

### Pitfall 1: Colon Escaping in Elasticsearch `rrid.curie` Queries

**What goes wrong:**
When searching or resolving an RRID by its identifier value via the SciCrunch Elasticsearch gateway, the colon in `RRID:SCR_012345` must be escaped as `RRID\\:SCR_012345` inside a `query_string` clause. Sending `RRID:SCR_012345` unescaped to a `query_string` query causes the Elasticsearch parser to interpret `RRID` as a field name and `SCR_012345` as a value, producing zero hits or a parse error — not a 4xx, just silently empty results.

**Why it happens:**
Developers see the RRID format and construct `{"query_string": {"query": "RRID:SCR_012345", "default_field": "rrid.curie"}}` following the Elasticsearch query string syntax. The colon is a reserved Elasticsearch query syntax character. The SciCrunch integration spec reference implementation uses `query_string` for free-text but does not show the escaped form for RRID-direct lookups.

**How to avoid:**
When querying `rrid.curie` by exact value, use a `term` query instead of `query_string`:
```python
{"query": {"term": {"rrid.curie": "RRID:SCR_012345"}}}
```
Or if `query_string` is required, escape the colon:
```python
{"query": {"query_string": {"query": "RRID\\:SCR_012345", "default_field": "rrid.curie"}}}
```
For the search endpoint (free-text), use `match` or `multi_match` against `item.name` — not `query_string` against `rrid.curie`.

**Warning signs:**
- Search returns 0 hits for a known valid RRID like `RRID:SCR_000415` when queried by exact RRID value
- No HTTP error is raised — the API returns `{"hits": {"total": 0, "hits": []}}` with a 200 OK

**Phase to address:**
Backend blueprint phase (Phase 1). Add a unit test that verifies a known RRID returns exactly one hit.

---

### Pitfall 2: Wrong Field Path for Type Filtering — `item.types.name` vs `item.types.name.aggregate`

**What goes wrong:**
The integration spec uses `{"match_phrase": {"item.types.name": "core facility"}}` for filtering by resource type. However, the SciCrunch RIN Elasticsearch data model exposes two sub-fields: `item.types.name` (analyzed/tokenized, for full-text) and `item.types.name.aggregate` (keyword, for exact matching). Using `match_phrase` on the tokenized field may return partial matches or miss records where the type string is stored with different case or alongside other tokens. For `term` filtering, the `.aggregate` keyword sub-field must be used.

**Why it happens:**
The spec document shows `match_phrase` on `item.types.name` as a working example. Developers copy this pattern and it often works for common types like "core facility", but fails silently for less common types or when type strings are stored with slightly different casing.

**How to avoid:**
For exact type filtering, use `term` against the `.aggregate` keyword sub-field:
```python
{"term": {"item.types.name.aggregate": "core facility"}}
```
For the search `type` parameter that accepts user-provided values, normalize to lowercase before constructing the query. Test with at least three resource types (software, antibody, core facility) at integration time.

**Warning signs:**
- Filtering by `type=software` returns results that include non-software resources
- Type filtering works for "core facility" but fails for "software application" or "antibody"

**Phase to address:**
Backend blueprint phase (Phase 1). Verified by testing search with `type=software` and confirming results are constrained.

---

### Pitfall 3: Resolver and Search Are on Different Domains — CORS and Proxy Configuration

**What goes wrong:**
The SciCrunch search endpoint is at `https://api.scicrunch.io/elastic/v1/...` while the RRID resolver is at `https://scicrunch.org/resolver/<RRID>.json`. These are different hostnames. If the Flask proxy sets up connection pooling, session-level timeouts, or domain-allowlists for one domain, they do not apply to the other. More critically, the resolver endpoint at `scicrunch.org` does not require the `apikey` header — sending the key header to it is harmless but unnecessary. Forgetting this split causes confusion when building tests or when the resolver starts failing independently of the search API (different CDN, different outage domain).

**Why it happens:**
Developers define `SCICRUNCH_BASE_URL = "https://api.scicrunch.io"` and then attempt to construct the resolver URL from the same base, producing `https://api.scicrunch.io/resolver/RRID:SCR_012345.json` — which returns a 404.

**How to avoid:**
Define two separate constants:
```python
SCICRUNCH_SEARCH_BASE = "https://api.scicrunch.io/elastic/v1"
SCICRUNCH_RESOLVER_BASE = "https://scicrunch.org/resolver"
```
Structure timeouts separately. In the Flask config, set `SCICRUNCH_SEARCH_TIMEOUT = 25` and `SCICRUNCH_RESOLVER_TIMEOUT = 15` (resolver is lighter). The spec reference implementation already handles this correctly — do not consolidate the URLs.

**Warning signs:**
- 404 responses when resolving a valid RRID
- Tests pass for search but fail for resolve, or vice versa
- Log shows requests going to `api.scicrunch.io/resolver/...`

**Phase to address:**
Backend blueprint phase (Phase 1). Resolver URL constant must be verified in tests.

---

### Pitfall 4: Polymorphic FK Design Without DB-Level Referential Integrity

**What goes wrong:**
The chosen `docid_rrids` table uses `entity_type` (varchar) + `entity_id` (integer) to reference either `publications.id` or `publication_organizations.id`. PostgreSQL cannot enforce a foreign key constraint across two different parent tables from a single column pair. This means orphan rows accumulate silently: if a publication is deleted without deleting its RRIDs first, the RRID rows remain with a dangling `entity_id` pointing to nothing. SQLAlchemy's `cascade="all, delete-orphan"` cannot be applied to a polymorphic association without explicit relationship declarations on both parent models.

**Why it happens:**
The `docid_rrids` table design mirrors the Option B from the integration spec. The spec correctly names the fields but does not spell out that PostgreSQL referential integrity enforcement is impossible for this pattern. Developers add the table but forget to add application-level cascade logic, and the Publications model already has `cascade="all, delete-orphan"` for its direct children (files, creators, organizations) but not for a table it does not have a declared relationship to.

**How to avoid:**
Add explicit `relationship()` declarations on both `Publications` and `PublicationOrganization` pointing to `DocidRrids`:
```python
# In Publications model
docid_rrids = relationship(
    'DocidRrids',
    primaryjoin="and_(DocidRrids.entity_type=='publication', "
                "DocidRrids.entity_id==foreign(DocidRrids.entity_id))",
    cascade="all, delete-orphan",
    viewonly=False
)
```
Alternatively (simpler): add a DB-level trigger or enforce deletion via the detach endpoint. Also add a composite index on `(entity_type, entity_id)` and a unique constraint on `(entity_type, entity_id, rrid)` to prevent duplicate attachments.

**Warning signs:**
- Deleting a publication does not remove its associated RRID rows
- `docid_rrids` table grows unboundedly; entity_ids no longer match any parent row
- No index on `(entity_type, entity_id)` — queries slow down as table grows

**Phase to address:**
Database migration phase (Phase 1 or dedicated schema phase). The unique constraint and index must be in the Alembic migration. The cascade logic must be verified by a test that deletes a publication and checks that its RRID rows are gone.

---

### Pitfall 5: API Key Exposed via Next.js API Route Misconfiguration

**What goes wrong:**
The DOCiD frontend uses Next.js API routes to proxy backend calls (see `frontend/src/app/api/`). If a developer adds a proxy route that calls SciCrunch directly from the Next.js server route (instead of routing through Flask), and that route passes the API key in a response body, header, or via `NEXT_PUBLIC_` environment variable, the key becomes visible to browsers. `NEXT_PUBLIC_` prefixed variables are embedded into the client bundle at build time.

**Why it happens:**
The Next.js frontend already has API proxy routes for Flask endpoints. When implementing RRID search, a developer might shortcut the Flask layer and call `https://api.scicrunch.io` directly from a Next.js API route using `NEXT_PUBLIC_SCICRUNCH_API_KEY`. This removes one network hop and seems efficient but violates the security constraint stated in PROJECT.md.

**How to avoid:**
The `SCICRUNCH_API_KEY` environment variable must only be set on the Flask backend server. It must never be prefixed with `NEXT_PUBLIC_`. The Next.js API routes for RRID must call `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/integrations/rrid/*` (the Flask proxy), not `api.scicrunch.io` directly. Verify with: `grep -r "scicrunch.io" frontend/src/` — should return no results.

**Warning signs:**
- `NEXT_PUBLIC_SCICRUNCH_API_KEY` appears anywhere in the Next.js codebase
- Browser DevTools network tab shows requests going directly to `api.scicrunch.io`
- The API key appears in a JavaScript bundle or page source

**Phase to address:**
Backend blueprint phase (Phase 1, before any frontend work). Establish the proxy chain before writing a single frontend line. Document in env `.env.example` that `SCICRUNCH_API_KEY` is backend-only.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `r.raise_for_status()` without catching `requests.exceptions.RequestException` | Simpler code | SciCrunch 5xx/timeout raises an unhandled exception in Flask, returns HTML error page to frontend | Never — always catch and return structured JSON |
| Storing raw resolver JSON in `resolved_json` JSONB without normalizing | Faster implementation | Schema changes in SciCrunch resolver response break application-level reads silently | Acceptable for MVP if resolver response is accessed only via `resolved_json['hits'][0]['_source']` path with `.get()` guards |
| Reusing the `cache = Cache()` with `CACHE_TYPE = 'simple'` (already in `__init__.py`) for RRID search results | No new infrastructure | `simple` cache is in-process and does not persist across Gunicorn workers; concurrent workers have separate caches, reducing cache hit rate | Acceptable at current scale; document the limitation |
| Hardcoding `RIN_Tool_pr` as the only search index | Covers core facility use case | Antibody and cell line searches require different indices (`RIN_Antibody_pr`, `RIN_CellLine_pr`); adding them later requires schema changes | Acceptable for MVP if the scope is explicitly limited to tools/software/core facilities |
| `entity_type` as a free-form string (e.g., `"publication"`, `"organization"`) | No migration needed for new types | Typos in `entity_type` produce silent bugs; no constraint prevents `"publications"` vs `"publication"` | Never — use a DB-level `CHECK` constraint or Python `Enum` |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| SciCrunch Search (`api.scicrunch.io`) | Sending `"Content-Type": "application/json"` without also sending `"apikey": key` header — the key is required on every request, not just the first | Always inject both headers in every `requests.post()` call via a helper function `_scicrunch_headers()` |
| SciCrunch Search | Using `GET` for the Elasticsearch search endpoint — `_search` supports both GET (with `q=`) and POST (with JSON body); the POST/JSON form is required for compound bool queries with `must` clauses | Use `requests.post()` with `json=payload` for all compound queries |
| RRID Resolver (`scicrunch.org`) | Sending `RRID:SCR_012345` without the `.json` suffix — the resolver without `.json` returns HTML, not JSON | Always construct `f"https://scicrunch.org/resolver/{rrid}.json"` |
| RRID Resolver | Not normalizing the RRID prefix before resolving — users may input `SCR_012345` without the `RRID:` prefix; calling `resolver/SCR_012345.json` returns a 404 | Always normalize: `rrid if rrid.startswith("RRID:") else f"RRID:{rrid}"` |
| Flask → SciCrunch | No timeout set on `requests.get/post()` — SciCrunch's Elasticsearch gateway can be slow (Africa-to-US latency); a hung connection blocks a Gunicorn worker indefinitely | Always pass `timeout=(connect_timeout, read_timeout)` — e.g., `timeout=(5, 20)` |
| Next.js → Flask | Missing `/api/v1/` prefix in the Next.js proxy route URL — all Flask blueprints use `url_prefix='/api/v1/rrid'`; the `integrations` prefix in the spec differs from the `v1` convention in DOCiD | Align the RRID blueprint URL prefix with the existing convention: `url_prefix='/api/v1/rrid'` |
| Alembic migration | Not adding `__init__.py` model import before running migration — SQLAlchemy discovers models only if they are imported; a new `DocidRrids` model not imported in `app/models.py` or `__init__.py` will not appear in `alembic revision --autogenerate` | Import the new model class in `backend/app/models.py` and verify `flask db migrate` detects the new table |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Resolving RRID on every page load instead of reading from `resolved_json` DB cache | Publication detail page is slow whenever it displays attached RRIDs; latency spikes to 2-5 seconds | Read `resolved_json` from DB; only call the resolver when `resolved_json IS NULL` or `last_resolved_at < (NOW() - interval '30 days')` | Immediately — even at 10 publications with RRIDs this creates 10 outbound HTTP calls per page load |
| No index on `docid_rrids(entity_type, entity_id)` | RRID lookup for a publication is a full table scan; slow as rows accumulate | Add composite index in Alembic migration: `Index('ix_docid_rrids_entity', 'entity_type', 'entity_id')` | Noticeable at ~1,000 RRID rows; critical at 10,000+ |
| Calling SciCrunch search on every keystroke in the search modal (no debounce) | Rapid typing floods Flask with outbound SciCrunch requests; API key may hit undocumented rate limits; Flask worker pool exhausted | Debounce search input by 400-500ms in the React component before firing the AJAX call | At ~3 concurrent users typing simultaneously |
| Storing full Elasticsearch `_source` blob in `resolved_json` JSONB | Large rows (~50-200 KB per RRID); slow JSON serialization for list endpoints that fetch multiple RRIDs | Store only the normalized subset: `{name, rrid, description, url, resource_type}` in a separate `metadata_json` column; keep `resolved_json` for debug only or omit it | Matters when fetching a publication with 5+ RRIDs attached; JSONB size impacts PostgreSQL page splits |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Setting `SCICRUNCH_API_KEY` as `NEXT_PUBLIC_SCICRUNCH_API_KEY` | API key exposed in browser JavaScript bundle; bad actors can exhaust the key's rate limit or use it for unauthorized requests | Key must only be set server-side in Flask `.env`; grep for `NEXT_PUBLIC_SCICRUNCH` before every deploy |
| Passing user-supplied `entity_type` directly into the DB query without validation | SQL injection via `entity_type` parameter in attach/detach endpoints; or logic bypass via `entity_type=user_accounts` | Validate `entity_type` against a strict allowlist: `ALLOWED_ENTITY_TYPES = {"publication", "organization"}` before any DB operation |
| Passing user-supplied `rrid` value directly to the resolver URL without sanitization | Path traversal or SSRF: `rrid=../../../etc/passwd` constructs `scicrunch.org/resolver/../../../etc/passwd.json`; also `rrid=http://internal-server/secret` | Validate RRID format with regex before constructing URL: `re.match(r'^RRID:[A-Za-z0-9_:]+$', rrid)` |
| Logging full SciCrunch API key in Flask request logs | Key appears in log files; access to logs means access to key | The existing `log_request_info` hook in `__init__.py` logs request body and URL; ensure `apikey` header is never logged — use a `_safe_headers()` helper that masks the key in logs |
| No authentication check on the RRID attach endpoint | Any unauthenticated caller can attach arbitrary RRIDs to any publication or organization | RRID attach/detach endpoints must require `@jwt_required()` — same as the publications and comments endpoints |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing raw RRID string (e.g., `RRID:SCR_012345`) without resolved label | Users do not know what resource the RRID refers to; RRID strings are opaque | Display resolved name alongside RRID (from `metadata_json.name`); fall back to the RRID string only if metadata is unavailable |
| No feedback when SciCrunch is slow or unavailable | Search modal appears broken; user retries and floods the queue | Show a loading spinner after 500ms; show a "SciCrunch is temporarily unavailable" message after the request times out (set a 15s frontend timeout before showing the error) |
| Search results show only the first page (`size=10`) with no way to load more | Users searching for common terms (e.g., "Africa") see 10 results and assume nothing else exists | Add a "Load more" button that increments the `size` parameter (up to 100); or show a "X total results found" count using `hits.total.value` from the Elasticsearch response |
| Allowing attachment of an RRID that is already attached to the same entity | Duplicate RRID entries appear on the entity detail page | Enforce the unique constraint at DB level `(entity_type, entity_id, rrid)` and return a 409 Conflict with a user-friendly message: "This RRID is already attached" |
| RRID search modal resets to empty when the user switches between Publications and Organizations tabs | Users must re-type their search term for each entity type | Preserve modal search state in component state; clear only on explicit modal close |

---

## "Looks Done But Isn't" Checklist

- [ ] **RRID attach endpoint:** Often missing auth — verify `@jwt_required()` is present on POST and DELETE endpoints
- [ ] **Resolver caching:** Often missing the "re-resolve if stale" logic — verify `last_resolved_at` is checked and a re-resolve is triggered when cache is >30 days old
- [ ] **Duplicate prevention:** Often missing the unique constraint — verify `(entity_type, entity_id, rrid)` unique constraint exists in the migration and is enforced at DB level, not just application level
- [ ] **Blueprint registration:** Often missing in `__init__.py` — verify the new `rrid_bp` is imported and registered with `app.register_blueprint(rrid_bp, url_prefix='/api/v1/rrid')`, and also added to `app/routes/__init__.py`
- [ ] **Orphan cleanup:** Often missing cascade — verify that deleting a publication also deletes its `docid_rrids` rows (run a test: create pub → attach RRID → delete pub → confirm `docid_rrids` row is gone)
- [ ] **entity_type validation:** Often missing allowlist — verify the attach endpoint rejects `entity_type=user_accounts` or any value not in `{"publication", "organization"}`
- [ ] **Resolver URL suffix:** Often missing `.json` — verify the resolver call constructs `scicrunch.org/resolver/RRID:SCR_012345.json`, not `scicrunch.org/resolver/RRID:SCR_012345`
- [ ] **Timeout handling:** Often missing graceful error — verify that a SciCrunch timeout returns a structured `{"error": "SciCrunch unavailable", "code": 503}` JSON response, not an HTML Flask 500 page

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Orphan RRID rows after parent entity deletion | LOW | Write a one-time cleanup migration: `DELETE FROM docid_rrids WHERE entity_type='publication' AND entity_id NOT IN (SELECT id FROM publications)` — then add cascade logic to prevent recurrence |
| API key exposed in Next.js bundle | HIGH | Revoke the key immediately via SciCrunch portal; request a new key from Africa PID Alliance; audit git history for key commits; redeploy with key only in Flask env |
| Wrong Elasticsearch field path causing empty search results | LOW | Update the query construction in `integrations_rrid.py`; no DB changes needed; test with known RRID |
| Duplicate RRID rows in `docid_rrids` (missing unique constraint) | MEDIUM | Add migration to remove duplicates, then add unique constraint: `ALTER TABLE docid_rrids ADD CONSTRAINT uq_entity_rrid UNIQUE (entity_type, entity_id, rrid)` |
| `CACHE_TYPE = 'simple'` causing cache miss storms across workers | LOW | Upgrade cache backend to `FileSystemCache` or Redis when deploying multi-worker Gunicorn; no code changes needed, only config change in `__init__.py` |
| SciCrunch resolver returns inconsistent schema (field path changes) | MEDIUM | Add `.get()` guards to all resolver field accesses; normalize to a stable internal schema on ingest rather than storing raw response |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Colon escaping in `rrid.curie` query | Phase 1: Backend blueprint | Unit test: query known RRID returns 1 hit; query with unescaped colon returns 0 or error |
| Wrong field path for type filtering | Phase 1: Backend blueprint | Integration test: filter by `type=software` returns only software resources |
| Resolver/search domain split | Phase 1: Backend blueprint | Code review: two separate URL constants; resolver test makes request to `scicrunch.org` not `api.scicrunch.io` |
| Polymorphic FK orphan rows | Phase 1: DB migration | Test: delete publication → verify `docid_rrids` rows removed; query publication list → verify no dangling rows |
| API key exposure via Next.js | Phase 1: Backend blueprint (before any frontend) | `grep -r "NEXT_PUBLIC_SCICRUNCH" frontend/` returns nothing; browser DevTools shows no direct calls to `api.scicrunch.io` |
| `entity_type` allowlist missing | Phase 1: Backend blueprint | Test: POST attach with `entity_type=user_accounts` returns 400 |
| Missing auth on attach endpoint | Phase 2: Frontend integration | Test: unauthenticated POST to attach returns 401 |
| No debounce on search input | Phase 2: Frontend integration | Manual test: rapid typing fires only one request per word, not per keystroke |
| Resolver not called with `.json` suffix | Phase 1: Backend blueprint | Unit test: resolver response is valid JSON, not HTML |
| Duplicate RRID constraint missing | Phase 1: DB migration | Test: attaching same RRID twice to same entity returns 409 |

---

## Sources

- SciCrunch API Handbook — Basic RIN Search Examples: https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/basic-rin-search-examples
- SciCrunch API Handbook — RIN JSON Data Model: https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/rin-elaticsearch-json-data-model
- SciCrunch API Handbook — RRID Resolver: https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/the-rrid-resolver
- SciCrunch GitHub API-Handbook — basic-rin-search-examples.md: https://github.com/SciCrunch/API-Handbook/blob/master/resources-information-network/basic-rin-search-examples.md
- RRID System documentation: https://www.rrids.org/rrid-system
- DOCiD codebase — `backend/app/__init__.py` (blueprint registration, cache config)
- DOCiD codebase — `backend/app/models.py` (PublicationOrganization, Publications cascade patterns)
- DOCiD codebase — `backend/app/routes/ror.py` (reference integration pattern)
- DOCiD codebase — `backend/app/routes/raid.py` (timeout handling, error patterns)
- DOCiD integration spec — `backend/temp/DOCID_Add_RRID_Integration.md`
- Flask-Caching documentation: https://flask-caching.readthedocs.io/
- SQLAlchemy 2.0 — Basic Relationship Patterns: https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html

---
*Pitfalls research for: RRID/SciCrunch integration into DOCiD (Flask + Next.js + PostgreSQL)*
*Researched: 2026-02-24*
