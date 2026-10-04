"""Composition root: bind settings, database, services, dependencies, and routers."""

import time
from collections.abc import Callable
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text

from framework_lab.auth_service import AuthService
from framework_lab.database import create_database
from framework_lab.delivery import SmtpDelivery
from framework_lab.document_service import DocumentService
from framework_lab.request_limits import BodyLimit
from framework_lab.routes import auth, documents
from framework_lab.security import JwtPolicy, PolicyError
from framework_lab.settings import LabSettings


def create_app(
    settings: LabSettings | None = None,
    *,
    engine=None,
    email_delivery=None,
    sms_delivery=None,
    clock: Callable[[], float] = time.time,
) -> FastAPI:
    settings = settings or LabSettings.from_env()
    if engine is None:
        engine, sessions = create_database(settings.database_url)
    else:
        from sqlalchemy.orm import sessionmaker

        sessions = sessionmaker(engine, expire_on_commit=False)
    app = FastAPI(title="Owned authentication and document lab", version="0.5.0", debug=False)
    app.state.engine, app.state.sessions, app.state.settings = engine, sessions, settings
    app.state.auth = AuthService(
        settings,
        JwtPolicy(settings, clock),
        email_delivery or SmtpDelivery(settings.smtp_host, settings.smtp_port),
        sms_delivery,
    )
    app.state.documents = DocumentService(settings)
    app.add_middleware(BodyLimit, max_bytes=settings.upload_limit + 8192)

    @app.middleware("http")
    async def correlation(request: Request, call_next):
        request.state.correlation_id = str(uuid4())
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = request.state.correlation_id
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(PolicyError)
    async def policy_error(request: Request, error: PolicyError):
        headers = {"WWW-Authenticate": "Bearer"} if error.status == 401 else {}
        if error.retry_after is not None:
            headers["Retry-After"] = str(error.retry_after)
        return JSONResponse(
            {"error": error.code, "correlation_id": request.state.correlation_id},
            status_code=error.status,
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, _error: RequestValidationError):
        # FastAPI's default errors can include raw input values, including secrets.
        return JSONResponse(
            {"error": "invalid_request", "correlation_id": request.state.correlation_id},
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, _error: Exception):
        correlation_id = getattr(request.state, "correlation_id", str(uuid4()))
        return JSONResponse(
            {"error": "internal_error", "correlation_id": correlation_id},
            status_code=500,
            headers={"X-Correlation-ID": correlation_id, "Cache-Control": "no-store"},
        )

    @app.get("/health", tags=["platform"])
    def health():
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    app.include_router(auth.router)
    app.include_router(documents.router)
    return app
