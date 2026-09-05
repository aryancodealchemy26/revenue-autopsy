"""Centralized Application and Domain Error Handling."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors import (
    ActionNotApprovedError,
    AIProviderUnavailableWorkflowError,
    ApplicationError,
    DuplicateExecutionError,
    DuplicateOutcomeError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    InvestigationWorkflowError,
    InvestigationWorkflowFailedError,
    TenantMismatchError,
)

logger = logging.getLogger("revenue_autopsy.errors")


def register_exception_handlers(app: FastAPI) -> None:
    """Register centralized custom exception handlers for the FastAPI application."""

    @app.exception_handler(AIProviderUnavailableWorkflowError)
    async def ai_unavailable_handler(request: Request, exc: AIProviderUnavailableWorkflowError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": 503,
                    "type": exc.__class__.__name__,
                    "message": "AI investigation service is temporarily unavailable. Please retry shortly.",
                }
            },
        )

    @app.exception_handler(InvestigationWorkflowFailedError)
    async def investigation_failed_handler(request: Request, exc: InvestigationWorkflowFailedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content={
                "error": {
                    "code": 502,
                    "type": exc.__class__.__name__,
                    "message": "Investigation workflow failed to produce a valid diagnosis.",
                }
            },
        )

    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": 404,
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(TenantMismatchError)
    async def tenant_mismatch_handler(request: Request, exc: TenantMismatchError) -> JSONResponse:
        # Safe 404 response without leaking foreign merchant resources
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": 404,
                    "type": "ResourceNotFoundError",
                    "message": "The requested resource was not found in the current tenant context.",
                }
            },
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_transition_handler(request: Request, exc: InvalidStateTransitionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": 409,
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(ActionNotApprovedError)
    async def action_not_approved_handler(request: Request, exc: ActionNotApprovedError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": 400,
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(DuplicateExecutionError)
    async def duplicate_execution_handler(request: Request, exc: DuplicateExecutionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": 409,
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(DuplicateOutcomeError)
    async def duplicate_outcome_handler(request: Request, exc: DuplicateOutcomeError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "error": {
                    "code": 409,
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.status_code,
                    "message": exc.detail,
                }
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": 422,
                    "message": "Validation error",
                    "details": exc.errors(),
                }
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("Unhandled server error: %s - %s", exc.__class__.__name__, str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": 500,
                    "message": "Internal server error",
                }
            },
        )
