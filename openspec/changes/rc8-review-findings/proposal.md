# EPIC: rc8-review-findings — suspected defects and open questions found in the 1.1.0-rc.8 review

## Appetite

**Small** for the investigation (≈1 week): confirm or dismiss each finding with a failing test or a
written explanation, and get the owner's answer to each open question. The fixes are shaped separately,
per confirmed finding, once the real cause is known.

## Why

A documentation review of ERSys 1.1.0-rc.8 compared the use cases, ADRs and the ERS–ERE Technical
Contract with the code and tests at tag `1.1.0-rc.8`. Most differences were intended decisions and the
documentation was updated. The findings below were not: they look like defects, or behaviour nobody has
decided on yet. They come from static analysis of code, tests, planning notes and commit history only;
none has been reproduced at runtime. Each needs further analysis to determine the real issue before any
fix is designed. Evidence per finding is in `inputs/findings.md`.

## Solution outline

Outcome: every suspected defect is either **confirmed** (reproduced by a failing unit, BDD or
integration test, with the real cause identified) or **dismissed** (reason recorded here), and every open
question has an owner's answer recorded as a decision. Confirmed findings then get their own shaped fix.

Suspected defects:

1. **F-1 Late ERE outcome rejected after a provisional identifier.** The stale check compares the ERE
   response timestamp (ERE clock, set when the ERE builds the response) with the provisional decision's
   creation time (ERS clock, at timeout). An outcome stamped before the timeout but integrated after it,
   or any clock skew, is rejected as stale and only logged at DEBUG: the provisional identifier may stay forever.
2. **F-2 refreshBulk can lose changes.** `updated_at` is the ERE response timestamp while the per-source
   watermark is the ERS time of the final page; an outcome stamped before a refresh but integrated after
   it is never returned. The watermark is also advanced before the response is enriched and sent, so a
   failure there loses the last page.
3. **F-3 Bulk resolve per-item error codes.** Items failing with an idempotency conflict or a parsing
   error are reported as `SERVICE_ERROR` inside `/resolve-bulk` responses instead of their own codes.
4. **F-4 Decisions can become permanently non-curatable.** After one curator action, further actions get
   HTTP 409 until the ERE returns a changed outcome. An identical outcome does not clear the review flag,
   the Basic ERE ignores recommendations, and a failed publish never produces an outcome, so the block
   may never lift.
5. **F-5 Lost ERE responses and misleading log.** Responses are popped destructively; if integration
   fails (for example the document store is down) the outcome is lost, while the log says it "may be
   retried on restart". Planning notes still claim at-least-once delivery.
6. **F-6 Bulk budget timeout leaves no provisional decision.** When `/resolve-bulk` exceeds its budget,
   pending tasks are cancelled; mentions without a stored decision get none, and a late ERE outcome is
   stored as a first assignment that refreshBulk never exposes.
7. **F-7 Stale or weak tests and notes.** Some BDD rows and scenarios assert behaviour the code no longer
   has (replay status, 500 vs 503, "first bulk lookup returns all assignments") or skip their check; some
   planning notes contradict the code (budget 0, status codes, delivery semantics).

Open questions (owner decision needed):

- **Q-1** Should refreshBulk report changes where only scores or candidates changed and the cluster
  stayed the same? The code reports them; the earlier delta design said only placement changes count.
- **Q-2** Should the open self-registration endpoint (`POST /auth/register`) stay, be configurable, or go?
- **Q-3** Should the number of mentions in one bulk request be capped at the API?
- **Q-4** For F-4: release the guard on any curator-triggered ERE response, disable further actions in
  the UI with an explanation, or require the ERE to honour recommendations?

## Key decisions

- **DEC-1**: Investigate before fixing — the findings come from static analysis; each is confirmed by a
  failing test or dismissed with a reason before any code changes.
- **DEC-2**: The use cases, ADRs and the ERS–ERE Technical Contract (entity-resolution-docs, aligned with
  1.1.0-rc.8) are the reference for intended behaviour; where they are silent, the question is raised
  (Q-n) rather than decided in code.

## Rabbit-holes

- Introducing an acknowledged or transactional queue (outbox, processing lists) as part of F-5 before the
  loss cases are confirmed and sized.
- Redesigning delta tracking (F-2) without first deciding Q-1: both touch what `updated_at` means.

## No-gos

- No behaviour change in this change until each finding is confirmed or each question answered.
- No change to the ERS–ERE message models (entity-resolution-spec).
- No changes to the Link Curation UI here (UI wording is noted in `inputs/findings.md` for the webapp team).

---

## What Changes

- Investigation only at this stage: failing tests for confirmed findings, recorded conclusions for
  dismissed ones, recorded decisions for Q-1 to Q-4. Fix scope is added after the investigation.

## Capabilities

### New Capabilities
<!-- To be determined after the investigation. -->

### Modified Capabilities
<!-- To be determined after the investigation; likely outcome integration (F-1, F-5), bulk refresh (F-2),
     bulk resolution (F-3, F-6) and curation (F-4). -->

## Impact

- `src/ers/ere_result_integrator/`, `src/ers/resolution_decision_store/adapters/decision_repository.py`,
  `src/ers/resolution_coordinator/services/`, `src/ers/ers_rest_api/services/`, `src/ers/curation/`,
  `src/ers/users/` and the Curation auth endpoints (Q-2).
- BDD and integration tests under `test/feature`, `test/e2e`, `test/integration`.
- Basic ERE: F-4 depends on how the ERE treats recommendations (see the ERE change `rc8-review-findings`).
