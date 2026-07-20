# Cordra access-control incident remediation — 2026-07-20

## Status

The unauthenticated Cordra minting path has been closed and the hardened release
`11b29a2` has been deployed to DOCiD Core/KENET, Docker demo, and Docker
production. PID minting remains globally disabled pending explicit approval of
the accounts that may receive the `pid_minter` role.

Direct write-endpoint smoke tests returned:

- anonymous request: `401 Unauthorized`
- authenticated ordinary user: `403 Forbidden`

The tests used non-minting payloads and did not reach Cordra.

## Evidence preservation

Before deployment, application and service-log inventories were captured in
timestamped `20260720-pre-remediation` directories on all application hosts.
The complete pre-tombstone Cordra search inventory was archived on DOCiD Core
as:

`/home/tcc-africa/docid_project/security-evidence/20260720-pre-remediation/cordra-security-inventory-20260720-pre-tombstone.tgz`

Archive SHA-256:

`bf1536c57b4bf6fc9e364f212a0bdbbe2df000bfbf0ba512c55bb237e4739124`

## Cordra findings

The inventory contained 14,327 objects:

| Object type | Count |
| --- | ---: |
| `APA_Handle_ID` | 13,915 |
| `Container iD` | 407 |
| `Schema` | 5 |

Of the 407 `Container iD` objects, 169 have only `id`, `groupName`, and
`description` in their content. This is the exact shape written by the formerly
unauthenticated `/api/v1/cordoi/assign-doi/container-id` route. These records
therefore lack an attributable DOCiD `user_id`, but that fact alone does not
prove that every record was malicious or created without organizational
approval.

One object is conclusively the disclosed integration probe:

- ID: `20.500.14351/d823920b601a74c29754`
- created: 2026-07-19 07:21:43 UTC
- original title: `Test Title For URAAS Integration Probe`
- original description: `A test description for probing the real docid assignment API.`

The production Nginx access log independently correlates the same timestamp
with a `POST /api/cordoi/assign-doi/container-id` response of `200`. The source
address and full log line are retained in
`confirmed-probe-nginx-lines.txt` in the production evidence directory and are
not reproduced here.

The original object was preserved in the evidence archive. On 2026-07-20 it
was tombstoned in place, retaining the persistent identifier while replacing
the public record with an explicit unauthorized-probe notice. The post-change
object SHA-256 is:

`3f7e3f4f0319037fce655c27907f47e8c4528d26eb8d2131c92dbe5773d53864`

No other object was changed. The remaining 168 unattributed records require a
governance review with record owners before quarantine; test-like names alone
are not sufficient evidence for destructive or reputational action.

## Credential decision

The vulnerable route used DOCiD's server-side Cordra credential as a proxy but
did not return that credential to callers. The preserved evidence contains no
indication that the Cordra credential itself was disclosed or used outside the
DOCiD application path. Cordra credential rotation is therefore not currently
required. Rotate immediately if subsequent Cordra access logs show direct
authentication from an unrecognized client or source address.

The newly introduced `AUTH_BOOTSTRAP_SECRET` was generated independently in
each environment and was never committed to Git.

## Role assignment pending approval

All three DOCiD databases contain the same sole existing operational candidate:

- Morris Mutinda (`morrismutinda468@gmail.com`), current role `Data Officer`

Changing this account to `pid_minter` requires explicit approval. The global
`PID_MINTING_ENABLED=false` kill switch remains in force until that decision is
recorded and an authorized-minter smoke test succeeds.

## Send-ready partner notification

> Thank you for reporting the unauthenticated DOCiD minting endpoint. We
> confirmed the missing backend access control, preserved the relevant logs and
> Cordra inventory, deployed JWT and role enforcement across all environments,
> enabled shared Redis rate limiting, and added immutable mutation audit events.
> Anonymous requests now receive 401 and authenticated non-minters receive 403.
> PID minting remains globally disabled pending approved-minter assignment. The
> disclosed URAAS probe identifier `20.500.14351/d823920b601a74c29754` has been
> tombstoned in place so it cannot be mistaken for a valid registered object.
> We found no evidence of personal-data exposure or Cordra credential leakage.
> Please do not perform further production security probes without written test
> authorization and an agreed scope; we are available to coordinate a safe
> integration retest.

Delivery is pending because no partner address or messaging channel is stored
in the repository.
