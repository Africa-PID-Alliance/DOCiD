---
phase: 03-flask-blueprint-search-resolve
plan: 01
subsystem: backend-api
tags: [flask, blueprint, rrid, scicrunch, jwt, search, resolve]
dependency_graph:
  requires:
    - 02-01-SUMMARY.md (search_rrid_resources service function)
    - 02-02-SUMMARY.md (resolve_rrid service function with DB cache)
  provides:
    - GET /api/v1/rrid/search endpoint
    - GET /api/v1/rrid/resolve endpoint
    - DocidRrid.ALLOWED_ENTITY_TYPES class constant
  affects:
    - backend/app/__init__.py (blueprint registration)
tech_stack:
  added: []
  patterns:
    - Flask Blueprint with url_prefix in both constructor and register_blueprint
    - jwt_required() decorator on all RRID endpoints
    - (data, error) tuple pattern from service layer mapped to HTTP status codes
    - Flattened response from nested service dict using dict spread operator
key_files:
  created:
    - backend/app/routes/rrid.py
  modified:
    - backend/app/models.py
    - backend/app/__init__.py
decisions:
  - DocidRrid.ALLOWED_ENTITY_TYPES as single source of truth for entity type validation (matches DB CHECK constraint)
  - Generic error messages for all SciCrunch failures — never expose internals
  - resolve endpoint returns flat response (canonical_metadata spread + last_resolved_at + stale)
  - Partial entity context (one without the other) returns 400 before any service call
metrics:
  duration: 2min
  completed: 2026-02-25
  tasks_completed: 2
  files_changed: 3
---

# Phase 3 Plan 1: RRID Flask Blueprint — Search & Resolve Summary

**One-liner:** RRID Flask blueprint with JWT-protected search and resolve endpoints delegating to SciCrunch service layer, with entity type allowlist on DocidRrid model.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Add ALLOWED_ENTITY_TYPES to DocidRrid and create RRID blueprint with search endpoint | 648e895 | backend/app/models.py, backend/app/routes/rrid.py |
| 2 | Add resolve endpoint and register blueprint in app factory | f1072ff | backend/app/routes/rrid.py, backend/app/__init__.py |

## What Was Built

### `backend/app/routes/rrid.py` (new file, 168 lines)

Flask blueprint `rrid_bp` with two JWT-protected GET endpoints:

**`GET /api/v1/rrid/search`**
- Requires `q` parameter — returns 400 if missing/empty
- Optional `type` filter passed to `search_rrid_resources(keyword_query, resource_type_filter)`
- Invalid resource type → 400; SciCrunch failure → 502; success → 200 JSON array
- Empty results → 200 `[]` per project decision

**`GET /api/v1/rrid/resolve`**
- Requires `rrid` parameter — returns 400 if missing
- Optional `entity_type`/`entity_id` for DB cache context — partial pair → 400
- `entity_type` validated against `DocidRrid.ALLOWED_ENTITY_TYPES` — invalid → 400
- Non-numeric `entity_id` → 400
- Calls `resolve_rrid(rrid_param, entity_type, entity_id)`
- Error mapping: Invalid RRID format → 400; not found/could not resolve → 404; other → 502
- Success: flattens nested `{"resolved": {...7 fields...}, "last_resolved_at": ..., "stale": ...}` into a single-level response

### `backend/app/models.py` (modified)

Added class-level constant to `DocidRrid`:
```python
ALLOWED_ENTITY_TYPES = frozenset({'publication', 'organization'})
```
Placed as first line in class body before `__tablename__`. Single source of truth matching DB-level CHECK constraint.

### `backend/app/__init__.py` (modified)

Added RRID blueprint import and registration:
```python
from app.routes.rrid import rrid_bp
app.register_blueprint(rrid_bp, url_prefix='/api/v1/rrid')
```

## Verification Results

All plan-level checks passed:
- `/api/v1/rrid/search` and `/api/v1/rrid/resolve` appear in Flask URL map
- `DocidRrid.ALLOWED_ENTITY_TYPES` is `frozenset({'publication', 'organization'})`
- `rrid_bp.name == 'rrid'`, `rrid_bp.url_prefix == '/api/v1/rrid'`
- `__init__.py` contains both the import and `register_blueprint(rrid_bp` call

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

Files verified:
- `backend/app/routes/rrid.py` — FOUND
- `backend/app/models.py` — FOUND (contains ALLOWED_ENTITY_TYPES)
- `backend/app/__init__.py` — FOUND (contains rrid_bp registration)

Commits verified:
- 648e895 — FOUND
- f1072ff — FOUND
