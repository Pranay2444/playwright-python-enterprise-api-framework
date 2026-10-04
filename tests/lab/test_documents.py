import hashlib
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from playwright.sync_api import sync_playwright
from sqlalchemy import func, select

from api_framework.assertions.openapi import OpenApiResponseError, validate_openapi_response
from api_framework.clients.lab.documents_client import DocumentsClient
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_object
from framework_lab.models import Audit, Document, User

pytestmark = [pytest.mark.lab, pytest.mark.documents, pytest.mark.domain("documents")]


@pytest.mark.database
def test_upload_metadata_download_delete_and_database(lab):
    user, _session, documents = lab.signed_in()
    content = b"Synthetic portfolio document\nNo real personal data.\n"
    response = documents.upload("report.txt", content, str(uuid4()))
    created = json_object(response, 201)
    assert created["size"] == len(content)
    assert created["sha256"] == hashlib.sha256(content).hexdigest()
    assert created["owner_id"] == user["id"]
    assert json_object(documents.metadata(created["id"])) == created
    row = lab.probe.document(created["id"])
    assert row["content"] == content and row["tenant_id"] == user["tenant_id"]
    download = documents.download(created["id"])
    assert download.status == 200 and download.body() == content
    assert download.headers["x-content-sha256"] == created["sha256"]
    assert download.headers["content-disposition"] == 'attachment; filename="report.txt"'
    assert download.headers["cache-control"] == "no-store"
    assert documents.delete(created["id"]).status == 204
    assert documents.metadata(created["id"]).status == 404
    assert documents.download(created["id"]).status == 404
    assert lab.probe.document(created["id"]) is None
    assert {"document_created", "document_deleted"} <= set(lab.probe.audit_events(user["id"]))


@pytest.mark.security
@pytest.mark.parametrize("same_tenant", [False, True])
def test_other_user_cannot_read_download_or_delete(lab, same_tenant):
    owner, _session_a, documents_a = lab.signed_in()
    other, _session_b, documents_b = lab.signed_in()
    if same_tenant:
        with lab.app.state.sessions() as db:
            db.get(User, other["id"]).tenant_id = owner["tenant_id"]
            db.commit()
    created = json_object(documents_a.upload("owned.txt", b"owned", str(uuid4())), 201)
    for operation in (documents_b.metadata, documents_b.download, documents_b.delete):
        assert operation(created["id"]).status == 404
    assert documents_a.download(created["id"]).body() == b"owned"
    assert lab.probe.document(created["id"])["owner_id"] == owner["id"]


@pytest.mark.security
def test_anonymous_documents_are_rejected(lab):
    public = DocumentsClient(lab.api)
    missing = str(uuid4())
    assert public.upload("test.txt", b"x", str(uuid4())).status == 401
    for operation in (public.metadata, public.download, public.delete):
        assert operation(missing).status == 401


@pytest.mark.parametrize(
    "filename",
    ["../escape.txt", "folder/file.txt", "..txt", "report.exe", 'bad"name.txt', "bad\nname.txt"],
)
def test_filename_rejections_do_not_persist(lab, filename):
    _user, _session, documents = lab.signed_in()
    assert documents.upload(filename, b"content", str(uuid4())).status == 422
    with lab.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 0


@pytest.mark.parametrize(
    "content,status",
    [(b"", 413), (b"\xff", 422), (b"a\x00b", 422), (b"x" * 65537, 413), (b"x" * 80000, 413)],
    ids=["empty", "invalid-utf8", "nul", "above-file-limit", "above-body-limit"],
)
def test_size_encoding_and_request_body_rejections(lab, content, status):
    _user, _session, documents = lab.signed_in()
    response = documents.upload("file.txt", content, str(uuid4()))
    assert response.status == status
    assert json_object(response, status)["correlation_id"] == response.headers["x-correlation-id"]


def test_maximum_file_size_and_content_type(lab):
    _user, _session, documents = lab.signed_in()
    assert documents.upload("maximum.txt", b"x" * 65536, str(uuid4())).status == 201
    assert (
        documents.upload("wrong.txt", b"x", str(uuid4()), "application/octet-stream").status == 415
    )
    assert documents.upload("bad-key.txt", b"x", "not-a-uuid").status == 422


@pytest.mark.database
def test_idempotency_exact_replay_and_conflict(lab):
    user, _session, documents = lab.signed_in()
    key = str(uuid4())
    first = json_object(documents.upload("same.txt", b"one", key), 201)
    assert json_object(documents.upload("same.txt", b"one", key), 200) == first
    assert documents.upload("same.txt", b"two", key).status == 409
    assert documents.upload("different.txt", b"one", key).status == 409
    assert lab.probe.document(first["id"])["content"] == b"one"
    assert lab.probe.audit_events(user["id"]).count("document_created") == 1


@pytest.mark.database
def test_concurrent_idempotent_upload_has_one_row(lab):
    user, session, _documents = lab.signed_in()
    key, headers = str(uuid4()), session.headers()

    def send():
        # Playwright's synchronous driver is thread-confined. Each thread owns its driver.
        with sync_playwright() as driver:
            context = driver.request.new_context(base_url=lab.base_url, timeout=10000)
            try:
                response = ApiClient(context).request(
                    "POST",
                    "/documents",
                    headers={
                        **headers,
                        "Idempotency-Key": key,
                    },
                    multipart={
                        "file": {"name": "race.txt", "mimeType": "text/plain", "buffer": b"race"}
                    },
                )
                return response.status, json_object(response, response.status)["id"]
            finally:
                context.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _index: send(), range(2)))
    assert sorted(status for status, _id in results) == [200, 201]
    assert len({document_id for _status, document_id in results}) == 1
    with lab.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Document)) == 1
        assert (
            db.scalar(
                select(func.count())
                .select_from(Audit)
                .where(Audit.user_id == user["id"], Audit.event == "document_created")
            )
            == 1
        )


@pytest.mark.contract
@pytest.mark.domain("contracts")
def test_owned_openapi_and_selected_response_validation(lab):
    spec = json_object(lab.api.get("/openapi.json"))
    assert spec["openapi"].startswith("3.1")
    assert spec["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    user, session, documents = lab.signed_in()
    identity = json_object(lab.auth.me(session.headers()))
    validate_openapi_response(spec, "/auth/me", "get", 200, identity)
    response = documents.upload("schema.txt", b"schema", str(uuid4()))
    body = json_object(response, 201)
    validate_openapi_response(spec, "/documents", "post", 201, body)
    bad = {**body, "size": "private-invalid-input"}
    with pytest.raises(OpenApiResponseError) as failure:
        validate_openapi_response(spec, "/documents", "post", 201, bad)
    assert "private-invalid-input" not in str(failure.value)
    assert identity["id"] == user["id"]
