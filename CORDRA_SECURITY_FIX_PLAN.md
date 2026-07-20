# Cordra and Flask Route Security Fix Plan

## Objective

Protect DOCiD's PID namespace by making Flask the authoritative security boundary for every state-changing operation. Frontend authentication remains useful for user experience, but no direct backend request may create, update, or delete protected data without a valid JWT and the required authorization.

## Phase 0 — Immediate Containment

1. Temporarily disable or firewall these Cordra write endpoints:

   - `POST /api/v1/cordoi/assign-doi/container-id`
   - `POST /api/v1/cordoi/assign-identifier/apa-handle`
   - `POST /api/v1/cordoi/assign-doi/indigenous-knowledge`
   - `POST /api/v1/cordoi/assign-doi/patent`
   - `POST /api/v1/cordoi/assign-doi/user`
   - `POST /api/v1/cordoi/push-apa-sample`
   - `GET /api/v1/cordoi/deposit-metadata`

2. Preserve Flask, reverse-proxy, and Cordra logs before normal log rotation removes evidence.
3. Export identifiers minted during the exposure window for investigation.
4. Do not delete suspicious persistent identifiers blindly. Quarantine or tombstone them according to the PID governance policy.

## Phase 1 — Establish the Backend Security Boundary

Create reusable Flask authorization utilities:

- Use `@jwt_required()` for authentication.
- Add `@pid_minter_required` for namespace-writing operations.
- Add `@admin_required` for administrative operations.
- Add owner-or-admin checks for user-owned records.
- Resolve the authenticated user from `get_jwt_identity()` and load their current role from the database.

Use explicit database roles such as:

- `user`
- `pid_minter`
- `admin`

Never trust `user_id`, `owner`, `role`, email, account type, or similar identity fields supplied in request bodies. JWT claims identify the caller; database records determine their current permissions.

## Phase 2 — Protect Cordra Operations

Apply `@jwt_required()` and `@pid_minter_required` to every Cordra mint or write route in `backend/app/routes/cordoi.py`.

Additional changes:

- Change `GET /deposit-metadata` to `POST` because it has side effects.
- Remove sample and debug routes from production, or disable them with a production configuration flag.
- Derive the actor and record owner from the JWT identity.
- Validate allowed resource types and metadata schemas before calling Cordra.
- Introduce an idempotency key to prevent accidental or automated duplicate minting.
- Reject attempts to submit another user's identity, privileged role, or credentials.
- Return sanitized upstream errors without exposing Cordra configuration or credentials.

## Phase 3 — Protect All Mutation Routes

Audit every Flask `POST`, `PUT`, `PATCH`, and `DELETE` route.

Explicitly exempt only authentication bootstrap operations that cannot already have a login-issued access token, including:

- Login
- Registration and verified social-provider callbacks
- Password-reset initiation and completion
- Refresh-token exchange, which must validate a refresh JWT

All other mutations must require JWT authentication and the appropriate role or ownership authorization.

Priority modules:

- `backend/app/routes/cordoi.py`
- `backend/app/routes/user_profile.py`
- `backend/app/routes/comments.py`
- `backend/app/routes/publications.py`
- `backend/app/routes/arks.py`
- `backend/app/routes/raid.py`
- `backend/app/routes/cstr.py`
- `backend/app/routes/localcontexts.py`
- `backend/app/routes/smtp.py`
- Integration deletion routes in DSpace, OJS, Figshare, and RRID

For each protected operation:

1. Authenticate with JWT.
2. Resolve the caller from the JWT identity.
3. Load the target object.
4. Check ownership or the required role.
5. Perform the mutation.
6. Write an audit event.

## Phase 4 — Abuse Controls and Audit Logging

Add configurable limits such as:

- PID minting: 5 requests per minute per authenticated user.
- PID minting: 100 requests per day per authenticated user.
- Additional limits per source IP.
- Stricter limits after repeated validation or authorization failures.

Record immutable audit events containing:

- Authenticated user ID and role
- Timestamp and request ID
- Source IP and user agent
- Operation and resource type
- A payload hash instead of sensitive raw content
- Resulting Handle or identifier
- Success or failure status
- Upstream Cordra operation ID where available

Remove global logging of complete request and response bodies. It can record passwords, password-reset tokens, JWTs, and personal information. Use structured, field-level logging with explicit redaction.

CAPTCHA may supplement public registration or recovery flows, but it must not replace authentication or authorization on PID-writing endpoints.

## Phase 5 — Tests and CI Enforcement

Add automated tests covering:

- Missing token returns `401`.
- Invalid or expired token returns `401`.
- A normal user calling a PID mint endpoint receives `403`.
- An authorized `pid_minter` can mint successfully.
- An administrator can perform explicitly approved administrative operations.
- Submitted `user_id`, owner, or role spoofing is rejected or ignored.
- A duplicate idempotency key returns the original result without minting again.
- Exceeding the configured limit returns `429`.
- Direct Flask requests cannot bypass frontend controls.
- Cross-user edits and deletes return `403`.
- Audit events are created for successful and failed mint attempts.
- Tokens, passwords, and credentials are absent from logs and error responses.

Add a CI route audit that fails when a non-allowlisted `POST`, `PUT`, `PATCH`, or `DELETE` Flask route lacks an approved authentication decorator. The audit should also flag administrative or destructive routes that have authentication but no role or ownership check.

## Phase 6 — Deployment and Incident Review

1. Deploy backend JWT and authorization enforcement first.
2. Deploy or retain frontend JWT attachment and forwarding second.
3. Confirm required roles exist and assign `pid_minter` only to approved accounts.
4. Smoke-test the public backend URL directly, not only through the browser interface.
5. Confirm anonymous requests return `401` and ordinary authenticated users return `403`.
6. Review historical Cordra records for unusual volume, sample metadata, repeated source IPs, invalid ownership, or rapid sequential minting.
7. Quarantine or tombstone confirmed unauthorized identifiers.
8. Rotate Cordra credentials if investigation shows credential exposure or suspicious upstream access.
9. Notify the reporting integration partner after backend enforcement and investigation are complete.

## Deployment Order

The safe order is:

1. Preserve evidence and temporarily contain exposed write endpoints.
2. Add backend authentication and authorization.
3. Add backend tests and run the complete suite.
4. Deploy backend changes.
5. Verify direct-backend `401` and `403` responses.
6. Deploy frontend JWT forwarding changes.
7. Enable authorized production minting.
8. Complete historical review and partner notification.

Do not deploy frontend enforcement as the only mitigation. A caller can bypass the frontend and access Flask directly.

## Acceptance Criteria

The remediation is complete only when all the following are true:

- No PID-writing operation succeeds without a valid login-issued JWT.
- Only database-authorized `pid_minter` or approved administrator accounts can mint identifiers.
- Client-supplied identity and role fields cannot affect authorization decisions.
- All other state-changing routes have explicit authentication and authorization policies.
- Anonymous direct requests to Flask return `401`.
- Authenticated but unauthorized requests return `403`.
- Minting is rate-limited and idempotent.
- Every mint attempt creates a sanitized audit event.
- CI prevents new unprotected mutation routes from being merged.
- Previously minted identifiers from the exposure window have been reviewed and dispositioned.

## Implementation Progress — 2026-07-20

Implemented in code:

- Database-backed `user`, `pid_minter`, and `admin` authorization helpers.
- JWT and role enforcement on all Cordra writes, with minting disabled by default.
- Per-user/IP minute and daily PID mint limits.
- Required idempotency keys and replay of completed PID operations.
- Sanitized PID audit records containing actor, request ID, payload hash, result, IP, and user agent.
- Debug/sample Cordra routes disabled by default and the credential-bearing user PID route retired.
- Ownership enforcement for profiles, comments, drafts, publication versions, RRID attachments, and integration deletion routes.
- Admin enforcement for harvest-source management, bulk DSpace deletion, SMTP, and credential/token operations.
- JWT enforcement for every non-bootstrap Flask `POST`, `PUT`, `PATCH`, and `DELETE` route.
- Frontend JWT enforcement and idempotency-key forwarding.
- CI route-audit tests that reject newly introduced unauthenticated mutation routes.
- Request/response body logging removed from the global Flask logger.

Still required during deployment and incident response:

- Apply the `pid_mint_audit` migration in every environment before serving the new backend.
- Assign `pid_minter` only to approved accounts, then explicitly set `PID_MINTING_ENABLED=true`.
- Configure a shared production limiter backend (for example Redis) for multi-worker enforcement.
- Preserve and review historical Flask, proxy, and Cordra logs and records from the exposure window.
- Quarantine or tombstone confirmed unauthorized identifiers under the PID governance policy.
- Rotate Cordra credentials if the review indicates exposure, then notify the reporting partner.
