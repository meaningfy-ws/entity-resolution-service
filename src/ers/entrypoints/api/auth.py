from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from ers.application.auth_dtos import UserContext
from ers.application.services import AuthService
from ers.domain.exceptions import AuthorizationError
from ers.entrypoints.api.dependencies import get_auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserContext:
    """Extract and validate JWT from Authorization header."""
    return await auth_service.get_current_user_context(token)


CurrentUser = Annotated[UserContext, Depends(get_current_user)]


def require_verified(user: CurrentUser) -> UserContext:
    """Dependency that enforces the user is verified."""
    if not user.is_verified:
        raise AuthorizationError("Account not verified")
    return user


def require_admin(user: CurrentUser) -> UserContext:
    """Dependency that enforces the user is a superuser."""
    if not user.is_superuser:
        raise AuthorizationError("Admin privileges required")
    return user


VerifiedUser = Annotated[UserContext, Depends(require_verified)]
AdminUser = Annotated[UserContext, Depends(require_admin)]
