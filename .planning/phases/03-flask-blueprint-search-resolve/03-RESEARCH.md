# Phase 3: Flask Blueprint — Search & Resolve - Research

**Researched:** 2026-02-24
**Domain:** Flask Blueprint routing, Flask-JWT-Extended, SciCrunch service integration
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Endpoint Response Shapes**
- Search endpoint returns a flat JSON array `[{scicrunch_id, name, ...}, ...]` — no wrapper object, no metadata
- Empty search results return HTTP 200 with `[]` — frontend checks `.length === 0`
- Resolve endpoint returns the 7 canonical fields plus `last_resolved_at` timestamp and `stale` boolean flag
- Hard cap at 20 search results, no pagination parameter — SciCrunch relevance ranking ensures best matches come first
- Search accepts only `q` (keyword) and `type` (resource type) query parameters — no entity context on search

**Error Handling & HTTP Status Codes**
- SciCrunch timeout/5xx → HTTP 502 Bad Gateway with `{error: "Search service unavailable"}` (or similar generic message)
- Generic error messages only — never expose SciCrunch internals, status codes, or response details to the frontend
- Validation errors return a single `{error: "..."}` string — matches existing ROR blueprint pattern
- RRID not found in SciCrunch → HTTP 404 with `{error: "RRID not found: RRID:SCR_999999"}`
- Invalid RRID format → HTTP 400 with `{error: "Invalid RRID format"}`
- Invalid `type` parameter → HTTP 400 with `{error: "Invalid resource type: ..."}`
- Missing required `q` parameter on search → HTTP 400 with `{error: "Missing required parameter: q"}`

**Authentication & Authorization**
- Both search and resolve endpoints require strict `@jwt_required()` — returns 401 if JWT missing/invalid
- Any authenticated user can access — no role-based restrictions on read-only endpoints
- Ownership checks deferred to Phase 4 (attach/detach) — Phase 3 only validates format, not permissions
- Format validation only for entity_type: check against allowlist, don't verify user owns the entity

**Entity Type Validation Behavior**
- `entity_type` and `entity_id` are optional on resolve — resolve works without entity context (returns metadata only)
- If entity_type is provided without entity_id (or vice versa), return HTTP 400: `"Both entity_type and entity_id are required when either is provided"`
- Entity type allowlist (`{'publication', 'organization'}`) imported from the DocidRrid model — single source of truth shared with DB CHECK constraint
- Search endpoint does NOT accept entity_type/entity_id — entity context is irrelevant for keyword lookups

### Claude's Discretion
- Exact function signatures and route handler structure
- How to wire the service module's `(data, error)` tuples into HTTP responses
- Blueprint variable naming and import organization
- Whether to add a shared entity validation helper or inline the checks

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INFRA-07 | Flask blueprint `rrid.py` registered in `app/__init__.py` under `/api/v1/rrid` prefix | Blueprint pattern confirmed from existing codebase and Context7 docs |
| INFRA-08 | `entity_type` parameter validated against allowlist `{"publication", "organization"}` on all endpoints that accept it | Allowlist import pattern from `DocidRrid` model; inline guard or helper both viable |
| SEARCH-01 | User can search RRID resources by keyword through backend proxy endpoint `GET /api/v1/rrid/search` | `service_scicrunch.search_rrid_resources()` already implemented in Phase 2 |
| SEARCH-02 | User can filter RRID search results by resource type via `type` query parameter | `RESOURCE_TYPE_MAP` already in service; blueprint reads `request.args.get('type')` |
| SEARCH-03 | Search type defaults to "core facility" when no type parameter is provided | `DEFAULT_RESOURCE_TYPE = "core_facility"` already in service layer |
| SEARCH-04 | Search results return normalized JSON: `scicrunch_id`, `name`, `description`, `url`, `types`, `rrid` | Service already returns normalized list; blueprint just `jsonify()`s it |
| SEARCH-05 | User can resolve a known RRID via `GET /api/v1/rrid/resolve` | `service_scicrunch.resolve_rrid()` already implemented in Phase 2 |
| SEARCH-06 | Resolver endpoint returns `properCitation`, `mentions`, `name`, `description`, `url`, `resource_type` | `_normalize_resolver_response()` already extracts all 7 fields; blueprint flattens them |
</phase_requirements>

---

## Summary

Phase 3 creates a thin Flask blueprint (`routes/rrid.py`) that exposes two `GET` endpoints — `/search` and `/resolve` — and wires them to the fully-implemented Phase 2 service layer (`service_scicrunch.py`). The blueprint itself has no business logic: it reads query params, calls the service, maps `(data, error)` tuples to HTTP responses, and applies `@jwt_required()` to both routes.

The project already contains the exact pattern to follow. The `routes/figshare.py` and `routes/ror.py` blueprints demonstrate Blueprint creation, URL prefix registration, and `@jwt_required()` decorator placement. The `app/__init__.py` registration pattern is uniform: import the Blueprint object, then call `app.register_blueprint(rrid_bp, url_prefix='/api/v1/rrid')`.

The only non-trivial decision is how to add `ALLOWED_ENTITY_TYPES` to the `DocidRrid` model (it does not yet exist as a class attribute) and how to flatten the resolve response. The service's `resolve_rrid()` returns a nested shape `{"resolved": {...7 fields...}, "last_resolved_at": "...", "stale": bool}` — the blueprint endpoint needs to flatten this into the single-level response shape specified in CONTEXT.md.

**Primary recommendation:** Create `routes/rrid.py` following the `figshare.py` pattern (lean blueprint, `@jwt_required()`, service delegation, `jsonify` returns), add `ALLOWED_ENTITY_TYPES = frozenset({"publication", "organization"})` as a class attribute on `DocidRrid`, then register in `app/__init__.py`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.0.3 (pinned) | Blueprint routing, `request.args`, `jsonify` | Project-wide web framework |
| Flask-JWT-Extended | 4.6.0 (pinned) | `@jwt_required()` decorator for route protection | Project auth standard, used across figshare/publications/auth routes |
| flask-sqlalchemy | 3.1.1 (pinned) | `DocidRrid` model import for allowlist constant | ORM in use for all DB models |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| service_scicrunch (internal) | Phase 2 | All SciCrunch calls — search and resolve | Already complete; blueprint delegates all SciCrunch logic here |
| logging (stdlib) | — | Module-level logger for blueprint errors | Consistent with figshare.py and service_scicrunch.py patterns |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `@jwt_required()` decorator | `verify_jwt_in_request()` function | Decorator is idiomatic and matches project; function form only needed for conditional auth |
| Inline `entity_type` check | Shared validation helper | Helper adds abstraction; CONTEXT.md leaves this to Claude's discretion — inline is simpler for two endpoints |
| `frozenset` for `ALLOWED_ENTITY_TYPES` | Plain `set` | Frozenset signals immutability and prevents accidental mutation; either works |

**Installation:** No new dependencies — all required libraries are already in `requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

```
backend/app/
├── routes/
│   └── rrid.py          # New blueprint file (Phase 3 output)
├── service_scicrunch.py  # Phase 2 service — already complete
├── models.py             # DocidRrid model — needs ALLOWED_ENTITY_TYPES added
└── __init__.py           # Blueprint registration — needs rrid_bp import + register
```

### Pattern 1: Blueprint Creation (Figshare Pattern)

**What:** Create a Blueprint object at module level with url_prefix, configure module-level logger, import service functions.
**When to use:** All new route modules in this project.
**Example (adapted from figshare.py):**

```python
# app/routes/rrid.py
import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models import DocidRrid
from app.service_scicrunch import search_rrid_resources, resolve_rrid

logger = logging.getLogger(__name__)

rrid_bp = Blueprint('rrid', __name__, url_prefix='/api/v1/rrid')
```

### Pattern 2: JWT-Protected GET Route with Query Params

**What:** Decorate route handler with `@rrid_bp.route(...)` then `@jwt_required()`. Read params via `request.args.get()`. Delegate to service. Map tuple result to HTTP response.
**When to use:** Both `/search` and `/resolve` handlers.
**Example:**

```python
@rrid_bp.route('/search', methods=['GET'])
@jwt_required()
def search_resources():
    keyword_query = request.args.get('q')
    if not keyword_query:
        return jsonify({'error': 'Missing required parameter: q'}), 400

    resource_type = request.args.get('type')  # None → service defaults to core_facility

    search_results, search_error = search_rrid_resources(keyword_query, resource_type)

    if search_error:
        # Distinguish validation errors (400) from upstream failures (502)
        if search_error.get('error', '').startswith('Invalid resource type'):
            return jsonify({'error': f"Invalid resource type: {resource_type}"}), 400
        return jsonify({'error': 'Search service unavailable'}), 502

    return jsonify(search_results), 200  # Empty list → 200 []
```

### Pattern 3: Resolve Response Flattening

**What:** The service returns `{"resolved": {...7 fields...}, "last_resolved_at": "...", "stale": bool, "cached": bool}`. The endpoint must flatten this to expose the 7 fields directly alongside `last_resolved_at` and `stale`.
**When to use:** `/resolve` handler only.
**Example:**

```python
@rrid_bp.route('/resolve', methods=['GET'])
@jwt_required()
def resolve_rrid_endpoint():
    rrid_param = request.args.get('rrid')
    if not rrid_param:
        return jsonify({'error': 'Missing required parameter: rrid'}), 400

    entity_type = request.args.get('entity_type')
    entity_id_raw = request.args.get('entity_id')

    # Validate partial entity context
    if bool(entity_type) != bool(entity_id_raw):
        return jsonify({'error': 'Both entity_type and entity_id are required when either is provided'}), 400

    # Validate entity_type against allowlist if provided
    if entity_type and entity_type not in DocidRrid.ALLOWED_ENTITY_TYPES:
        return jsonify({'error': f"Invalid entity_type: {entity_type}"}), 400

    entity_id = int(entity_id_raw) if entity_id_raw else None

    resolved_result, resolve_error = resolve_rrid(rrid_param, entity_type, entity_id)

    if resolve_error:
        if resolve_error.get('error') == 'Invalid RRID format':
            return jsonify({'error': 'Invalid RRID format'}), 400
        if 'not found' in resolve_error.get('detail', '').lower():
            return jsonify({'error': f"RRID not found: {rrid_param}"}), 404
        return jsonify({'error': 'Search service unavailable'}), 502

    # Flatten nested service response into single-level JSON
    canonical_fields = resolved_result['resolved']
    flat_response = {
        **canonical_fields,
        'last_resolved_at': resolved_result.get('last_resolved_at'),
        'stale': resolved_result.get('stale', False),
    }
    return jsonify(flat_response), 200
```

### Pattern 4: Blueprint Registration in app/__init__.py

**What:** Import the Blueprint object, call `app.register_blueprint()` with explicit `url_prefix`.
**When to use:** Every new blueprint — mirrors the 20+ existing registrations.
**Example (from existing __init__.py pattern):**

```python
# In create_app(), alongside existing blueprint imports:
from app.routes.rrid import rrid_bp

# In register_blueprint block:
app.register_blueprint(rrid_bp, url_prefix='/api/v1/rrid')
```

Note: The `rrid_bp` Blueprint object is created with `url_prefix` in `rrid.py`, but passing it again in `register_blueprint()` is the established project pattern — it overrides/reinforces the default. All existing blueprints do this.

### Pattern 5: ALLOWED_ENTITY_TYPES on DocidRrid Model

**What:** Add a class-level constant to `DocidRrid` so blueprint and any future code share one source of truth.
**When to use:** Required by CONTEXT.md and INFRA-08.
**Example:**

```python
class DocidRrid(db.Model):
    ALLOWED_ENTITY_TYPES = frozenset({'publication', 'organization'})
    # ... rest of model unchanged
```

### Anti-Patterns to Avoid

- **Importing service_scicrunch inside route handlers:** Module-level import is cleaner and matches figshare.py. Only use deferred import if circular dependency arises (unlikely here).
- **Passing raw service error dicts to the frontend:** The contract is `{error: "generic message"}` only — never `return jsonify(search_error), 500` which would expose SciCrunch internals.
- **Relying on Blueprint url_prefix alone:** The project always passes `url_prefix` in both `Blueprint(...)` and `register_blueprint(...)`. Follow the convention to avoid confusion.
- **Returning HTTP 204 for empty search:** The decision is explicit: empty results → 200 with `[]`. The ROR blueprint returns 204 for no-results; the RRID blueprint must not copy that behavior.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JWT auth | Custom token validation middleware | `@jwt_required()` from Flask-JWT-Extended 4.6.0 | Handles header parsing, expiry, signature validation, error responses |
| HTTP retries to SciCrunch | Custom retry loop | `requests.Session` + `Retry` in service layer | Already implemented in `service_scicrunch.py` |
| RRID format validation | Blueprint-level regex | `validate_rrid()` from `service_scicrunch.py` | Already implemented in Phase 2; service is the authority |
| Resource type mapping | Blueprint-level dict | `RESOURCE_TYPE_MAP` / `DEFAULT_RESOURCE_TYPE` from `service_scicrunch.py` | Already implemented; service owns this logic |
| Search normalization | Blueprint-level field extraction | `search_rrid_resources()` return value | Service already normalizes to `{scicrunch_id, name, description, url, types, rrid}` |
| Resolver caching | Blueprint-level cache | `resolve_rrid()` + DB `resolved_json` column | Phase 2 service handles cache read/write; blueprint is cache-unaware |

**Key insight:** The service layer (`service_scicrunch.py`) absorbed all SciCrunch-facing complexity in Phase 2. Phase 3 blueprint is purely a translation layer between HTTP and the service API.

---

## Common Pitfalls

### Pitfall 1: Expose SciCrunch Error Details to Frontend

**What goes wrong:** Route handler passes `search_error` or `resolve_error` dict directly to `jsonify()`, leaking SciCrunch status codes, URLs, or raw response text to API consumers.
**Why it happens:** `(data, error)` tuple makes it tempting to `return jsonify(error), 500`.
**How to avoid:** Always map error types to generic frontend messages. Check `error.get('error')` or `error.get('detail')` to classify, then return a clean `{error: "..."}` response.
**Warning signs:** Response body contains `status_code`, `detail`, or SciCrunch URLs.

### Pitfall 2: Missing `entity_id` Type Conversion

**What goes wrong:** `entity_id` arrives from `request.args.get('entity_id')` as a string. Passing a string to `resolve_rrid()` which queries `DocidRrid` with integer `entity_id` causes a type mismatch in the SQLAlchemy filter.
**Why it happens:** `request.args` always returns strings.
**How to avoid:** Convert with `int(entity_id_raw)` — but wrap in try/except to return 400 if non-numeric.
**Warning signs:** SQLAlchemy emits a `DataError` or `ProgrammingError` about integer/varchar mismatch.

### Pitfall 3: Blueprint url_prefix Duplication Confusion

**What goes wrong:** Developer sets `url_prefix='/api/v1/rrid'` in `Blueprint(...)` but omits it in `register_blueprint()`, or vice versa, causing 404s.
**Why it happens:** Flask allows prefix in either location; the project convention passes it in both.
**How to avoid:** Follow the exact pattern of the 20+ existing blueprint registrations in `__init__.py` — both in the Blueprint constructor and in `register_blueprint()`.
**Warning signs:** Routes respond with 404 when tested directly.

### Pitfall 4: Resolve Response Shape Mismatch

**What goes wrong:** Blueprint returns the raw service output `{"resolved": {...}, "cached": bool}` instead of the flattened shape with the 7 fields at top level.
**Why it happens:** Service return shape is nested for internal clarity; frontend contract is flat.
**How to avoid:** Always unpack `resolved_result['resolved']` and merge `last_resolved_at`/`stale` into the top-level response dict.
**Warning signs:** Frontend receives `{resolved: {...}}` instead of `{properCitation: "...", name: "...", ...}`.

### Pitfall 5: `entity_type=user_account` Returns 200 Instead of 400

**What goes wrong:** Blueprint passes `entity_type` straight to `resolve_rrid()` without allowlist check. Service doesn't validate entity_type — it only uses it for DB cache lookup.
**Why it happens:** Service layer never sees `user_account` row in DB, so query returns `None`, and execution falls through to SciCrunch fetch successfully.
**How to avoid:** Validate `entity_type` against `DocidRrid.ALLOWED_ENTITY_TYPES` in the blueprint **before** calling the service.
**Warning signs:** Success criterion #4 fails: `entity_type=user_account` returns 200 instead of 400.

---

## Code Examples

Verified patterns from project codebase and official sources:

### Blueprint Creation (from figshare.py + Context7)

```python
# Source: /Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/routes/figshare.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging

logger = logging.getLogger(__name__)
rrid_bp = Blueprint('rrid', __name__, url_prefix='/api/v1/rrid')
```

### jwt_required() on GET Route (from figshare.py line 411)

```python
# Source: /Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/routes/figshare.py
@figshare_bp.route('/my-articles', methods=['GET'])
@jwt_required()
def get_my_articles():
    ...
```

### request.args.get() Query Parameter Access (from Context7/Flask docs)

```python
# Source: https://github.com/pallets/flask/blob/main/docs/quickstart.rst
searchword = request.args.get('key', '')
```

### Blueprint Registration (from app/__init__.py pattern)

```python
# Source: /Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/__init__.py
from app.routes.rrid import rrid_bp
app.register_blueprint(rrid_bp, url_prefix='/api/v1/rrid')
```

### ALLOWED_ENTITY_TYPES Class Attribute (add to DocidRrid)

```python
# Source: /Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/models.py (to be added)
class DocidRrid(db.Model):
    ALLOWED_ENTITY_TYPES = frozenset({'publication', 'organization'})
    __tablename__ = 'docid_rrids'
    # ... existing columns unchanged
```

### Error Response Pattern (from auth.py / ROR blueprint convention)

```python
# Source: /Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/routes/auth.py (line 1688+)
return jsonify({'error': 'Missing required parameter: q'}), 400
return jsonify({'error': 'Search service unavailable'}), 502
return jsonify({'error': f"RRID not found: {rrid_value}"}), 404
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@jwt_required` (no parens) | `@jwt_required()` (with parens, v4+) | Flask-JWT-Extended v4.0 | Must use parens — project uses v4.6.0 |
| `@jwt_optional` | `@jwt_required(optional=True)` | Flask-JWT-Extended v4.0 | Not needed here, but good to know |
| Separate search/resolver URL constants in one var | Two separate constants `SCICRUNCH_SEARCH_BASE` + `SCICRUNCH_RESOLVER_BASE` | Phase 2 decision | Blueprint never constructs SciCrunch URLs directly |

**No deprecated patterns identified for this phase.** Flask 3.0 Blueprint API is stable. Flask-JWT-Extended 4.6.0 is the pinned version.

---

## Open Questions

1. **How does `resolve_rrid()` signal "RRID not found" vs "resolver error"?**
   - What we know: The service returns `(None, {"error": "SciCrunch resolver failed", "detail": "..."})` when the resolver can't be reached AND when no RRID exists. HTTP 200 from SciCrunch resolver could mean either "found" or "not found" depending on the response body shape.
   - What's unclear: Whether a valid RRID that doesn't exist in SciCrunch returns a specific status code or a recognizable response body that the service translates into a distinguishable error.
   - Recommendation: Review `resolve_rrid()` implementation in `service_scicrunch.py` during implementation. If the resolver returns 404 for unknown RRIDs, the service would log `HTTP 404` and fall through to the stale-cache path (returning error if no cache). The blueprint should treat any `None, error` as a 502 unless the error detail contains a pattern like "404" or "not found" — then return HTTP 404.

2. **Should `entity_id` type-conversion failure return 400 or 422?**
   - What we know: The project uses 400 for all validation errors (confirmed from `auth.py` patterns).
   - What's unclear: Non-numeric `entity_id` strings are not explicitly addressed in CONTEXT.md.
   - Recommendation: Use HTTP 400 with `{error: "Invalid entity_id: must be an integer"}` — consistent with project convention.

---

## Sources

### Primary (HIGH confidence)

- `/pallets/flask` (Context7) — Blueprint creation, `request.args`, `register_blueprint`, url_prefix patterns
- `/vimalloc/flask-jwt-extended` (Context7) — `@jwt_required()` decorator, v4 API shape
- `/Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/__init__.py` — Live codebase: exact blueprint registration pattern used by all 20+ existing blueprints
- `/Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/routes/figshare.py` — Live codebase: best existing example of `@jwt_required()` on GET routes
- `/Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/service_scicrunch.py` — Live codebase: Phase 2 service API surface (function signatures, return shapes)
- `/Users/ekariz/Projects/AMBAND/DOCiD/project/backend/app/models.py` — Live codebase: `DocidRrid` model confirming no `ALLOWED_ENTITY_TYPES` yet exists

### Secondary (MEDIUM confidence)

- `routes/ror.py` — Pattern reference for `{error: "..."}` response shape and `jsonify` usage (ROR blueprint does not use JWT)
- `routes/auth.py` — Pattern reference for `{error: "..."}` format on validation failures

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries pinned in requirements.txt, verified against live codebase
- Architecture: HIGH — existing blueprint registration pattern is uniform and directly observable
- Pitfalls: HIGH — derived from reading actual service layer code and CONTEXT.md decisions, not speculation

**Research date:** 2026-02-24
**Valid until:** 2026-03-26 (30 days — Flask Blueprint API is stable)
