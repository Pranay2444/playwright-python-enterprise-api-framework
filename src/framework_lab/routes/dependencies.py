from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from framework_lab.security import PolicyError

bearer = HTTPBearer(auto_error=False)


def database(request: Request):
    with request.app.state.sessions() as db:
        yield db


Db = Annotated[Session, Depends(database)]


def identity(
    request: Request,
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise PolicyError(401, "unauthorized")
    return request.app.state.auth.identity(db, credentials.credentials)


Identity = Annotated[tuple, Depends(identity)]
