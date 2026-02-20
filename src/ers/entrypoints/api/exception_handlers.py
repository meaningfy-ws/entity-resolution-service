from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ers.application.exceptions import ApplicationError, NotFoundError
from ers.domain.exceptions import (
    DomainError,
    InvalidClusterError,
    InvalidStateTransitionError,
)


def register_exception_handlers(app: FastAPI) -> None:
    """Register domain and application exception handlers."""

    @app.exception_handler(NotFoundError)
    async def not_found_handler(
        request: Request,
        exc: NotFoundError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_handler(
        request: Request,
        exc: InvalidStateTransitionError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message},
        )

    @app.exception_handler(InvalidClusterError)
    async def invalid_cluster_handler(
        request: Request,
        exc: InvalidClusterError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": exc.message},
        )

    @app.exception_handler(ApplicationError)
    async def application_error_handler(
        request: Request,
        exc: ApplicationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message},
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(
        request: Request,
        exc: DomainError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"detail": exc.message},
        )
