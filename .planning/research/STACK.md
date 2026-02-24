# Stack Research

**Domain:** RRID/SciCrunch integration for scholarly PID platform (Flask + Next.js)
**Researched:** 2026-02-24
**Confidence:** HIGH

---

## What This Is

This is a **milestone-scoped** stack document. It covers only NEW additions required for the
RRID/SciCrunch integration. Everything in the "Already in Stack" section is confirmed present
in `requirements.txt` and must NOT be re-added.

---

## Already in Stack — Do NOT Add Again

| Package | Version in requirements.txt | Notes |
|---------|---------------------------|-------|
| `requests` | 2.28.0 | Used for all HTTP calls — covers SciCrunch API calls |
| `flask-caching` | 2.3.0 | Installed; currently configured as `CACHE_TYPE = 'simple'` |
| `redis` | unpinned | Listed in requirements; backing store available |
| `jsonschema` | 4.22.0 | Available for response validation in tests |
| `SQLAlchemy` | 2.0.30 | `JSONB` column support via `sqlalchemy.dialects.postgresql` |
| `psycopg2-binary` | 2.9.9 | PostgreSQL driver — JSONB works out of the box |
| `Flask-Migrate` | 4.0.5 | Alembic wrapper — handles the new `docid_rrids` migration |
| `pytest` | 2.6.0 | Installed (very old; see note below) |
| `python-dotenv` | 1.0.1 | `SCICRUNCH_API_KEY` loaded via `os.getenv` with dotenv |

---

## New Stack Additions Needed

### Core — Backend

| Technology | Recommended Version | Purpose | Why |
|------------|--------------------|---------|----|
| `responses` | `>=0.26.0` | Mock `requests` HTTP calls in unit tests | No network needed in CI; intercepts `requests.get/post` calls to SciCrunch at test time. The alternative (VCR.py cassettes) is heavier and harder to maintain. `responses` is the standard mock library for `requests`-based code — confirmed at 0.26.0 as of Feb 2026. |

That is the only new Python dependency. All other SciCrunch integration needs are satisfied by
the existing stack.

### Core — Frontend

No new npm packages are required. The RRID search modal follows the same AJAX + MUI Dialog
pattern used for ROR and ORCID modals already in the codebase.

---

## Recommended Stack Patterns for This Milestone

### 1. SciCrunch API Client — Use `requests` Directly (No Wrapper Library)

**Why not a dedicated SciCrunch Python SDK?**
No official or community SciCrunch Python SDK exists on PyPI as of 2026-02-24. SciBot
(scicrunch/scibot on GitHub) is the only Python implementation in the SciCrunch org, and it is
a Hypothes.is annotation tool — not a reusable API client. Building a thin wrapper inside the
blueprint using plain `requests.post` (for search) and `requests.get` (for resolve) is the
correct approach and matches the existing ROR/ORCID integration pattern.

**Why not the `elasticsearch-py` client?**
SciCrunch exposes its Elasticsearch gateway via standard HTTP with `apikey` header auth.
There is no need to connect to ES directly. The gateway accepts plain JSON POST bodies and
returns standard ES `hits.hits._source` format. Using `requests.post` with a JSON payload is
simpler, avoids a 15 MB dependency, and keeps the integration identical to how every other
external service is called in DOCiD. Confidence: HIGH (verified against official SciCrunch API
Handbook at docs.scicrunch.io).

### 2. RRID Validation — Use `re` from Python stdlib

No external RRID validation package exists. RRID format is well-specified:

```
RRID:SCR_########     (software / tools, 6-9 digits)
RRID:AB_#########     (antibodies, 6-9 digits)
RRID:CVCL_####        (cell lines, 4 alphanumeric)
```

Regex using the stdlib `re` module covers all validation needs:

```python
import re

RRID_PATTERN = re.compile(
    r'^RRID:(SCR_\d{6,9}|AB_\d{6,9}|CVCL_[A-Z0-9]{4,6})$'
)

def is_valid_rrid(rrid_string: str) -> bool:
    return bool(RRID_PATTERN.match(rrid_string.strip()))
```

Confidence: MEDIUM (format verified against official rrids.org and resolver examples; exact
digit ranges confirmed against SciCrunch resolver sample data in docs).

### 3. DB Caching for Resolver Results — PostgreSQL JSONB Column

**Decision confirmed:** Use the `docid_rrids.resolved_json` JSONB column as the cache store
for resolver metadata. This matches the project decision in PROJECT.md (Option B, DB-level
caching over Redis for resolver results).

**Import pattern for the model:**

```python
from sqlalchemy.dialects.postgresql import JSONB

class DocidRrid(db.Model):
    __tablename__ = "docid_rrids"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    rrid = db.Column(db.String(100), nullable=False)
    resolved_json = db.Column(JSONB, nullable=True)
    last_resolved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

`JSONB` is available via `sqlalchemy.dialects.postgresql` — confirmed supported with
SQLAlchemy 2.0 + psycopg2-binary as already installed.

### 4. Flask-Caching for Search Results — Upgrade `CACHE_TYPE` to Redis

**Current state:** `__init__.py` sets `CACHE_TYPE = 'simple'`. SimpleCache is an in-process
dict — not thread-safe, not shared across gunicorn workers, resets on each restart.

**For SciCrunch search caching** (5-30 minute TTL on `q=` query results):

```python
# config.py addition
SCICRUNCH_API_KEY = os.getenv("SCICRUNCH_API_KEY")
CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")       # dev: simple, prod: redis
CACHE_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_DEFAULT_TIMEOUT = 300
```

`redis` package is already in requirements.txt (unpinned). No new package needed.

Use `@cache.cached(timeout=300, key_prefix=...)` on the search endpoint. Do NOT cache
the resolver endpoint in Flask-Caching — resolver results go to the DB column instead
(one-time fetch per RRID, stored forever with `last_resolved_at`).

### 5. Testing — `pytest` + `responses` + `pytest-flask`

**Problem with existing pytest 2.6.0:** This is extremely old (2014). It will fail with
modern fixtures and assertion introspection. However, the project currently has NO active test
suite using it (no `tests/` directory, no test files in `backend/`). The test files in
`scripts/` are ad-hoc integration scripts, not pytest test suites.

**Recommendation for RRID tests:** Write a standalone `backend/tests/` directory with:
- `pytest` upgrade or pin at `>=7.4,<9` (constraint: avoid pytest 6.x API)
- `pytest-flask 1.3.0` for Flask test client fixtures (confirmed Flask 3.0 compatible)
- `responses 0.26.0` for mocking SciCrunch HTTP calls

**Do not add `pytest-flask` as a blocker.** The RRID blueprint can be tested with plain
`Flask.test_client()` if `pytest-flask` adds friction. Plain `requests_mock` or `responses`
alone is sufficient for the core parse/schema validation tests in scope.

---

## Recommended Stack for New Code

### Blueprint File: `backend/app/routes/rrid.py`

```python
import os
import re
import requests
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app import db, cache
from app.models import DocidRrid

SCICRUNCH_SEARCH_URL = "https://api.scicrunch.io/elastic/v1/{index}/_search"
SCICRUNCH_RESOLVER_URL = "https://scicrunch.org/resolver/{rrid}.json"
RRID_PATTERN = re.compile(r'^RRID:(SCR_\d{6,9}|AB_\d{6,9}|CVCL_[A-Z0-9]{4,6})$')

rrid_bp = Blueprint("rrid", __name__, url_prefix="/api/v1/rrid")
```

### Environment Variable Addition

```bash
# .env (server-side only, never expose to frontend)
SCICRUNCH_API_KEY=your_key_here
CACHE_TYPE=redis                     # for production; leave 'simple' for dev
```

### Config Addition (`backend/config.py`)

```python
SCICRUNCH_API_KEY = os.getenv("SCICRUNCH_API_KEY")
```

### Migration

Generated with `Flask-Migrate` (already installed):

```bash
python run.py db migrate -m "add docid_rrids table"
python run.py db upgrade
```

---

## Alternatives Considered

| Recommended | Alternative | Why Not |
|-------------|-------------|---------|
| `requests` (existing) for SciCrunch API | `elasticsearch-py` client | ES client connects to ES natively; SciCrunch exposes ES via HTTP gateway that works identically with plain `requests.post`. Adds 15 MB dependency for no gain. |
| `re` stdlib for RRID validation | Dedicated RRID package (PyPI) | No such package exists. Regex is 3 lines and covers all known RRID prefixes. |
| DB JSONB column for resolver cache | Redis for resolver cache | PROJECT.md already decided DB-level caching to avoid infrastructure complexity. DB cache survives restarts; suitable for long-lived (weekly) resolver metadata. |
| `responses` 0.26.0 for HTTP mocking | `unittest.mock.patch` on requests | `responses` provides cleaner DSL for URL-specific mocks; avoids low-level patch targets that break when request internals change. |
| `pytest-flask` 1.3.0 | `flask.testing.FlaskClient` directly | pytest-flask provides `live_server` and `client` fixtures reducing boilerplate. Flask 3.0 compat confirmed in 1.3.0 release notes. |

---

## What NOT to Add

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `elasticsearch-py` or `elasticsearch` PyPI package | SciCrunch is accessed via HTTP REST, not native ES transport. This package adds TLS/transport complexity for no benefit. | `requests.post(url, json=payload, headers={"apikey": key})` |
| Any "scicrunch" named PyPI package | No official package exists; any such package would be unofficial, unmaintained, or malicious. | Hand-rolled blueprint using `requests` |
| `marshmallow` or `pydantic` for schema validation | Project uses no schema validation library currently; introducing one for a single integration creates inconsistency. | `jsonschema 4.22.0` already in requirements — use for response shape validation in tests |
| New Redis instance or `celery` | Bulk sync is explicitly OUT OF SCOPE for this milestone. Redis is already referenced in config. | Existing `redis` package + flask-caching upgrade if needed |
| `flask-restx` or `flask-restplus` | Project uses plain Flask Blueprints + Flasgger. Switching REST framework mid-project breaks consistency. | Follow existing Blueprint pattern in `routes/ror.py` |

---

## Version Compatibility

| Package | Version | Compatibility Notes |
|---------|---------|-------------------|
| `requests` 2.28.0 | `responses` 0.26.0 | `responses` 0.26.0 requires `requests >= 2.30.0`. **This is a conflict.** See mitigation below. |
| `SQLAlchemy` 2.0.30 | `JSONB` dialect type | Full support confirmed. Import from `sqlalchemy.dialects.postgresql`. |
| `pytest` 2.6.0 | `pytest-flask` 1.3.0 | pytest-flask 1.3.0 requires pytest >= 5.2. Existing pytest 2.6.0 is incompatible. |
| `Flask` 3.0.3 | `pytest-flask` 1.3.0 | Confirmed compatible — Flask 3.0 fix in 1.3.0 release notes. |
| `flask-caching` 2.3.0 | `redis` package | Compatible with unpinned `redis`. For production, pin `redis>=4.0`. |

### Critical Conflict: `responses` vs `requests` Version

`responses 0.26.0` requires `requests >= 2.30.0` but the project pins `requests==2.28.0`.

**Options:**
1. **Upgrade requests to `2.32.3`** (latest stable) — LOW RISK. The requests API has been
   stable since 2.28. Upgrading is safe; the existing 13 integrations use only standard
   `requests.get/post/raise_for_status` patterns.
2. **Use `responses==0.23.3`** — the last version compatible with requests 2.28.x. This is
   the safer no-change-to-requirements option.
3. **Use `unittest.mock.patch("requests.Session.send", ...)` instead** — zero new dependency,
   more brittle but works with any requests version.

**Recommendation: Upgrade `requests` to `2.32.3` and `responses` to `0.26.0`** — the
improvement in security patches (urllib3, certificate handling) since 2.28.0 makes this
worthwhile beyond just the test mocking need.

---

## Installation

```bash
# Upgrade existing pinned packages (safe, backwards compatible)
pip install "requests==2.32.3"

# New test dependency only — do not add to production requirements
pip install "responses==0.26.0" "pytest-flask==1.3.0" "pytest>=7.4,<9"

# If upgrading pytest in requirements.txt (project had no active test suite):
# Change: pytest==2.6.0
# To:     pytest>=7.4,<9
```

**requirements.txt changes:**
```
# Change
requests==2.28.0   →  requests==2.32.3

# Add (test deps — can put in requirements-test.txt or requirements.txt)
responses==0.26.0
pytest-flask==1.3.0
pytest>=7.4,<9
```

---

## Sources

- SciCrunch API Handbook (docs.scicrunch.io) — Search endpoint format, RIN_Tool_pr index, resolver URL, authentication; HIGH confidence
- SciCrunch resolver docs — No API key required for resolver GET; HIGH confidence
- PyPI: responses 0.26.0 — Release date Feb 19, 2026; requires requests >= 2.30.0; HIGH confidence
- PyPI: pytest-flask 1.3.0 — Flask 3.0 compatibility confirmed; HIGH confidence
- SQLAlchemy 2.0 docs — JSONB via `sqlalchemy.dialects.postgresql.JSONB`; HIGH confidence
- DOCiD `backend/requirements.txt` — Verified all existing package versions directly; HIGH confidence
- DOCiD `backend/app/__init__.py` — Verified `CACHE_TYPE = 'simple'`, Cache initialized; HIGH confidence
- DOCiD `backend/app/routes/ror.py` — Reference pattern for blueprint structure; HIGH confidence
- WebSearch: No dedicated RRID Python package on PyPI; MEDIUM confidence (confirmed via GitHub SciCrunch org, PyPI search)

---

*Stack research for: RRID/SciCrunch integration milestone on DOCiD platform*
*Researched: 2026-02-24*
