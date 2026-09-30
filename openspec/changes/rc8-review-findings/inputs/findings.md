# Findings — evidence (static analysis at tag 1.1.0-rc.8)

Source: documentation review of ERSys 1.1.0-rc.8 (2026-09-30), comparing the use cases, ADRs and the
ERS–ERE Technical Contract (entity-resolution-docs) with the code, tests, planning notes under
`.claude/memory/epics/` and commit history. Nothing below was reproduced at runtime. Line numbers refer
to tag `1.1.0-rc.8`.

## F-1 Late ERE outcome rejected after a provisional identifier

- `_issue_provisional` (`resolution_coordinator/services/resolution_coordinator_service.py` ~293-338)
  stores the provisional decision with `updated_at=datetime.now(UTC)` (ERS clock); the insert path records
  it as the creation time.
- `_execute_update` (`resolution_decision_store/adapters/decision_repository.py` ~451-490): stale filter
  `updated_at < incoming OR (updated_at unset AND created_at < incoming)`, where `incoming` is the ERE
  `response.timestamp` (`ere_result_integrator/services/outcome_integration_service.py` ~91).
- The ERE sets `timestamp` to its own `now()` when it builds the response, before the message crosses the queue.
- `StaleOutcomeError` is caught and logged at DEBUG (`outcome_integration_service.py` ~102).
- Suspected effect: an ERE outcome integrated after the timeout but stamped before it (queue latency,
  integrator backlog) or any ERE/ERS clock skew leaves the provisional identifier in place with no later correction.
- Planning note: ERS1-214 R2 intended ordering between ERE outcomes, not between ERS and ERE clocks.
- To analyse: reproduce with an integration test; decide whether a stored provisional placement should
  always be replaceable by an ERE outcome.

## F-2 refreshBulk can lose changes

- Delta filter `updated_at > watermark` (`decision_repository.find_delta_for_source` ~1039-1075).
- `updated_at` = ERE response timestamp; watermark = ERS `now()` after the final page is queried
  (`bulk_refresh_coordinator_service.py` ~72-73, 137-138).
- Scenario: ERE stamps T, a refresh completes at S > T, the outcome is integrated after S → never returned.
- Watermark advanced before `RefreshBulkService` enriches contexts and serialises the response
  (`ers_rest_api/services/refresh_bulk_service.py` ~37-60); a failure there loses the last page.
  Use cases UC-W3/UC-B1.3 and Spine C require the advance only after a successful response.
- Concurrency: `advance_snapshot` reads then upserts without compare-and-swap
  (`request_registry_service.py` ~158-171); the documented rule is one sequential consumer per source.
- Planning note: ERS1-214 mentions "advancing to now() after the query rather than to the query-time
  bound — tracked separately"; no fix found.
- To analyse: reproduce; decide the timestamp used for delta tracking (ERS ingestion time vs ERE time).

## F-3 Bulk resolve per-item error codes

- `ers_rest_api/services/resolve_service.py` ~30-33 (`_error_code_for`): idempotency conflict and parsing
  errors inside a bulk request map to `SERVICE_ERROR`.
- The mocked REST scenario "Bulk resolve with an idempotency conflict within the batch"
  (`test/feature/ers_rest_api/resolve_entity_mention.feature` ~236-248) expects `IDEMPOTENCY_CONFLICT`.
- Documentation (API integration guide) states bulk items carry the same codes as single requests.

## F-4 Decisions can become permanently non-curatable

- Guard: `user_action_service.py` ~45-71 and the atomic claim in `decision_repository.py` ~597-680;
  a second action on the same placement → `AlreadyCuratedError` → HTTP 409.
- Only `_build_update_doc` (`decision_repository.py` ~367-402) resets `reviewed_since_placement`;
  `DecisionStoreService.store_decision` (`decision_store_service.py` ~75-82) returns early when
  `is_same_outcome` holds, so an identical ERE confirmation keeps the flag set.
- The Basic ERE ignores `proposed_cluster_ids` / `excluded_cluster_ids` and answers from stored state.
  Stored scores are float32 in the ERE, so the first re-query may differ by accident and reset the flag;
  later re-queries are identical. Singletons (score 0.0) may block after the first action.
- Failed publish of the re-evaluation request (`decision_curation_service.py` ~81-100) is only logged; the
  flag stays set and no outcome ever arrives.
- UI: the actions stay enabled; clicking returns a generic error toast ("already been curated on its
  current version"); nothing tells the curator the block may be permanent.
- The manual full-cycle notes state that the Basic ERE ignores recommendations; the lifecycle scenarios
  used injected responses with changed candidates, so the identical case was not exercised.
- To analyse: reproduce end to end with the Basic ERE; decide Q-4.

## F-5 Lost ERE responses and misleading log

- Responses are consumed with a blocking pop (`commons/adapters/redis_client.py` ~211).
- On an integration failure the message is logged and dropped
  (`ere_result_integrator/entrypoints/outcome_integration_worker.py` ~104-134); the log text says the
  outcome "may be retried on restart", which nothing does.
- EPIC-05 claims "at-least-once via blocking pop"; the documentation now states no delivery guarantee.
- To analyse: size the loss window; correct the log text and the planning note at minimum.

## F-6 Bulk budget timeout leaves no provisional decision

- `resolution_coordinator_service.py` ~278-291: when the bulk budget is exceeded, pending per-mention
  tasks are cancelled and the whole request fails with 504; provisional decisions already written stay,
  but cancelled mentions get none.
- A late ERE outcome for such a mention is stored as a first insert (no `updated_at`), which refreshBulk
  never exposes; the client has to re-submit to learn it.
- To analyse: confirm; decide whether cancelled mentions should receive a provisional decision.

## F-7 Stale or weak tests and notes

- `test/feature/ers_rest_api/resolve_entity_mention.feature:68` row `req-021` expects replay → PROVISIONAL/202;
  the code returns CANONICAL/200 for replays (intended, commit 9c189e0; e2e `ucb11_resolve_entity_mention.feature`
  row `req-031`). The feature mocks `ResolveService`.
- Same file: header comment ~145 and scenarios ~126-131, ~262-273 expect 500 for an unavailable
  coordinator; the code returns 503 `SERVICE_UNAVAILABLE`.
- `test/feature/ers_rest_api/lookup_cluster_assignment.feature:75` "First bulk lookup for a source returns
  all assignments" contradicts the first-assignment rule; passes only because the service is mocked.
- `single_mention_resolution.feature` ~29-38 "no new request is published to the ERE": the step
  (`test_single_mention_resolution.py` ~451-457) deliberately skips the check; the code republishes when no decision exists.
- Planning notes: EPIC-06 TC-002/TC-003 (budget 0 → ValueError; code: provisional-only mode), EPIC-07
  line 32 (only 200/400/500), EPIC-05 line 63 (at-least-once), `ResolutionTimeoutError` docstring;
  `EnginePublishFailedError` appears unused.

## Open questions — context

- **Q-1** Commit 4ee2b36 (TEDSWS-524 D3) rewrites a decision on any material outcome change so curators see
  "Needs revisit"; neither TEDSWS-524 document considers the refreshBulk effect. ERS1-214 R1 made only a
  placement change count and left scoring to product ("Confirm with product").
- **Q-2** `POST /auth/register` (`curation/entrypoints/api/v1/auth.py` ~19-30) creates unverified accounts;
  they can reach only `/users/me` until an Admin verifies them. The Link Curation UI has no registration
  page. No planning note explains why the endpoint is open.
- **Q-3** `BulkResolveRequest.mentions` has only `min_length=1`; EPIC-06 assumption 5 expected a maximum
  enforced at the API layer (EPIC-07).
- **Q-4** See F-4.

## Related, outside this repository (for the webapp team)

- Link Curation UI texts suggest effects the Basic ERE does not have ("create a new cluster", "The system
  will learn"; `ComparisonPanel.tsx`, `AlternativeClusters.tsx`), and the actions stay enabled on an
  already-curated decision.
