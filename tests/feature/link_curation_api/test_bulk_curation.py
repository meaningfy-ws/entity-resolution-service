"""Step definitions for bulk_curation.feature.

Tests the POST bulk-accept and bulk-reject endpoints through the FastAPI test
client with mocked DecisionCurationService.
"""

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

from pytest_bdd import given, parsers, scenario, then, when
from starlette.testclient import TestClient

from ers.curation.domain.data_transfer_objects import (
    BulkActionResponse,
    BulkItemResult,
    BulkItemStatus,
)

FEATURE = str(Path(__file__).resolve().parent / "bulk_curation.feature")

DECISIONS_URL = "/api/v1/curation/decisions"

STATUS_MAP = {
    "success": "success",
    "not found": "not_found",
    "already curated": "already_curated",
    "error": "error",
}


# ---------------------------------------------------------------------------
# Scenario bindings
# ---------------------------------------------------------------------------


@scenario(FEATURE, "Bulk accept multiple decisions successfully")
def test_bulk_accept_all():
    pass


@scenario(FEATURE, "Bulk accept with partial failures")
def test_bulk_accept_partial():
    pass


@scenario(FEATURE, "Bulk accept with already curated decisions")
def test_bulk_accept_already_curated():
    pass


@scenario(FEATURE, "Bulk reject multiple decisions successfully")
def test_bulk_reject_all():
    pass


@scenario(FEATURE, "Bulk reject with mixed outcomes")
def test_bulk_reject_mixed():
    pass


@scenario(FEATURE, "Bulk operation with empty decision list is rejected")
def test_bulk_empty_rejected():
    pass


@scenario(FEATURE, "Bulk operation respects maximum batch size")
def test_bulk_max_size():
    pass


# ---------------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------------


@given(parsers.parse("{count:d} decisions exist that have not been curated"))
def n_uncurated_decisions(ctx: dict[str, Any], count: int) -> None:
    ctx.setdefault("decision_ids", []).extend(f"d-{i}" for i in range(count))
    ctx.setdefault("expected_success", 0)
    ctx["expected_success"] += count


@given(parsers.parse("{count:d} decision does not exist"))
def n_missing_decisions_singular(ctx: dict[str, Any], count: int) -> None:
    ctx.setdefault("decision_ids", []).extend(f"missing-{i}" for i in range(count))
    ctx.setdefault("expected_not_found", 0)
    ctx["expected_not_found"] += count


@given(
    parsers.parse("{count:d} decision has already been curated on its current version"),
)
def n_already_curated_singular(ctx: dict[str, Any], count: int) -> None:
    ctx.setdefault("decision_ids", []).extend(f"curated-{i}" for i in range(count))
    ctx.setdefault("expected_already_curated", 0)
    ctx["expected_already_curated"] += count


@given(parsers.parse("{count:d} decision has not been curated"))
def n_not_curated_singular(ctx: dict[str, Any], count: int) -> None:
    ctx.setdefault("decision_ids", []).extend(f"d-fresh-{i}" for i in range(count))
    ctx.setdefault("expected_success", 0)
    ctx["expected_success"] += count


@given(parsers.parse("{count:d} decision has already been curated"))
def n_already_curated_no_version(ctx: dict[str, Any], count: int) -> None:
    ctx.setdefault("decision_ids", []).extend(f"curated-x-{i}" for i in range(count))
    ctx.setdefault("expected_already_curated", 0)
    ctx["expected_already_curated"] += count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_bulk_response(ctx: dict[str, Any]) -> BulkActionResponse:
    results: list[BulkItemResult] = []
    for did in ctx.get("decision_ids", []):
        if did.startswith("missing"):
            results.append(BulkItemResult(decision_id=did, status=BulkItemStatus.NOT_FOUND))
        elif did.startswith("curated"):
            results.append(
                BulkItemResult(decision_id=did, status=BulkItemStatus.ALREADY_CURATED),
            )
        else:
            results.append(BulkItemResult(decision_id=did, status=BulkItemStatus.SUCCESS))
    return BulkActionResponse(results=results)


# ---------------------------------------------------------------------------
# When
# ---------------------------------------------------------------------------


@when(
    parsers.parse("the curator bulk-accepts all {count:d} decisions"),
    target_fixture="response",
)
def bulk_accept_n(
    client: TestClient,
    ctx: dict[str, Any],
    count: int,
    decision_curation_service: AsyncMock,
) -> Any:
    decision_curation_service.bulk_accept_decisions.return_value = _build_bulk_response(ctx)
    return client.post(
        f"{DECISIONS_URL}/bulk-accept",
        json={"decision_ids": ctx["decision_ids"]},
    )


@when(
    parsers.parse("the curator bulk-accepts all {count:d} decision identifiers"),
    target_fixture="response",
)
def bulk_accept_ids(
    client: TestClient,
    ctx: dict[str, Any],
    count: int,
    decision_curation_service: AsyncMock,
) -> Any:
    decision_curation_service.bulk_accept_decisions.return_value = _build_bulk_response(ctx)
    return client.post(
        f"{DECISIONS_URL}/bulk-accept",
        json={"decision_ids": ctx["decision_ids"]},
    )


@when("the curator bulk-accepts both decisions", target_fixture="response")
def bulk_accept_both(
    client: TestClient,
    ctx: dict[str, Any],
    decision_curation_service: AsyncMock,
) -> Any:
    decision_curation_service.bulk_accept_decisions.return_value = _build_bulk_response(ctx)
    return client.post(
        f"{DECISIONS_URL}/bulk-accept",
        json={"decision_ids": ctx["decision_ids"]},
    )


@when(
    parsers.parse("the curator bulk-rejects all {count:d} decisions"),
    target_fixture="response",
)
def bulk_reject_n(
    client: TestClient,
    ctx: dict[str, Any],
    count: int,
    decision_curation_service: AsyncMock,
) -> Any:
    decision_curation_service.bulk_reject_decisions.return_value = _build_bulk_response(ctx)
    return client.post(
        f"{DECISIONS_URL}/bulk-reject",
        json={"decision_ids": ctx["decision_ids"]},
    )


@when(
    parsers.parse("the curator bulk-rejects all {count:d} decision identifiers"),
    target_fixture="response",
)
def bulk_reject_ids(
    client: TestClient,
    ctx: dict[str, Any],
    count: int,
    decision_curation_service: AsyncMock,
) -> Any:
    decision_curation_service.bulk_reject_decisions.return_value = _build_bulk_response(ctx)
    return client.post(
        f"{DECISIONS_URL}/bulk-reject",
        json={"decision_ids": ctx["decision_ids"]},
    )


@when(
    "the curator submits a bulk accept with no decision identifiers",
    target_fixture="response",
)
def bulk_accept_empty(client: TestClient) -> Any:
    return client.post(
        f"{DECISIONS_URL}/bulk-accept",
        json={"decision_ids": []},
    )


@when(
    parsers.parse(
        "the curator submits a bulk accept with more than {limit:d} decision identifiers"
    ),
    target_fixture="response",
)
def bulk_accept_over_limit(client: TestClient, limit: int) -> Any:
    ids = [f"d-{i}" for i in range(limit + 1)]
    return client.post(
        f"{DECISIONS_URL}/bulk-accept",
        json={"decision_ids": ids},
    )


# ---------------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------------


@then(parsers.parse('the response contains {count:d} results all with status "{status}"'))
def all_results_with_status(response: Any, count: int, status: str) -> None:
    api_status = STATUS_MAP.get(status, status)
    assert response.status_code == 200
    results = response.json()["results"]
    assert len(results) == count
    assert all(r["status"] == api_status for r in results)


@then(parsers.parse('the response contains {count:d} results with status "{status}"'))
def contains_n_results_with_status(response: Any, count: int, status: str) -> None:
    api_status = STATUS_MAP.get(status, status)
    results = response.json()["results"]
    matching = [r for r in results if r["status"] == api_status]
    assert len(matching) == count


@then(parsers.parse('the response contains {count:d} result with status "{status}"'))
def contains_one_result_with_status(response: Any, count: int, status: str) -> None:
    api_status = STATUS_MAP.get(status, status)
    results = response.json()["results"]
    matching = [r for r in results if r["status"] == api_status]
    assert len(matching) == count


@then(parsers.parse('{count:d} result with status "{status}"'))
def n_results_with_status(response: Any, count: int, status: str) -> None:
    api_status = STATUS_MAP.get(status, status)
    results = response.json()["results"]
    matching = [r for r in results if r["status"] == api_status]
    assert len(matching) == count


@then(parsers.parse('{count:d} results with status "{status}"'))
def n_results_with_status_plural(response: Any, count: int, status: str) -> None:
    api_status = STATUS_MAP.get(status, status)
    results = response.json()["results"]
    matching = [r for r in results if r["status"] == api_status]
    assert len(matching) == count


@then("the request is rejected as invalid")
def request_rejected(response: Any) -> None:
    assert response.status_code == 422
