# DOCiD security hardening work summary

**Work period:** 20–22 July 2026

**Repository:** Africa-PID-Alliance/DOCiD

**Final branch:** `main`

## Objective

Close the unauthenticated PID-minting path, make Flask the authoritative
security boundary for all mutations, preserve incident evidence, and deploy
the remediation consistently across DOCiD Core/KENET, Docker demo, and Docker
production.

## Application security changes

### Backend authentication and authorization

- Added reusable database-backed authorization helpers:
  - `database_user_required`
  - `owner_or_admin_required`
  - `pid_minter_required`
  - `admin_required`
- Added JWT enforcement to protected `POST`, `PUT`, `PATCH`, and `DELETE`
  routes across publications, comments, profiles, Cordra, ARK, CSTR, RAID,
  RRID, Local Contexts, SMTP, analytics, harvest administration, and external
  integrations.
- PID writes now require a valid login-issued JWT and a current database role
  of `pid_minter` or `admin`.
- Caller identity and role are loaded from the database instead of trusting
  request-body identity fields.

### PID namespace protection

- Secured all Cordra mint/write endpoints, including Container iD and APA
  Handle assignment.
- Added a configurable `PID_MINTING_ENABLED` kill switch.
- Disabled Cordra sample/debug routes by default.
- Required an `Idempotency-Key` for PID writes to prevent duplicate minting.
- Added per-user and per-IP PID rate limits.
- Sanitized Cordra error responses so credentials and upstream details are not
  exposed.
- Added an immutable `pid_mint_audit` table for PID write attempts.

### Frontend enforcement

- Added JWT forwarding and validation to frontend mutation proxies.
- Protected browser routes through middleware where authentication is
  required.
- Added consistent handling for missing and expired access tokens.
- Confirmed that frontend controls supplement, but do not replace, backend
  enforcement.

### Registration, social authentication, and password reset

- Introduced a server-only `AUTH_BOOTSTRAP_SECRET` between the Next.js server
  and Flask authentication bootstrap endpoints.
- Stored registration and password-reset tokens as SHA-256 digests instead of
  plaintext.
- Made reset expiry server-controlled and removed reset tokens from API
  responses and logs.
- Required JWT ownership checks when a social-authenticated user sets a
  password.
- Retired legacy social-registration endpoints that bypassed the hardened
  bootstrap flow.
- Added rate limits to registration and password-reset endpoints.

### General immutable mutation auditing

- Added the append-only `mutation_audit` table for every state-changing HTTP
  request.
- Audit records include request ID, actor ID and role, method, route, payload
  hash, response status, outcome, source address, user agent, and timestamp.
- PostgreSQL triggers reject updates or deletions of audit records.
- Direct administrative assignment of the approved PID role was also recorded
  in the immutable audit table.

## Shared rate limiting

- Configured Flask-Limiter to use Redis instead of per-process memory.
- Corrected the existing malformed Redis bind configuration on Core/KENET and
  restricted it to localhost.
- Docker demo and production use their isolated Compose Redis service.
- Verified persisted limiter keys in Redis.

## Database migrations

Two security migrations were deployed:

- `f4a8c2d1e6b9` — PID mint audit table
- `a7c9e2f4b6d8` — immutable general mutation audit table and trigger

All three databases were verified at `a7c9e2f4b6d8 (head)`.

## Environment rollout

| Environment | Code deployed | Migration | Redis limiter | PID minting |
| --- | --- | --- | --- | --- |
| DOCiD Core/KENET | Yes | Head | Local Redis | Disabled |
| Docker demo | Yes | Head | Compose Redis | Disabled |
| Docker production | Yes | Head | Compose Redis | Enabled for approved roles |

Core/KENET and demo remain unable to mint because they currently point at the
same official Cordra namespace as production. This prevents test activity from
polluting the public registry.

## Approved PID operator

Morris Mutinda (`morrismutinda468@gmail.com`, user ID `151`) was approved as
the delegated operator who creates and edits client records. His role was
changed from `Data Officer` to `pid_minter` in all three databases.

The former `Data Officer` value was only a label and was not used by any
authorization check. Normal record creation and owner-based editing remain
available, while production PID minting is now explicitly authorized.

## Verification results

Automated checks completed successfully:

- Backend maintained test suite: 66 tests passed.
- Frontend production build: passed.
- GitHub Actions deployments and health checks: passed.

Direct production security checks returned:

- Missing JWT on frontend PID proxy: `401 Unauthorized`
- Missing JWT on direct Flask PID endpoint: `401 Unauthorized`
- Valid ordinary-user JWT on PID endpoint: `403 Forbidden`
- Approved `pid_minter` JWT with kill switch enabled: `503`, proving role
  recognition without creating a test identifier
- Missing authentication bootstrap secret: `403 Forbidden`
- Valid bootstrap secret with invalid payload: `400 Bad Request`, proving the
  trusted server path was accepted
- Retired legacy social-registration endpoint: `410 Gone`

After production minting was enabled, anonymous requests continued returning
`401` and ordinary authenticated users continued returning `403`. No test PID
was minted during verification.

## Cordra investigation and remediation

Pre-remediation logs and service metadata were preserved before deployment.
The Cordra inventory contained 14,327 objects:

| Type | Count |
| --- | ---: |
| `APA_Handle_ID` | 13,915 |
| `Container iD` | 407 |
| `Schema` | 5 |

Of the Container iD records, 169 matched the minimal shape written by the
formerly unauthenticated endpoint. That shape alone was not treated as proof
that every record was unauthorized.

One disclosed integration probe was conclusively identified and correlated
with the production Nginx access log:

- `20.500.14351/d823920b601a74c29754`

Its original evidence was preserved and hashed. The identifier was tombstoned
in place rather than deleted, so it now resolves to an explicit unauthorized
probe notice and cannot be mistaken for a valid registered object. The other
168 unattributed records were left unchanged pending owner and governance
review.

No evidence showed that the Cordra credential itself was disclosed or used
outside DOCiD's application path, so credential rotation was not required.

## Evidence location

The pre-remediation Cordra archive is stored on DOCiD Core at:

`/home/tcc-africa/docid_project/security-evidence/20260720-pre-remediation/cordra-security-inventory-20260720-pre-tombstone.tgz`

SHA-256:

`bf1536c57b4bf6fc9e364f212a0bdbbe2df000bfbf0ba512c55bb237e4739124`

Environment-specific application and proxy evidence is stored in matching
`20260720-pre-remediation` directories on the application hosts.

## Relevant commits

- `bfb8f97` — Enforce frontend JWT mutations and document security fix
- `d3ea1a2` — Secure Flask mutation routes and PID minting
- `11b29a2` — Harden authentication bootstrap and audit mutations
- `cb64306` — Document Cordra security incident remediation
- `362a62c` — Record proxy evidence for Cordra probe
- `8d1318a` — Record approved PID minter assignment

## Remaining administrative item

The partner notification wording has been prepared. Delivery remains outside
the repository because no recipient address or messaging integration is
configured here.
