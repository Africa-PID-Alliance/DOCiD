# Phase 4: Flask Blueprint — Attach, List, Detach - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Three endpoints complete the RRID lifecycle — attaching an RRID to a publication or organization, listing attached RRIDs for any entity, and removing a specific RRID — with data integrity enforced at every step. All endpoints live in the existing `rrid_bp` blueprint under `/api/v1/rrid`.

</domain>

<decisions>
## Implementation Decisions

### Attach Request Shape & Resolution Behavior
- Server resolves the RRID on attach — POST body sends only `rrid`, `entity_type`, `entity_id`
- Server calls `resolve_rrid()` internally to fetch metadata before creating the DB row
- If SciCrunch is down during attach, fail the request with HTTP 502 — don't create rows without resolved metadata
- Attach response returns the full serialized DocidRrid row (all 12 fields) so the frontend can display immediately without a follow-up GET
- Validation: `entity_type` against `DocidRrid.ALLOWED_ENTITY_TYPES`, `entity_id` must be numeric, RRID format via `validate_rrid()`

### Duplicate & Conflict Handling
- Duplicate detection via DB-level IntegrityError catch on the UniqueConstraint — atomic, race-condition-free
- Duplicate returns HTTP 409 Conflict with error message only: `"RRID:SCR_012345 is already attached to this publication"`
- Same RRID allowed on multiple different entities (UniqueConstraint is per entity_type + entity_id + rrid tuple)
- No pre-check query — let the INSERT attempt hit the constraint, catch the IntegrityError

### List Endpoint Filtering & Response
- `GET /entity?entity_type=...&entity_id=...` returns flat JSON array of full serialized DocidRrid rows
- Empty result returns HTTP 200 with `[]` — consistent with Phase 3 search pattern
- No entity existence validation — just query docid_rrids for matching rows; missing entity returns empty array
- Both `entity_type` and `entity_id` are required parameters; missing either returns HTTP 400

### Cascade Deletion Strategy
- Application-level cascade in the existing publication delete route — delete all docid_rrids rows matching entity_type='publication' AND entity_id=<id> in the same transaction
- Same cascade applies to publication_organizations deletions — removing an org from a publication also removes its entity_type='organization' RRID rows
- `DELETE /rrid/<rrid_id>` allows any authenticated user to delete any RRID attachment — no ownership checks in this phase
- Delete response returns `{message: "RRID detached successfully"}` with HTTP 200
- Deleting a non-existent rrid_id returns HTTP 404

### Claude's Discretion
- Exact function decomposition within the blueprint module
- How to integrate cascade logic into existing publication/org delete routes
- Transaction handling approach (db.session scope)
- Whether to add the cascade routes to rrid.py or modify existing route files

</decisions>

<specifics>
## Specific Ideas

- All three new endpoints (`POST /attach`, `GET /entity`, `DELETE /<rrid_id>`) add to the existing `rrid_bp` blueprint created in Phase 3
- All endpoints require `@jwt_required()` — consistent with Phase 3 pattern
- Entity type validation reuses `DocidRrid.ALLOWED_ENTITY_TYPES` from Phase 3
- The `(data, error)` tuple pattern from service_scicrunch.py should be used for the resolve call during attach

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-flask-blueprint-attach-list-detach*
*Context gathered: 2026-02-25*
