# Phase 3: Flask Blueprint — Search & Resolve - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Two working Flask endpoints let authenticated code search SciCrunch by keyword/type and resolve any known RRID to canonical metadata — all routed through the `/api/v1/rrid` blueprint. Blueprint registered in `app/__init__.py`, entity_type validated against allowlist on all endpoints that accept it.

</domain>

<decisions>
## Implementation Decisions

### Endpoint Response Shapes
- Search endpoint returns a flat JSON array `[{scicrunch_id, name, ...}, ...]` — no wrapper object, no metadata
- Empty search results return HTTP 200 with `[]` — frontend checks `.length === 0`
- Resolve endpoint returns the 7 canonical fields plus `last_resolved_at` timestamp and `stale` boolean flag
- Hard cap at 20 search results, no pagination parameter — SciCrunch relevance ranking ensures best matches come first
- Search accepts only `q` (keyword) and `type` (resource type) query parameters — no entity context on search

### Error Handling & HTTP Status Codes
- SciCrunch timeout/5xx → HTTP 502 Bad Gateway with `{error: "Search service unavailable"}` (or similar generic message)
- Generic error messages only — never expose SciCrunch internals, status codes, or response details to the frontend
- Validation errors return a single `{error: "..."}` string — matches existing ROR blueprint pattern
- RRID not found in SciCrunch → HTTP 404 with `{error: "RRID not found: RRID:SCR_999999"}`
- Invalid RRID format → HTTP 400 with `{error: "Invalid RRID format"}`
- Invalid `type` parameter → HTTP 400 with `{error: "Invalid resource type: ..."}`
- Missing required `q` parameter on search → HTTP 400 with `{error: "Missing required parameter: q"}`

### Authentication & Authorization
- Both search and resolve endpoints require strict `@jwt_required()` — returns 401 if JWT missing/invalid
- Any authenticated user can access — no role-based restrictions on read-only endpoints
- Ownership checks deferred to Phase 4 (attach/detach) — Phase 3 only validates format, not permissions
- Format validation only for entity_type: check against allowlist, don't verify user owns the entity

### Entity Type Validation Behavior
- `entity_type` and `entity_id` are optional on resolve — resolve works without entity context (returns metadata only)
- If entity_type is provided without entity_id (or vice versa), return HTTP 400: `"Both entity_type and entity_id are required when either is provided"`
- Entity type allowlist (`{'publication', 'organization'}`) imported from the DocidRrid model — single source of truth shared with DB CHECK constraint
- Search endpoint does NOT accept entity_type/entity_id — entity context is irrelevant for keyword lookups

### Claude's Discretion
- Exact function signatures and route handler structure
- How to wire the service module's `(data, error)` tuples into HTTP responses
- Blueprint variable naming and import organization
- Whether to add a shared entity validation helper or inline the checks

</decisions>

<specifics>
## Specific Ideas

- Follow the existing `routes/ror.py` blueprint pattern for module structure (Blueprint creation, route decorators, jsonify responses)
- Blueprint registration follows the same pattern as ROR: import in `app/__init__.py`, register with `url_prefix='/api/v1/rrid'`
- The service layer already returns `(data, error)` tuples — blueprint routes just need to map `error` → appropriate HTTP status and `data` → jsonify response
- `ALLOWED_ENTITY_TYPES` should be a class attribute or constant on `DocidRrid` model, imported by the blueprint

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-flask-blueprint-search-resolve*
*Context gathered: 2026-02-24*
