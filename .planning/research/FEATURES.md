# Feature Research

**Domain:** RRID/SciCrunch Integration for DOCiD PID Platform
**Researched:** 2026-02-24
**Confidence:** HIGH

---

## Context: What RRIDs Are and Who Needs Them

RRIDs are persistent identifiers for research resources — specifically the tools,
reagents, and infrastructure used in scientific experiments. The five registry-backed
resource types are: **Tools/Software** (prefix `SCR_`), **Antibodies** (`AB_`),
**Cell Lines** (`CVCL_`), **Model Organisms** (`MGI_`, `ZFIN_`, etc.), and
**Core Facilities** (also `SCR_`, same registry as Tools).

In the DOCiD context, the Africa PID Alliance partnership makes **core facilities**
the primary use case — African research infrastructure (labs, microscopy centers,
genomics facilities) needs to be credited in publications. Core facilities are
registered in the SciCrunch Tools index (`RIN_Tool_pr`, type filter:
`item.types.name: "core facility"`).

**Key distinction surfaced by research (rrids.org, 2024):** RRIDs track core
facility *acknowledgements* (what resources were used in an experiment). ROR IDs
track *contributor affiliations* (where researchers work). Both can apply to the
same facility, but they serve different metadata slots in a publication record. This
means attaching an RRID to `PublicationOrganization` is semantically different from
attaching a ROR ID — the former acknowledges a resource used, the latter records an
organizational affiliation. The feature must preserve that distinction in the UI.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features a research platform integrating an identifier system must have. Missing
any of these makes the integration feel unfinished.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| RRID search by keyword with type filter | Every identifier integration in DOCiD (ROR, ORCID, RAiD) has a search modal. Users expect the same UX for RRID. | MEDIUM | Must hit SciCrunch `RIN_Tool_pr/_search` through backend proxy. Type filter dropdown required: core facility, software, antibody, cell line. Default type: core facility. |
| Attach RRID to a publication | Core action. Without this the search is pointless. | MEDIUM | POST to create `docid_rrids` row linking `entity_type=publication`, `entity_id`. Follows LocalContext `PublicationLocalContext` pattern. |
| Attach RRID to an organization | `PublicationOrganization` rows already have `identifier`/`identifier_type` slots. Users expect organization records to carry their RRID just as they carry a ROR ID. | MEDIUM | POST to create `docid_rrids` row with `entity_type=organization`, `entity_id`. Organization entity scope = `publication_organizations.id`. |
| Display attached RRIDs on publication detail page | DOCiD detail page already shows creators (ORCID), organizations (ROR), funders (ROR), projects (RAiD). RRID must appear in the same section pattern. | LOW | GET `docid_rrids` filtered by `entity_type` + `entity_id`. Render as linked badge: `RRID:SCR_012345` linking to `https://scicrunch.org/resolver/RRID:SCR_012345`. |
| Display attached RRIDs on organization display | Same expectation as publication display. | LOW | Reuses the same GET endpoint, different `entity_type`. |
| Resolve a known RRID to metadata | When user enters `RRID:SCR_012345` directly (already has it), they expect to resolve it without searching. Direct resolve is standard across all RRID-aware platforms. | LOW | GET `/api/integrations/rrid/resolve?rrid=RRID:SCR_012345` proxying `https://scicrunch.org/resolver/<RRID>.json`. No API key required by resolver. |
| Detach/remove an RRID from an entity | Users make mistakes attaching the wrong RRID. Every attach workflow needs a remove action. | LOW | DELETE on `docid_rrids` by ID. Soft delete or hard delete acceptable; hard delete preferred for this use case (no audit requirement stated). |
| DB-level caching of resolver metadata | DOCiD explicitly uses DB caching (see `LocalContext.cached_at`, `last_sync_attempt`). Users on slow networks (Africa context) expect fast repeated lookups. SciCrunch latency is variable. | MEDIUM | Store `resolved_json` JSONB + `last_resolved_at` on `docid_rrids`. Re-use cached data if `last_resolved_at` < 30 days. Same TTL pattern as LocalContexts. |
| RRID format validation | Every PID integration validates the format before storing. Users expect clear error feedback for `AB_123` vs `RRID:AB_123456789`. | LOW | Regex server-side: `^RRID:(SCR_\d{6,9}\|AB_\d{6,11}\|CVCL_\w+\|MGI:\d+\|ZFIN:\w+)$`. Normalize by auto-prepending `RRID:` prefix if absent. |
| Backend tests (request/parse + schema validation) | Explicitly required in PROJECT.md acceptance criteria. Every other blueprint in DOCiD has test coverage. | LOW | Pytest: mock SciCrunch response, assert normalized output shape, assert schema validation catches bad input. |

### Differentiators (Competitive Advantage)

Features that would make DOCiD's RRID integration genuinely better than a minimal
attach-and-display implementation. These create direct value for the Africa PID
Alliance partnership.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dual-tab search modal (search by name / enter RRID directly) | ORCID and ROR modals in DOCiD already use a tabbed UX (see `OrganizationsForm.jsx` — Tab 0: ROR ID lookup, Tab 1: search by name). Applying the same pattern to RRID makes the UX immediately familiar and handles both the "I know the RRID" and "I need to find it" flows. | LOW | Two tabs: "Search by Name" (keyword + type dropdown + results list) and "Enter RRID" (text field + resolve button + metadata preview). MUI `Tabs` + `TabPanel` exactly as in `OrganizationsForm.jsx`. |
| Proper RRID citation string displayed on attach confirmation | SciCrunch returns `rrid.properCitation` in resolver responses (e.g., `"DSHB Cat# nc82, RRID:AB_2314866"`). Showing this at confirmation time teaches users the correct citation format for their methods sections — a known pain point in RRID adoption. | LOW | Extract `hits.hits[0]._source.rrid.properCitation` from resolver JSON. Display in confirmation chip/tooltip. Store in `resolved_json`. |
| RRID type badge with color coding on display | Core facilities, software, antibodies, and cell lines are visually distinct resource types. Color-coded MUI `Chip` components (matching DOCiD's existing badge style from comments/local contexts) help users scan attached resources at a glance. | LOW | Map type prefix to color: `SCR_` = blue (tools/software), `AB_` = red (antibody), `CVCL_` = green (cell line). Use MUI `Chip` with `size="small"`. |
| Prevent duplicate RRID attachment | `PublicationLocalContext` already has `UniqueConstraint('publication_id', 'local_context_id')`. The same discipline should apply to RRID: attaching the same `RRID:SCR_012345` twice to the same publication should be blocked at DB level, not just UI level. | LOW | `UniqueConstraint('entity_type', 'entity_id', 'rrid')` on `docid_rrids`. Return 409 Conflict with readable message on duplicate. |
| Resource type filter defaulting to "core facility" | DOCiD serves African research infrastructure. Core facilities (shared labs, instruments) are the primary RRID type for this context. Defaulting the type filter there reduces friction for the primary user workflow. | LOW | Set `type=core facility` as default in search query. User can change dropdown to access software, antibody, cell line searches. |
| `mentions` count display from resolver JSON | The SciCrunch resolver returns `mentions` (citation count in literature, e.g., 434 for the antibody example fetched during research). Displaying this gives researchers quick validation that the resource they're attaching is widely recognized. | LOW | Extract `_source.mentions` from resolved JSON. Show as small count label: "Cited 434 times". Cache in `resolved_json`. Only display when count > 0. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Direct client-side SciCrunch API calls | Simpler to implement — no backend proxy route needed. | Exposes the SciCrunch API key to browser. The Africa PID Alliance API key is a shared credential and must never be public. Explicitly prohibited in PROJECT.md constraints. | Backend proxy blueprint at `/api/integrations/rrid/*` that injects `apikey` header server-side. Already the pattern for CORDRA, CSTR, Local Contexts. |
| Bulk RRID sync for local fast search | Faster search response, offline capability. | Requires Elasticsearch scroll (complex), large storage, background job infrastructure, sync scheduling — none of which DOCiD has. Explicitly deferred in PROJECT.md out-of-scope section. | DB-level caching of resolver results per RRID. Search goes to SciCrunch live. Add `size=10` limit to keep response times manageable. |
| RRID attachment to creators/projects | Researchers use tools and it seems natural to tag a creator's ORCID record with the tools they use. | Scope creep without clear user story. Creators already have ORCID/ISNI. Projects already have RAiD. Neither has a convention for attaching tool RRIDs. Explicitly out of scope in PROJECT.md. | Stick to publications and organizations for this milestone. Revisit in a future milestone with a concrete user story. |
| Redis caching for search results | Faster repeated searches, common pattern in web services. | DOCiD uses Flask-Caching (already configured), not Redis. Adding Redis for RRID search results introduces infrastructure complexity without proportional benefit given search is paginated and results can vary. | Flask-Caching with short TTL (5 min) for search query responses. DB-level caching for resolver results. This is the pattern the PROJECT.md specifies explicitly. |
| Generic `docid_external_identifiers` table (Option A) | More flexible — future identifier types could reuse the table without a new migration. | Project decision was explicitly for `docid_rrids` (Option B) for strict RRID separation. A generic table makes querying, indexing, and serialization more complex with no immediate payoff. | Dedicated `docid_rrids` table as specified. If a new identifier type arrives later, a new dedicated table can be added following the same pattern. |
| RRID autocomplete/typeahead search | Feels more modern UX than a search button + results list. | SciCrunch Elasticsearch search has non-trivial latency (up to 25s timeout in the spec document). Autocomplete on every keystroke would degrade UX and hammer the API. | Debounced search triggered by explicit "Search" button or Enter key press. This is exactly what ROR and ORCID search modals do in DOCiD today. |

---

## Feature Dependencies

```
[Backend Flask Blueprint]
    └── requires --> [SCICRUNCH_API_KEY env var]
    └── requires --> [docid_rrids Alembic migration]
                        └── requires --> [Publications model FK] (publication_id)
                        └── requires --> [PublicationOrganization model FK] (organization_id)

[RRID Search Modal (Frontend)]
    └── requires --> [Next.js API proxy routes for RRID]
                        └── requires --> [Backend Flask Blueprint]

[RRID Attach action]
    └── requires --> [RRID Search or Resolve (user must have an RRID to attach)]
    └── requires --> [Backend POST /api/integrations/rrid/attach endpoint]

[RRID Display on publication detail page]
    └── requires --> [Backend GET /api/integrations/rrid/entity?type=publication&id=X]
    └── requires --> [docid_rrids rows exist (attach must have run first)]

[DB-level resolver caching]
    └── enhances --> [RRID Resolve endpoint] (first call fetches, subsequent calls use cache)
    └── requires --> [resolved_json JSONB column on docid_rrids]

[Citation string display]
    └── requires --> [DB-level resolver caching] (properCitation stored in resolved_json)

[Type badge display]
    └── requires --> [RRID Display on publication detail page]
    └── requires --> [rrid column to determine prefix: SCR_, AB_, CVCL_]

[Duplicate prevention]
    └── requires --> [docid_rrids UniqueConstraint at DB level]
    └── enhances --> [RRID Attach action] (prevents user error silently at DB level)
```

### Dependency Notes

- **Backend blueprint requires migration:** The Alembic migration creating `docid_rrids` must run before any endpoints can write RRID records. This determines phase ordering — migration is Phase 1.
- **Frontend proxy requires backend blueprint:** Next.js API routes for RRID cannot be built without working Flask endpoints to proxy. Frontend is Phase 3.
- **Display requires prior attach:** The detail page display feature is only testable end-to-end after attach works. Test the display unit (rendering from mock data) independently.
- **Citation string display requires resolver caching:** `properCitation` lives in `resolved_json`. The caching feature must store this field during the first resolve call.
- **RRID Attach to Organization requires knowing the `PublicationOrganization.id`:** The frontend must pass the organization row's PK (integer), not the ROR ID string, as `entity_id`. This is how `LocalContext` handles it — `entity_id` references the junction table row.

---

## MVP Definition

### Launch With (v1)

Minimum to satisfy the milestone goal and PROJECT.md acceptance criteria.

- [ ] Alembic migration creating `docid_rrids` table with `entity_type`, `entity_id`, `rrid`, `resolved_json`, `last_resolved_at`, and `UniqueConstraint` — without this nothing else works
- [ ] Flask blueprint with search endpoint (`POST RIN_Tool_pr/_search` proxy, type filter, keyword query)
- [ ] Flask blueprint with resolve endpoint (`GET scicrunch.org/resolver/<RRID>.json` proxy, DB cache write)
- [ ] Flask blueprint with attach endpoint (`POST`, creates `docid_rrids` row, returns 409 on duplicate)
- [ ] Flask blueprint with list endpoint (`GET`, returns all RRIDs for an entity)
- [ ] Flask blueprint with detach endpoint (`DELETE`, removes `docid_rrids` row by ID)
- [ ] Next.js API proxy routes for all five Flask endpoints above
- [ ] RRID search modal on publication detail page (search tab + direct RRID entry tab, MUI Dialog)
- [ ] RRID search modal on organization rows in assign-docid form
- [ ] RRID display on `docid/[id]/page.jsx` (linked RRID badges, type-colored chips)
- [ ] Backend tests: mock SciCrunch search response and resolver response, assert normalized output, assert schema validation

### Add After Validation (v1.x)

Features that are low effort and high value once v1 is confirmed working.

- [ ] `properCitation` shown at attach confirmation time — add once resolver caching is confirmed working end-to-end
- [ ] `mentions` count shown on display — add once `resolved_json` structure is confirmed stable
- [ ] RRID display on organization management pages (not just publication detail) — add once publication display is proven

### Future Consideration (v2+)

Features explicitly deferred.

- [ ] Bulk RRID sync for local fast search — requires background job infrastructure and Elasticsearch scroll
- [ ] RRID attachment to creators (ORCID records linking to tools they use) — needs a concrete user story and model change
- [ ] RRID attachment to projects (RAiD records linking to tools used in the project) — same as above
- [ ] Model Organism RRID support (MGI, ZFIN, RGSC prefixes) — needs separate Organism index queries, different resolver patterns

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| DB migration + `docid_rrids` model | HIGH | LOW | P1 |
| Flask search endpoint | HIGH | MEDIUM | P1 |
| Flask resolve endpoint + DB cache write | HIGH | MEDIUM | P1 |
| Flask attach endpoint | HIGH | LOW | P1 |
| Flask list + detach endpoints | HIGH | LOW | P1 |
| Duplicate prevention (UniqueConstraint) | HIGH | LOW | P1 |
| Next.js API proxy routes | HIGH | LOW | P1 |
| RRID search modal (publication) | HIGH | MEDIUM | P1 |
| RRID search modal (organization) | HIGH | MEDIUM | P1 |
| RRID display on publication detail | HIGH | LOW | P1 |
| RRID format validation | HIGH | LOW | P1 |
| Backend tests | HIGH | LOW | P1 |
| Dual-tab modal UX (search + direct entry) | MEDIUM | LOW | P2 |
| Type-colored badge on display | MEDIUM | LOW | P2 |
| `properCitation` at confirmation | MEDIUM | LOW | P2 |
| `mentions` count display | LOW | LOW | P3 |
| RRID display on organization management page | MEDIUM | LOW | P2 |

**Priority key:**
- P1: Must have for this milestone launch
- P2: Should have, add within this milestone if time allows
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | SciCrunch Portal (scicrunch.org) | DOI/ROR integrators (e.g., Zenodo, OpenAIRE) | DOCiD Approach |
|---------|----------------------------------|-----------------------------------------------|----------------|
| RRID search UI | Full-text search with faceted filters by resource type, organism, keyword | Not applicable (these platforms don't integrate RRID) | Keyword + type dropdown in modal. Start with core facility default. |
| RRID display | Full resource page with citation, description, vendor, literature count | Not applicable | RRID badge linking to resolver. Type chip. `properCitation` on hover. |
| Direct RRID entry | URL bar entry (e.g., `scicrunch.org/resolver/RRID:SCR_012345`) | Not applicable | Tab 1 in modal: text field + resolve button. Same UX as ROR ID tab in OrganizationsForm. |
| Bulk/export | CSV download, API scroll for full datasets | Not applicable | Out of scope for this milestone. |
| RRID + ROR co-display | Not integrated | Not applicable | DOCiD uniquely positions itself: show both ROR ID and RRID for an organization, with clear labels distinguishing affiliation vs resource acknowledgement. |

---

## Existing DOCiD Model Dependencies

These existing models must be understood before implementing RRID. No changes to these
models are required — `docid_rrids` references them by ID.

| Existing Model | Table | How RRID Attaches To It |
|---------------|-------|-------------------------|
| `Publications` | `publications` | `entity_type='publication'`, `entity_id=publications.id` |
| `PublicationOrganization` | `publication_organizations` | `entity_type='organization'`, `entity_id=publication_organizations.id` |

**Implications:**
- RRID is attached to the junction row (`publication_organizations.id`), not to a
  standalone organization record. This mirrors how LocalContext attaches to a
  publication (via `publication_id`), not to a generic entity table.
- The list endpoint must accept `entity_type` + `entity_id` as query params, exactly
  as specified in the integration spec.
- Deleting a `publication_organizations` row should cascade to `docid_rrids`. Use
  `ON DELETE CASCADE` on the FK, or use SQLAlchemy `cascade="all, delete-orphan"`.
  (Note: `entity_id` is an integer, not a FK — handle cascade via application logic
  or use a DB trigger. Simpler: clean up orphaned RRID rows in the detach/delete
  organization endpoint.)

---

## Sources

- [SciCrunch API Handbook — Research Resource Identifiers](https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/research-resource-identifiers)
- [SciCrunch API Handbook — Searching RIN Indices](https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/searching-rin-indices)
- [SciCrunch API Handbook — RIN Elasticsearch JSON Data Model](https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/rin-elaticsearch-json-data-model)
- [SciCrunch API Handbook — Basic RIN Search Examples](https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/basic-rin-search-examples)
- [SciCrunch API Handbook — The RRID Resolver](https://docs.scicrunch.io/elasticsearch-metadata-services/resource-information-network-rin-services/the-rrid-resolver)
- [rrids.org — Understanding RRID and ROR for Facilities (2024)](https://www.rrids.org/news/2024/11/26/understanding-rrid-and-ror-for-facilities)
- [rrids.org — RRID System](https://www.rrids.org/rrid-system)
- [INCF — Research Resource Identifier (RRID)](https://www.incf.org/research-resource-identifier)
- [NIH ORIP — Research Resource Identifiers](https://orip.nih.gov/division-comparative-medicine/research-resources-directory/research-resource-identifiers-rrids)
- [SciCrunch Resolver live example (antibody)](https://scicrunch.org/resolver/RRID:AB_2314866.json)
- [RRID FAQ — SciCrunch](https://www.scicrunch.com/faq-rrid)
- DOCiD integration spec: `backend/temp/DOCID_Add_RRID_Integration.md`
- DOCiD existing models: `backend/app/models.py` (LocalContext/PublicationLocalContext pattern)
- DOCiD existing ROR pattern: `backend/app/routes/ror.py`
- DOCiD existing frontend modal pattern: `frontend/src/app/assign-docid/components/OrganizationsForm.jsx`

---

*Feature research for: RRID/SciCrunch integration milestone on DOCiD platform*
*Researched: 2026-02-24*
