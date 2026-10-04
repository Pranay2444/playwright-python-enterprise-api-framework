from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, File, Header, Request, Response, UploadFile
from fastapi.responses import JSONResponse

from framework_lab.auth_service import audit
from framework_lab.document_service import document_view
from framework_lab.routes.dependencies import Db, Identity
from framework_lab.schemas import DocumentView, ErrorView

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={code: {"model": ErrorView} for code in (401, 404, 409, 413, 415, 422)},
)


@router.post(
    "", status_code=201, response_model=DocumentView, responses={200: {"model": DocumentView}}
)
def upload(
    request: Request,
    db: Db,
    identity: Identity,
    file: Annotated[UploadFile, File()],
    idempotency_key: Annotated[UUID, Header()],
):
    user, _session = identity
    content = file.file.read(request.app.state.settings.upload_limit + 1)
    try:
        view, created = request.app.state.documents.upload(
            db,
            user,
            file.filename or "",
            file.content_type,
            content,
            str(idempotency_key),
            request.state.correlation_id,
        )
    finally:
        file.file.close()
    return JSONResponse(view, status_code=201 if created else 200)


@router.get("/{document_id}", response_model=DocumentView)
def metadata(document_id: UUID, request: Request, db: Db, identity: Identity):
    user, _session = identity
    return document_view(request.app.state.documents.owned(db, user, str(document_id)))


@router.get(
    "/{document_id}/download",
    responses={
        200: {"content": {"text/plain": {"schema": {"type": "string", "format": "binary"}}}}
    },
)
def download(document_id: UUID, request: Request, db: Db, identity: Identity):
    user, _session = identity
    row = request.app.state.documents.owned(db, user, str(document_id))
    return Response(
        row.content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{row.filename}"',
            "X-Content-SHA256": row.sha256,
        },
    )


@router.delete("/{document_id}", status_code=204)
def delete(document_id: UUID, request: Request, db: Db, identity: Identity):
    user, _session = identity
    row = request.app.state.documents.owned(db, user, str(document_id))
    db.delete(row)
    audit(db, user.id, "document_deleted", request.state.correlation_id)
    db.commit()
    return Response(status_code=204)
