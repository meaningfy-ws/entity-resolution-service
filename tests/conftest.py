import pytest

# TODO: replace with actual package imports once released
from ere.models.core import ClusterReference
from ere.models.ers import DecisionStatus
from ers.domain.models import CurationDecision
from tests.factories import (
    ClusterReferenceFactory,
    CurationDecisionFactory,
)


@pytest.fixture
def cluster_reference() -> ClusterReference:
    return ClusterReferenceFactory.build()


@pytest.fixture
def pending_decision() -> CurationDecision:
    return CurationDecisionFactory.build(status=DecisionStatus.PENDING_MANUAL_REVIEW)


@pytest.fixture
def pending_decision_with_candidates() -> CurationDecision:
    candidates = [
        ClusterReferenceFactory.build(confidenceScore=0.9),
        ClusterReferenceFactory.build(confidenceScore=0.7),
        ClusterReferenceFactory.build(confidenceScore=0.5),
    ]
    return CurationDecisionFactory.build(
        status=DecisionStatus.PENDING_MANUAL_REVIEW,
        candidates=candidates,
    )


@pytest.fixture
def reviewed_decision() -> CurationDecision:
    return CurationDecisionFactory.build(status=DecisionStatus.MANUALLY_REVIEWED)


@pytest.fixture
def auto_confident_decision() -> CurationDecision:
    return CurationDecisionFactory.build(status=DecisionStatus.AUTOMATIC_CONFIDENT)
