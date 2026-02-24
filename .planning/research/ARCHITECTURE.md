# Architecture Research

**Domain:** RRID/SciCrunch integration into existing DOCiD Flask + Next.js platform
**Researched:** 2026-02-24
**Confidence:** HIGH — based on direct inspection of existing codebase

---

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Browser / Next.js Frontend                       │
│                                                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────────┐  │
│  │ /docid/[id]      │  │ /assign-docid/   │  │ /user-profile/    │  │
│  │ page.jsx         │  │ page.jsx         │  │ page.jsx          │  │
│  │ (displays RRIDs) │  │ (attach RRIDs)   │  │ (org RRIDs)       │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬──────────┘  │
│           │ AJAX (axios)        │ AJAX                 │ AJAX        │
│  ┌────────▼─────────────────────▼──────────────────────▼──────────┐  │
│  │                  Next.js API Proxy Routes                        │  │
│  │  src/app/api/rrid/search/route.js                               │  │
│  │  src/app/api/rrid/resolve/route.js                              │  │
│  │  src/app/api/rrid/attach/route.js                               │  │
│  │  src/app/api/rrid/[entity_type]/[entity_id]/route.js            │  │
│  └──────────────────────────────┬──────────────────────────────────┘  │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │ HTTP (fetch, server-side)
┌─────────────────────────────────┼────────────────────────────────────┐
│                     Flask Backend (port 5001)                         │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               app/routes/rrid.py (Blueprint)                  │    │
│  │  GET  /api/v1/rrid/search?q=&type=&size=                     │    │
│  │  GET  /api/v1/rrid/resolve?rrid=RRID:SCR_012345              │    │
│  │  POST /api/v1/rrid/attach                                     │    │
│  │  GET  /api/v1/rrid/<entity_type>/<entity_id>                 │    │
│  │  DELETE /api/v1/rrid/<rrid_id>                               │    │
│  └───────────────────────┬─────────────────────────────────────┘    │
│                           │                                          │
│  ┌────────────────────────▼────────────────────────────────────┐    │
│  │              app/service_scicrunch.py                         │    │
│  │  SciCrunchService: search(), resolve(), normalize_result()   │    │
│  │  Injects SCICRUNCH_API_KEY header on every outbound call     │    │
│  └───────────────────────┬─────────────────────────────────────┘    │
│                           │                                          │
│  ┌────────────────────────▼────────────────────────────────────┐    │
│  │              app/models.py  (DocidRrid model)                 │    │
│  │  Table: docid_rrids                                           │    │
│  │  FK → publications.id  OR  publication_organizations.id      │    │
│  └────────────────────────┬────────────────────────────────────┘    │
│                           │                                          │
│  ┌────────────────────────▼────────────────────────────────────┐    │
│  │           PostgreSQL  (via SQLAlchemy 2.0)                    │    │
│  │  docid_rrids | publications | publication_organizations       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
                                  │ HTTPS (apikey header, server-side only)
┌─────────────────────────────────▼────────────────────────────────────┐
│                      SciCrunch External APIs                          │
│  POST https://api.scicrunch.io/elastic/v1/RIN_Tool_pr/_search        │
│  GET  https://scicrunch.org/resolver/<RRID>.json                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Next.js page components | Render RRID search modals, display attached RRIDs, fire AJAX | `page.jsx` — AJAX via `axios`, no full reloads |
| Next.js API proxy routes | Forward browser requests to Flask, keep Flask URL internal | `src/app/api/rrid/*/route.js` — thin pass-through |
| `app/routes/rrid.py` | Blueprint exposing `/api/v1/rrid/*` endpoints, request validation, response shaping | Flask Blueprint following ROR/ISNI pattern |
| `app/service_scicrunch.py` | Encapsulate all SciCrunch HTTP calls, inject API key, normalize payloads | Standalone service module following `service_crossref.py` pattern |
| `DocidRrid` SQLAlchemy model | Persist RRID-to-entity associations and cached resolver metadata | Added to `app/models.py` |
| Alembic migration | Create `docid_rrids` table in PostgreSQL | `migrations/versions/<hash>_add_docid_rrids_table.py` |

---

## Recommended Project Structure

```
backend/
├── app/
│   ├── routes/
│   │   └── rrid.py                   # NEW — Flask Blueprint /api/v1/rrid/*
│   ├── service_scicrunch.py          # NEW — SciCrunch API wrapper
│   ├── models.py                     # MODIFIED — add DocidRrid model
│   └── __init__.py                   # MODIFIED — register rrid_bp
├── migrations/
│   └── versions/
│       └── <hash>_add_docid_rrids_table.py  # NEW — Alembic migration
└── tests/
    └── test_rrid.py                  # NEW — request/parse + schema tests

frontend/
└── src/
    └── app/
        ├── api/
        │   └── rrid/                        # NEW directory
        │       ├── search/
        │       │   └── route.js             # NEW — proxy /api/v1/rrid/search
        │       ├── resolve/
        │       │   └── route.js             # NEW — proxy /api/v1/rrid/resolve
        │       ├── attach/
        │       │   └── route.js             # NEW — proxy /api/v1/rrid/attach
        │       └── [entity_type]/
        │           └── [entity_id]/
        │               └── route.js         # NEW — proxy GET/DELETE on entity
        ├── docid/
        │   └── [id]/
        │       └── page.jsx                 # MODIFIED — add RRID display section
        └── components/
            └── RridSearchModal.jsx          # NEW — reusable RRID search + attach modal
```

### Structure Rationale

- **`app/routes/rrid.py`:** Follows every existing integration pattern — one Blueprint per external service, URL prefix `/api/v1/rrid`.
- **`app/service_scicrunch.py`:** Separating HTTP calls into a service module is the established pattern (`service_crossref.py`, `service_codra.py`). The Blueprint stays thin; all SciCrunch knowledge lives in the service.
- **`DocidRrid` in `models.py`:** All models live in the single `app/models.py` file. This is a deliberate project convention. Do not create a separate models file.
- **`src/app/api/rrid/`:** Mirrors the Flask URL structure. Existing proxy routes in `src/app/api/ror/` and `src/app/api/comments/` show the same pattern — thin Next.js route handlers that forward to Flask and return `NextResponse.json`.
- **`RridSearchModal.jsx`:** Extracted as a reusable component because the modal is needed on both the publication detail page and potentially the organization profile page.

---

## Architectural Patterns

### Pattern 1: API Key Injection in Service Layer

**What:** The Flask service module reads `SCICRUNCH_API_KEY` from env and injects it into every outbound request. No route handler ever touches the key directly.

**When to use:** Any time an external service requires server-side credentials that must not be exposed client-side.

**Trade-offs:** Simple and clear. The API key is isolated. The only cost is an extra function call boundary.

**Example:**
```python
# app/service_scicrunch.py
import os
import requests

SCICRUNCH_SEARCH_URL = "https://api.scicrunch.io/elastic/v1/RIN_Tool_pr/_search"
RRID_RESOLVER_URL = "https://scicrunch.org/resolver/{rrid}.json"

def _get_headers():
    api_key = os.getenv("SCICRUNCH_API_KEY")
    if not api_key:
        raise RuntimeError("SCICRUNCH_API_KEY environment variable is not set")
    return {"apikey": api_key, "Content-Type": "application/json"}

def search_resources(query: str, resource_type: str, size: int = 10) -> dict:
    must_clauses = [
        {"term": {"recordValid": True}},
        {"match_phrase": {"item.types.name": resource_type}},
    ]
    if query:
        must_clauses.append({"query_string": {"query": f'"{query}"'}})

    payload = {"query": {"bool": {"must": must_clauses}}, "size": size}
    response = requests.post(
        SCICRUNCH_SEARCH_URL,
        headers=_get_headers(),
        json=payload,
        timeout=25
    )
    response.raise_for_status()
    return response.json()

def resolve_rrid(rrid: str) -> dict:
    normalized_rrid = rrid if rrid.startswith("RRID:") else f"RRID:{rrid}"
    response = requests.get(
        RRID_RESOLVER_URL.format(rrid=normalized_rrid),
        timeout=25
    )
    response.raise_for_status()
    return response.json()
```

### Pattern 2: Blueprint with URL Prefix Registration

**What:** Flask Blueprint registered in `app/__init__.py` with a URL prefix. All endpoints live under `/api/v1/rrid/`.

**When to use:** Every integration in this project follows this pattern. Do not deviate.

**Trade-offs:** Extremely predictable — any developer can find endpoints based on service name alone.

**Example:**
```python
# app/routes/rrid.py
from flask import Blueprint, jsonify, request
from app import db
from app.models import DocidRrid, Publications, PublicationOrganization
from app.service_scicrunch import search_resources, resolve_rrid as sc_resolve_rrid

rrid_bp = Blueprint("rrid", __name__, url_prefix="/api/v1/rrid")

@rrid_bp.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    resource_type = request.args.get('type', 'core facility').strip()
    size = min(int(request.args.get('size', 10)), 100)

    try:
        raw = search_resources(query, resource_type, size)
        hits = raw.get("hits", {}).get("hits", [])
        results = [_normalize_hit(h) for h in hits]
        return jsonify({"count": len(results), "results": results})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@rrid_bp.route('/resolve', methods=['GET'])
def resolve():
    rrid = request.args.get('rrid', '').strip()
    if not rrid:
        return jsonify({"error": "rrid parameter is required"}), 400

    # Check DB cache first
    cached = DocidRrid.query.filter_by(rrid=rrid).first()
    if cached and cached.resolved_json:
        return jsonify(cached.resolved_json)

    try:
        data = sc_resolve_rrid(rrid)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Pattern 3: Dedicated Association Table with Polymorphic Entity Reference

**What:** `docid_rrids` uses `entity_type` (string) + `entity_id` (integer) to reference either a publication or an organization row. No SQLAlchemy polymorphic relationship — kept simple with a string discriminator.

**When to use:** When the same identifier type (RRID) attaches to multiple entity kinds and you want strict RRID separation (per the user's stated preference for Option B).

**Trade-offs:** Slightly more logic in queries than a direct FK, but completely flexible and avoids schema changes when a new entity type is added. No multi-table inheritance complexity.

**Example:**
```python
# In app/models.py — add after PublicationProjects

from sqlalchemy.dialects.postgresql import JSONB

class DocidRrid(db.Model):
    """
    Dedicated association table for RRID (Research Resource Identifier) attachments.
    Supports publications and organizations as entity types for this milestone.
    """
    __tablename__ = 'docid_rrids'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    # entity_type values: 'publication', 'organization'
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    rrid = db.Column(db.String(100), nullable=False, index=True)
    # Normalized format: always stored with RRID: prefix (e.g., RRID:SCR_012345)
    resource_name = db.Column(db.String(500), nullable=True)
    # Human-readable name cached at attach time (avoids re-resolving for display)
    resolved_json = db.Column(db.Text, nullable=True)
    # Full resolver/search response cached as JSON text (TEXT over JSONB for portability)
    last_resolved_at = db.Column(db.DateTime, nullable=True)
    attached_by_user_id = db.Column(
        db.Integer, db.ForeignKey('user_accounts.user_id'), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Composite unique constraint: one RRID per entity
    __table_args__ = (
        db.UniqueConstraint('entity_type', 'entity_id', 'rrid', name='uq_rrid_per_entity'),
    )

    def serialize(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "rrid": self.rrid,
            "resource_name": self.resource_name,
            "resolved_json": self.resolved_json,
            "last_resolved_at": self.last_resolved_at.isoformat() if self.last_resolved_at else None,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<DocidRrid(id={self.id}, entity_type='{self.entity_type}', entity_id={self.entity_id}, rrid='{self.rrid}')>"
```

---

## Data Flow

### Primary Flow: Search → Select → Attach → Display

```
User clicks "Add RRID" on publication detail page
    ↓
RridSearchModal opens (React state: isOpen=true)
    ↓
User types query, selects resource type (e.g., "core facility")
    ↓
AJAX: axios.get('/api/rrid/search?q=microscopy&type=core facility')
    ↓
Next.js proxy: GET /api/rrid/search/route.js
    forwards to Flask GET /api/v1/rrid/search?q=...&type=...
    ↓
Flask rrid_bp.search()
    → service_scicrunch.search_resources(query, resource_type, size)
    → POST https://api.scicrunch.io/elastic/v1/RIN_Tool_pr/_search
        (apikey header injected server-side)
    → Returns ES hits
    ↓
Flask normalizes hits → returns {count, results[{scicrunch_id, name, rrid, url}]}
    ↓
Next.js proxy returns JSON to browser
    ↓
RridSearchModal renders result list
    ↓
User clicks "Attach" on a result
    ↓
AJAX: axios.post('/api/rrid/attach', {
    entity_type: 'publication',
    entity_id: 42,
    rrid: 'RRID:SCR_012345',
    resource_name: 'Fiji',
    resolved_json: {...}
})
    ↓
Next.js proxy: POST /api/rrid/attach/route.js → Flask POST /api/v1/rrid/attach
    ↓
Flask rrid_bp.attach()
    → validates entity_type and entity_id exist in DB
    → validates rrid format (must have RRID: prefix)
    → checks for duplicate (unique constraint)
    → saves DocidRrid row
    → returns {id, rrid, resource_name, created_at}
    ↓
RridSearchModal closes, page re-fetches attached RRIDs
    ↓
Publication detail page shows RRID badge/chip with link to scicrunch.org/resources/Any/...
```

### Secondary Flow: Resolve Known RRID (with DB Cache)

```
Flask GET /api/v1/rrid/resolve?rrid=RRID:SCR_012345
    ↓
Query DocidRrid.query.filter_by(rrid='RRID:SCR_012345').first()
    ↓
[Cache HIT] → return cached resolved_json immediately
[Cache MISS] → call service_scicrunch.resolve_rrid('RRID:SCR_012345')
    → GET https://scicrunch.org/resolver/RRID:SCR_012345.json
    → optionally update resolved_json on existing DocidRrid row if entity match
    → return resolver JSON to caller
```

### Fetch Attached RRIDs Flow (for display)

```
Publication detail page loads
    ↓
AJAX: axios.get('/api/rrid/publication/42')
    → Flask GET /api/v1/rrid/publication/42
    → DocidRrid.query.filter_by(entity_type='publication', entity_id=42).all()
    → returns [{id, rrid, resource_name, ...}]
    ↓
Page renders list of RRID chips with external links
```

---

## New vs Modified Components

### New Components (create from scratch)

| Component | Path | Why New |
|-----------|------|---------|
| RRID Blueprint | `backend/app/routes/rrid.py` | New integration, no existing file |
| SciCrunch service | `backend/app/service_scicrunch.py` | New external API, isolated per service convention |
| Alembic migration | `backend/migrations/versions/<hash>_add_docid_rrids_table.py` | New table required |
| Backend tests | `backend/tests/test_rrid.py` | New feature, new tests |
| Next.js proxy — search | `frontend/src/app/api/rrid/search/route.js` | New endpoint |
| Next.js proxy — resolve | `frontend/src/app/api/rrid/resolve/route.js` | New endpoint |
| Next.js proxy — attach | `frontend/src/app/api/rrid/attach/route.js` | New endpoint |
| Next.js proxy — entity list | `frontend/src/app/api/rrid/[entity_type]/[entity_id]/route.js` | New endpoint |
| RRID search modal | `frontend/src/app/components/RridSearchModal.jsx` | Reusable UI, shared between publication and org pages |

### Modified Components (change existing)

| Component | Path | What Changes |
|-----------|------|--------------|
| Flask app factory | `backend/app/__init__.py` | Import and register `rrid_bp` — 2-line addition matching existing pattern |
| SQLAlchemy models | `backend/app/models.py` | Add `DocidRrid` class after `PublicationProjects` |
| Publication detail page | `frontend/src/app/docid/[id]/page.jsx` | Add "Attached RRIDs" display section and "Add RRID" button that opens `RridSearchModal` |
| Environment config | `backend/.env` / `backend/.env.example` | Add `SCICRUNCH_API_KEY=` variable |

### No Changes Needed

- `publications.py` route — RRID attachment goes through the dedicated `/rrid` blueprint, not through the publications creation endpoint. Publications are already created; RRIDs are attached post-creation.
- `PublicationOrganization` model — the `docid_rrids` table references `publication_organizations.id` via `entity_id` when `entity_type='organization'`. No columns added to `publication_organizations`.
- Existing migrations — no alterations to existing tables.

---

## Integration Points

### docid_rrids Table Relations to Existing Entities

```
Publications (publications.id)
    ↑  entity_type='publication', entity_id=<publications.id>
docid_rrids
    ↓  entity_type='organization', entity_id=<publication_organizations.id>
PublicationOrganization (publication_organizations.id)
```

**Important:** There is no standalone Organization model in DOCiD. Organizations exist only as `publication_organizations` rows, each tied to a publication. When attaching an RRID to an "organization", the `entity_id` is the `publication_organizations.id` (the join-table row), not an independent org entity ID.

This means:
- An RRID attached to `entity_type='organization', entity_id=7` refers to `publication_organizations` row 7, which in turn has its own `publication_id` FK.
- The "organization scope" for RRIDs is scoped to a publication's organization affiliation, not a global organization registry.

**To display organization RRIDs on a publication page:** Query `DocidRrid.query.filter_by(entity_type='organization', entity_id__in=[org.id for org in publication.publication_organizations]).all()`

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| SciCrunch Search API | POST via `service_scicrunch.py` with `apikey` header | Elasticsearch gateway; `RIN_Tool_pr` index; returns hits array |
| SciCrunch Resolver | GET `https://scicrunch.org/resolver/<RRID>.json` | No API key required for resolver endpoint; different base domain from search |
| Flask-Caching (Redis/simple) | Already initialized in `app/__init__.py` as `cache` | Search results can use `@cache.cached(timeout=300)` on the route; resolver results use DB-level caching in `resolved_json` column |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `rrid.py` blueprint ↔ `service_scicrunch.py` | Direct Python function calls | Blueprint calls service functions; service knows nothing about Flask |
| `service_scicrunch.py` ↔ SciCrunch | `requests` library with injected API key header | All credentials stay in service module |
| `rrid.py` ↔ `DocidRrid` model | SQLAlchemy ORM queries | Blueprint validates entity existence before saving |
| Next.js proxy ↔ Flask | HTTP fetch with `NEXT_PUBLIC_API_BASE_URL` env variable | Pattern identical to existing `ror/search-organization/route.js` |
| `RridSearchModal.jsx` ↔ Next.js proxy | Axios AJAX calls | No full page reloads; follows project's AJAX-first requirement |

---

## Suggested Build Order

Build order follows the dependency chain: database before code before UI.

### Step 1: Backend Foundation (no frontend dependencies)

1. **`DocidRrid` model in `app/models.py`** — defines the data shape everything else depends on
2. **Alembic migration** — creates `docid_rrids` table in PostgreSQL
3. **`app/service_scicrunch.py`** — isolates SciCrunch API; can be tested independently
4. **`app/routes/rrid.py`** — implements endpoints using service + model
5. **Register blueprint in `app/__init__.py`** — two lines; enables the routes
6. **Add `SCICRUNCH_API_KEY` to env files** — required before any endpoint works

### Step 2: Backend Tests (validates foundation before frontend)

7. **`backend/tests/test_rrid.py`** — tests for:
   - `service_scicrunch.py` request/parse (mock requests)
   - `rrid.py` endpoint schema validation (Flask test client)
   - `DocidRrid` model constraint (unique RRID per entity)

### Step 3: Frontend Proxy (depends on working Flask endpoints)

8. **Next.js API proxy routes** — all four route files under `src/app/api/rrid/`
   - `search/route.js` — GET proxy
   - `resolve/route.js` — GET proxy
   - `attach/route.js` — POST proxy
   - `[entity_type]/[entity_id]/route.js` — GET (list) + DELETE proxy

### Step 4: Frontend UI (depends on working proxies)

9. **`RridSearchModal.jsx`** — search input, resource type dropdown, results list, attach action
10. **Modify `docid/[id]/page.jsx`** — add "Attached RRIDs" section and wire up modal

---

## Architectural Patterns to Avoid

### Anti-Pattern 1: Calling SciCrunch from the Browser

**What people do:** Expose `SCICRUNCH_API_KEY` in `NEXT_PUBLIC_` env variables and call SciCrunch directly from the browser via `useEffect`.

**Why it's wrong:** API key leaks in browser DevTools Network tab and page source. SciCrunch API key is a partnership credential provided by Africa PID Alliance — its exposure could revoke access for the entire platform.

**Do this instead:** All SciCrunch calls go through the Flask backend. The Next.js proxy routes are purely pass-through. The API key lives only in the server's environment (`SCICRUNCH_API_KEY` without `NEXT_PUBLIC_` prefix).

### Anti-Pattern 2: Adding RRID Columns Directly to Publications or PublicationOrganization

**What people do:** Add an `rrid` column or `rrid_json` column directly to the `publications` or `publication_organizations` table — the same approach used for `orcid_id` on `user_accounts`.

**Why it's wrong:** Publications can have multiple RRIDs (e.g., software tool + cell line + antibody). A single column cannot hold a list. Extending to a JSON column creates an unindexed, unqueriable blob. The user explicitly chose the dedicated `docid_rrids` table (Option B).

**Do this instead:** Use `DocidRrid` with the polymorphic `entity_type` + `entity_id` pattern. Query by entity when displaying.

### Anti-Pattern 3: Creating a Separate models_rrid.py File

**What people do:** Create a new `app/models_rrid.py` to keep the models file shorter.

**Why it's wrong:** The entire DOCiD project uses a single `app/models.py`. All SQLAlchemy models are imported from there throughout the codebase. Splitting models creates circular import risk and breaks the convention that every other developer on the project relies on.

**Do this instead:** Append `DocidRrid` class to `app/models.py` after the `PublicationProjects` class.

### Anti-Pattern 4: Full Page Reload on RRID Attach

**What people do:** Submit a form with a standard POST and redirect/reload the page to show the newly attached RRID.

**Why it's wrong:** The project-wide convention (enforced in `~/.claude/CLAUDE.md`) is AJAX for all page interactions including buttons and filtering. A full reload breaks user flow on the rich detail page.

**Do this instead:** After a successful `axios.post('/api/rrid/attach', ...)`, fire an AJAX GET to `/api/rrid/publication/<id>` and update the displayed RRID list in state without any page reload.

---

## Sources

- **Direct codebase inspection** (HIGH confidence): `backend/app/routes/ror.py`, `backend/app/models.py`, `backend/app/__init__.py`, `backend/app/routes/comments.py`, `backend/app/routes/publications.py`, `frontend/src/app/api/ror/search-organization/route.js`, `frontend/src/app/api/publications/[id]/comments/route.js`, `frontend/src/app/docid/[id]/page.jsx`
- **Integration specification** (HIGH confidence): `backend/temp/DOCID_Add_RRID_Integration.md`
- **Project context** (HIGH confidence): `.planning/PROJECT.md`
- **Project development patterns** (HIGH confidence): `backend/CLAUDE.md`, `frontend/CLAUDE.md`
- **SciCrunch API base** (MEDIUM confidence from spec + PROJECT.md): `https://api.scicrunch.io`, resolver at `https://scicrunch.org/resolver/<RRID>.json`

---

*Architecture research for: RRID/SciCrunch integration into DOCiD Flask + Next.js platform*
*Researched: 2026-02-24*
