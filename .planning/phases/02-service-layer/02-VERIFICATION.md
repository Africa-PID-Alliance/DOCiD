---
phase: 02-service-layer
verified: 2026-02-24T18:30:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 2: Service Layer Verification Report

**Phase Goal:** A self-contained Python module isolates all SciCrunch HTTP calls, RRID validation, and resolver cache logic behind a clean API — with the SciCrunch API key never leaving the server
**Verified:** 2026-02-24T18:30:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `SCICRUNCH_API_KEY` loaded from environment into Flask `app.config` and never exposed with `NEXT_PUBLIC_` prefix | VERIFIED | `config.py:23` uses `os.getenv('SCICRUNCH_API_KEY')`. Zero matches for `NEXT_PUBLIC_SCICRUNCH` across all frontend files and env files. |
| 2 | `service_scicrunch.py` defines `SCICRUNCH_SEARCH_BASE` (`api.scicrunch.io`) and `SCICRUNCH_RESOLVER_BASE` (`scicrunch.org`) as separate constants | VERIFIED | Lines 27-28 define both constants with correct domains. |
| 3 | `validate_rrid` accepts `RRID:SCR_012345`, `RRID:AB_123456789`, `RRID:CVCL_0001` and auto-prepends `RRID:` when absent; rejects non-matching strings | VERIFIED | Automated tests pass: all 3 prefix families accepted, auto-prepend works, `INVALID_123` and `RRID:XYZ_999` rejected. |
| 4 | `validate_rrid` normalizes case-insensitive input to uppercase (`rrid:scr_012345` becomes `RRID:SCR_012345`) | VERIFIED | Automated test `validate_rrid('rrid:cvcl_0001')[0] == 'RRID:CVCL_0001'` passes. `re.IGNORECASE` flag on line 39, uppercase normalization on line 126. |
| 5 | `search_rrid_resources` sends requests to `api.scicrunch.io` with `apikey` header, using `term` queries for exact RRID lookups | VERIFIED | Line 215: `"apikey": api_key` in request headers only on search call. Lines 188-191: `{"term": {"item.curie": rrid_identifier}}` used for RRID path. No `apikey` header in resolver call (line 421-424). |
| 6 | `search_rrid_resources` returns `(data, None)` tuple on success with normalized fields: `scicrunch_id`, `name`, `description`, `url`, `types`, `rrid` | VERIFIED | Lines 269-280: normalized result dict has all 6 required fields. Return on line 288: `(normalized_results, None)`. |
| 7 | `resolve_rrid` fetches metadata from `scicrunch.org` resolver and returns normalized subset | VERIFIED | Lines 417-438: GET to `{SCICRUNCH_RESOLVER_BASE}/resolver/{normalized_rrid}.json`. No `apikey` in resolver call. |
| 8 | Resolved metadata is cached in `DocidRrid.resolved_json`; subsequent calls reuse cached data if less than 30 days old | VERIFIED | Lines 383-414: cache lookup with `DocidRrid.query.filter_by()`. TTL check: `(datetime.utcnow() - cached_row.last_resolved_at) < timedelta(days=CACHE_MAX_AGE_DAYS)`. Cache update at lines 455-461. |
| 9 | `resolved_json` stores only the normalized 7-field subset; on SciCrunch failure stale cached data is returned if available | VERIFIED | `_normalize_resolver_response()` returns exactly 7 keys: `name`, `rrid`, `description`, `url`, `resource_type`, `properCitation`, `mentions`. Stale fallback at lines 486-502 with `"stale": True` flag. |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/config.py` | `SCICRUNCH_API_KEY` config entry | VERIFIED | Line 23: `SCICRUNCH_API_KEY = os.getenv('SCICRUNCH_API_KEY')`. No `NEXT_PUBLIC_` variant anywhere. |
| `backend/app/service_scicrunch.py` | RRID validation and search/resolve functions, 100+ lines | VERIFIED | 512 lines. Exports `validate_rrid`, `search_rrid_resources`, `resolve_rrid`. All substantive implementations. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `service_scicrunch.py` | `config.py` | `current_app.config.get('SCICRUNCH_API_KEY')` | WIRED | Line 89: `api_key = current_app.config.get("SCICRUNCH_API_KEY")`. Config sourced correctly from Flask app context. |
| `service_scicrunch.py` | `api.scicrunch.io` | `requests.Session` POST with `apikey` header | WIRED | Lines 213-225: POST to `{SCICRUNCH_SEARCH_BASE}/{SCICRUNCH_ES_INDEX}/_search` with `"apikey"` header. Retry adapter mounted on session. |
| `service_scicrunch.py` | `scicrunch.org` | `requests.Session` GET to resolver URL | WIRED | Lines 421-425: GET to `{SCICRUNCH_RESOLVER_BASE}/resolver/{normalized_rrid}.json`. No `apikey` header (correct per project decision). |
| `service_scicrunch.py` | `models.py` | `DocidRrid.query` for cache read/write | WIRED | Line 16: `from app.models import DocidRrid`. Line 386: `DocidRrid.query.filter_by(...)`. Lines 455-461: cache update via `db.session.commit()`. |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| INFRA-05 | 02-01-PLAN.md | `SCICRUNCH_API_KEY` server-side only, no `NEXT_PUBLIC_*` exposure | SATISFIED | `config.py:23` uses `os.getenv`. Zero `NEXT_PUBLIC_SCICRUNCH` matches in frontend files or env files. |
| INFRA-06 | 02-01-PLAN.md | `service_scicrunch.py` with separate URL constants for search and resolver | SATISFIED | Lines 27-28 define `SCICRUNCH_SEARCH_BASE` (api.scicrunch.io) and `SCICRUNCH_RESOLVER_BASE` (scicrunch.org). |
| SEARCH-07 | 02-01-PLAN.md | RRID format validation with regex covering `SCR_`, `AB_`, `CVCL_` prefixes; auto-prepends `RRID:` if absent | SATISFIED | `RRID_PATTERN` at line 37-40. `validate_rrid()` normalizes and auto-prepends. All automated tests pass. |
| SEARCH-08 | 02-01-PLAN.md | Elasticsearch queries use `term` queries for exact RRID lookups (not `query_string`) | SATISFIED | Lines 188: `{"term": {"item.curie": rrid_identifier}}` for RRID path. `query_string` only used for free-text keyword path (line 203). |
| CACHE-01 | 02-02-PLAN.md | Resolver metadata cached in `resolved_json` JSONB column after first resolve | SATISFIED | Lines 455-461: `cached_row.resolved_json = resolved_data`, `db.session.commit()` after successful resolve. |
| CACHE-02 | 02-02-PLAN.md | Cached resolver data reused if `last_resolved_at` less than 30 days old | SATISFIED | Lines 399-414: TTL check `(datetime.utcnow() - cached_row.last_resolved_at) < timedelta(days=CACHE_MAX_AGE_DAYS)` where `CACHE_MAX_AGE_DAYS = 30`. |
| CACHE-03 | 02-02-PLAN.md | `resolved_json` stores normalized subset only (7 fields), not raw blob | SATISFIED | `_normalize_resolver_response()` returns exactly: `name`, `rrid`, `description`, `url`, `resource_type`, `properCitation`, `mentions`. Automated test confirms 7 keys. |

**All 7 phase requirements SATISFIED.**

**Orphaned requirements check:** REQUIREMENTS.md traceability table maps exactly INFRA-05, INFRA-06, SEARCH-07, SEARCH-08, CACHE-01, CACHE-02, CACHE-03 to Phase 2. No orphaned requirements.

---

### Anti-Patterns Found

No anti-patterns detected.

| File | Pattern | Severity | Result |
|------|---------|----------|--------|
| `service_scicrunch.py` | TODO/FIXME/placeholder | Checked | None found |
| `service_scicrunch.py` | Empty return values (`return null`, `return {}`) | Checked | None found |
| `service_scicrunch.py` | Console-log-only stubs | Checked | None found |

---

### Human Verification Required

#### 1. Live SciCrunch API Integration

**Test:** Set `SCICRUNCH_API_KEY` env var to a valid key. Start Flask. Call `search_rrid_resources("flow cytometry", "core_facility")`. Inspect the returned data.
**Expected:** HTTP 200 from SciCrunch; normalized results list with `scicrunch_id`, `name`, `description`, `url`, `types`, `rrid` fields.
**Why human:** Requires a valid SciCrunch API key and live network. Automated checks verify the code structure but cannot confirm the actual Elasticsearch response shape matches the field extraction at `hit["_source"]["item"]`.

#### 2. Live Resolver Integration

**Test:** Call `resolve_rrid("RRID:SCR_012345")` within a Flask app context with real HTTP.
**Expected:** SciCrunch resolver at `https://scicrunch.org/resolver/RRID:SCR_012345.json` returns JSON; `_normalize_resolver_response` correctly maps the actual response fields. Note that the resolver JSON shape may differ from the expected `name`, `curie`, `description`, `url`, `resource_type`, `properCitation`, `mentions` field paths — plan explicitly flagged this as needing adjustment.
**Why human:** SciCrunch resolver JSON schema is empirical. The plan acknowledged "adjust field paths based on actual SciCrunch ES response structure if needed." Cannot verify field path accuracy without a live call.

---

### Gaps Summary

No gaps. All automated checks pass with zero failures.

The one area of uncertainty (live API field path accuracy) is flagged for human verification per the plan's own caveat — this is expected, not a gap in implementation.

---

## Commit Verification

| Plan | Commit | Exists in Git |
|------|--------|---------------|
| 02-01 | `ebfb1e5` | YES — `feat(02-01): add SciCrunch RRID validation and search service` |
| 02-02 | `d674760` | YES — `feat(02-02): add resolve_rrid with 30-day DB cache and stale fallback` |

---

_Verified: 2026-02-24T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
