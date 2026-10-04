from fastapi import APIRouter, Request, Response

from framework_lab.auth_service import audit
from framework_lab.routes.dependencies import Db, Identity
from framework_lab.schemas import (
    ChallengeView,
    ErrorView,
    Login,
    Refresh,
    Registered,
    Registration,
    Tokens,
    UserView,
    Verification,
)
from framework_lab.security import PolicyError

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={code: {"model": ErrorView} for code in (401, 409, 422, 429, 503)},
)


@router.post("/register", status_code=201, response_model=Registered)
def register(body: Registration, request: Request, db: Db):
    return request.app.state.auth.register(db, body, request.state.correlation_id)


@router.post("/login", status_code=202, response_model=ChallengeView)
def login(body: Login, request: Request, db: Db):
    return request.app.state.auth.login(db, body, request.state.correlation_id)


@router.post("/verify", response_model=Tokens)
def verify(body: Verification, request: Request, db: Db):
    return request.app.state.auth.verify(db, body, request.state.correlation_id)


@router.post("/refresh", response_model=Tokens)
def refresh(body: Refresh, request: Request, db: Db):
    return request.app.state.auth.refresh(db, body, request.state.correlation_id)


@router.get("/me", response_model=UserView)
def me(identity: Identity):
    user, _session = identity
    return {key: getattr(user, key) for key in ("id", "tenant_id", "role", "mfa_method")}


@router.post("/logout", status_code=204)
def logout(request: Request, db: Db, identity: Identity):
    user, session = identity
    session.revoked = True
    audit(db, user.id, "logged_out", request.state.correlation_id)
    db.commit()
    return Response(status_code=204)


@router.get("/admin/audit")
def admin_audit(identity: Identity):
    user, _session = identity
    if user.role != "admin":
        raise PolicyError(403, "forbidden")
    # Demonstrates vertical access policy without exposing other tenants' records.
    return {"role": "admin", "tenant_id": user.tenant_id}
