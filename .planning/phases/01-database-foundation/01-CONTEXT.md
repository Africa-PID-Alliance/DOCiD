# Phase 1: Database Foundation - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the `docid_rrids` PostgreSQL table and `DocidRrid` SQLAlchemy model that all subsequent RRID integration phases depend on. Includes Alembic migration, unique constraint, composite index, and model with query helpers. No API endpoints, no frontend — purely database infrastructure.

</domain>

<decisions>
## Implementation Decisions

### Column Types & Sizes
- `id`: Integer, primary key, autoincrement
- `entity_type`: varchar(50), NOT NULL — stores 'publication' or 'organization'
- `entity_id`: Integer, NOT NULL — matches existing PK types (publications.id, publication_organizations.id)
- `rrid`: varchar(50), NOT NULL — stores RRID curie format e.g. `RRID:SCR_012345`
- `rrid_name`: varchar(500), nullable — facility/resource name from SciCrunch
- `rrid_description`: Text, nullable — resource description
- `rrid_resource_type`: varchar(100), nullable — e.g. 'core facility', 'software', 'antibody'
- `rrid_url`: varchar(500), nullable — resource URL
- `resolved_json`: JSONB, nullable — cached resolver metadata (normalized subset only)
- `last_resolved_at`: DateTime, nullable — when resolver cache was last refreshed
- `created_at`: DateTime, NOT NULL, server_default=now()
- `updated_at`: DateTime, nullable, onupdate=now()

### Model Conventions
- Add query helper class methods following the Comments model pattern:
  - `get_rrids_for_entity(entity_type, entity_id)` — returns all RRIDs for an entity
  - `get_by_rrid(rrid_value)` — looks up by RRID curie value
- `serialize()` includes all fields including `resolved_json` inline (already a small normalized subset)
- No SQLAlchemy `relationship()` defined — polymorphic entity_id prevents clean FK relationships. Query by ID using class methods instead.
- Place `DocidRrid` class after the LocalContext/PublicationLocalContext models in `models.py` (closest existing pattern)

### Entity Reference Design
- Both DB-level CHECK constraint AND Python-side validation for `entity_type`
  - CHECK constraint: `entity_type IN ('publication', 'organization')` in the Alembic migration
  - Python validation: allowlist check in blueprint before any DB write
- Application-level cascade cleanup in delete routes (not DB triggers, not periodic jobs)
  - When a publication is deleted, also delete its `docid_rrids` rows (entity_type='publication')
  - When a publication_organization is deleted, also delete its `docid_rrids` rows (entity_type='organization')
- Entity type values are short lowercase strings: `'publication'`, `'organization'`
- Add `resolve_entity(entity_type, entity_id)` helper function that maps entity_type to the model class and fetches the row — validates entity exists before RRID attachment

### Migration Approach
- Autogenerate migration from model, then review and adjust
- Include full downgrade path (drop table) — follows existing DOCiD migration patterns
- Explicit index names:
  - Composite index: `ix_docid_rrids_entity_lookup` on (entity_type, entity_id)
  - Unique constraint: `uq_docid_rrids_entity_rrid` on (entity_type, entity_id, rrid)
- Include 2-3 sample RRID seed records for development testing (actual RRID values from SciCrunch)

### Claude's Discretion
- Exact `__repr__` format for the model
- Column ordering in the migration (follow logical grouping)
- Which specific sample RRIDs to include as seed data
- Whether to add `__tablename__` explicitly or let SQLAlchemy infer

</decisions>

<specifics>
## Specific Ideas

- Follow the `LocalContext` model pattern (external_id, cached metadata, timestamps) as the closest existing reference
- The Comments model (`PublicationComments`) is the gold standard for class method patterns in this codebase
- Existing DOCiD identifier pattern: `identifier` (String 500) + `identifier_type` (String 50) — but we're using a dedicated table instead

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-database-foundation*
*Context gathered: 2026-02-24*
