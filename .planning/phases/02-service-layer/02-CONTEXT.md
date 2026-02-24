# Phase 2: Service Layer - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Create `service_scicrunch.py` — a self-contained Python module that isolates all SciCrunch HTTP calls, RRID validation, and resolver cache logic behind a clean API. The SciCrunch API key never leaves the server. No Flask endpoints, no frontend — purely service functions that the blueprint (Phase 3) will call.

</domain>

<decisions>
## Implementation Decisions

### RRID Validation Rules
- Accept 3 prefix families only: `SCR_`, `AB_`, `CVCL_`
- Numeric part: prefix + any digits (`SCR_\d+`, `AB_\d+`, `CVCL_\d+`)
- Auto-prepend `RRID:` silently when prefix is absent (e.g. `SCR_012345` → `RRID:SCR_012345`)
- Case-insensitive input, normalize to uppercase (e.g. `rrid:scr_012345` → `RRID:SCR_012345`)
- Reject strings that don't match the known prefix+digits patterns

### Search Function Design
- Support 4 resource type filters: Core Facility, Software, Antibody, Cell Line
- Default type when omitted: Core Facility (DOCiD's primary use case)
- Return limit: 20 results per query
- Normalized search result fields: `scicrunch_id`, `name`, `description`, `url`, `types`, `rrid`
- Use `term` queries for exact RRID lookups (not `query_string`) to avoid colon-escaping failures

### Resolver Cache Behavior
- Auto-refresh if `last_resolved_at` > 30 days on the next resolve call (transparent to caller)
- On SciCrunch API failure: return stale cache if available, error only if no cached data exists
- Update only the requested row's `resolved_json` — not all rows with the same RRID
- Return resolved data + `last_resolved_at` timestamp to callers (useful for UI "last updated" display)
- Normalized cache fields: `name`, `rrid`, `description`, `url`, `resource_type`, `properCitation`, `mentions`

### Service Module API Shape
- Error handling: return `(data, error)` tuples — `(result, None)` on success, `(None, error_dict)` on failure
- HTTP session: module-level `requests.Session` with connection pooling and basic retry via `HTTPAdapter`
- API key: read from `Flask app.config['SCICRUNCH_API_KEY']` sourced from environment (follow existing ORCID/ROR pattern)
- Request timeout: 30 seconds per SciCrunch API call (accommodates their variable latency up to 25s)
- Two separate URL constants: `SCICRUNCH_SEARCH_BASE` (api.scicrunch.io) and `SCICRUNCH_RESOLVER_BASE` (scicrunch.org)
- API key sent as `apikey` header only to the search domain, never to the resolver domain

### Claude's Discretion
- Exact function signatures and parameter names
- Internal helper function decomposition
- HTTPAdapter retry configuration (max retries, backoff factor)
- How to extract/map SciCrunch ES response fields to normalized shape
- Session initialization approach (lazy vs eager)

</decisions>

<specifics>
## Specific Ideas

- Follow the existing `service_ror.py` or ROR integration pattern for module structure
- The SciCrunch ES index to query is `RIN_Tool_pr`
- API key header format: `apikey: <key>` (not `Authorization: Bearer`)
- Resolver URL pattern: `https://scicrunch.org/resolver/{RRID}.json`
- Search URL pattern: `https://api.scicrunch.io/elastic/v1/RIN_Tool_pr/_search`

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-service-layer*
*Context gathered: 2026-02-24*
