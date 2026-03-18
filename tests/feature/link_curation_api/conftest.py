"""Shared fixtures for link_curation_api BDD step definitions.

Reuses the same FastAPI dependency-override pattern as tests/curation/api/conftest.py,
but exposed as pytest fixtures for pytest-bdd step functions.

Uses starlette TestClient (sync) because pytest-bdd @scenario creates sync test
functions — async steps/fixtures would return unawaited coroutines.
"""

from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock, create_autospec

import pytest
from fastapi import FastAPI
from pytest_bdd import given
from starlette.testclient import TestClient

from ers.config import Settings
from ers.curation.entrypoints.api.app import create_app
from ers.curation.entrypoints.api.auth import get_current_user
from ers.curation.entrypoints.api.dependencies import (
    get_auth_service,
    get_canonical_entity_service,
    get_decision_curation_service,
    get_entity_service,
    get_statistics_service,
    get_user_action_service,
    get_user_management_service,
)
from ers.curation.services import (
    CanonicalEntityService,
    DecisionCurationService,
    EntityService,
    StatisticsService,
    UserActionService,
)
from ers.users.domain.data_transfer_objects import UserContext
from ers.users.services import AuthService, UserManagementService

ADMIN_USER = UserContext(
    id="admin-user-id",
    email="admin@example.com",
    is_superuser=True,
    is_verified=True,
)

VERIFIED_USER = UserContext(
    id="verified-user-id",
    email="curator@example.com",
    is_superuser=False,
    is_verified=True,
)

UNVERIFIED_USER = UserContext(
    id="unverified-user-id",
    email="unverified@example.com",
    is_superuser=False,
    is_verified=False,
)


@pytest.fixture
def ctx() -> dict[str, Any]:
    """Shared mutable context for passing state between step functions."""
    return {}


@pytest.fixture
def settings() -> Settings:
    return Settings(app_name="Test ERS", debug=True)


@pytest.fixture
def decision_curation_service() -> AsyncMock:
    return create_autospec(DecisionCurationService, instance=True)


@pytest.fixture
def canonical_entity_service() -> AsyncMock:
    return create_autospec(CanonicalEntityService, instance=True)


@pytest.fixture
def entity_service() -> AsyncMock:
    return create_autospec(EntityService, instance=True)


@pytest.fixture
def statistics_service() -> AsyncMock:
    return create_autospec(StatisticsService, instance=True)


@pytest.fixture
def auth_service() -> AsyncMock:
    return create_autospec(AuthService, instance=True)


@pytest.fixture
def user_management_service() -> AsyncMock:
    return create_autospec(UserManagementService, instance=True)


@pytest.fixture
def user_action_service() -> AsyncMock:
    return create_autospec(UserActionService, instance=True)


@pytest.fixture
def app(
    settings: Settings,
    decision_curation_service: AsyncMock,
    canonical_entity_service: AsyncMock,
    entity_service: AsyncMock,
    statistics_service: AsyncMock,
    auth_service: AsyncMock,
    user_action_service: AsyncMock,
    user_management_service: AsyncMock,
) -> FastAPI:
    application = create_app(settings=settings)
    application.dependency_overrides[get_decision_curation_service] = lambda: (
        decision_curation_service
    )
    application.dependency_overrides[get_canonical_entity_service] = lambda: (
        canonical_entity_service
    )
    application.dependency_overrides[get_entity_service] = lambda: entity_service
    application.dependency_overrides[get_statistics_service] = lambda: statistics_service
    application.dependency_overrides[get_auth_service] = lambda: auth_service
    application.dependency_overrides[get_user_action_service] = lambda: user_action_service
    application.dependency_overrides[get_user_management_service] = lambda: user_management_service
    application.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    return application


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as tc:
        yield tc


def make_client_with_user(app: FastAPI, user: UserContext) -> TestClient:
    """Create a test client authenticated as a specific user."""
    app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app)


def make_unauthenticated_client(app: FastAPI) -> TestClient:
    """Create a test client with no authentication."""
    app.dependency_overrides.pop(get_current_user, None)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Shared Background steps
# ---------------------------------------------------------------------------


@given("the curator is authenticated and verified", target_fixture="_auth_done")
def curator_authenticated() -> bool:
    return True
