import hashlib
import os
from uuid import uuid4

import pytest

from api_framework.auth.lab_session import LabSession
from api_framework.auth.mailpit import MailpitCodeReader
from api_framework.clients.lab.auth_client import LabAuthClient
from api_framework.clients.lab.documents_client import DocumentsClient
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_object

pytestmark = [pytest.mark.lab, pytest.mark.deployment, pytest.mark.domain("framework")]


def test_container_email_mfa_document_flow(playwright, request):
    base_url = request.config.getoption("--lab-base-url")
    mail_url = os.getenv("LAB_MAILPIT_URL", "http://127.0.0.1:8025")
    if not base_url.startswith("http://127.0.0.1:") or not mail_url.startswith("http://127.0.0.1:"):
        pytest.fail("Container smoke tests require owned loopback endpoints")
    context = playwright.request.new_context(base_url=base_url, timeout=8000)
    mail_context = playwright.request.new_context(base_url=mail_url, timeout=3000)
    session = None
    documents = None
    document_id = None
    try:
        api, mail_api = ApiClient(context), ApiClient(mail_context)
        assert json_object(api.get("/health"))["status"] == "ready"
        auth = LabAuthClient(api)
        email, password = f"qa-{uuid4().hex}@example.test", f"Qa!{uuid4().hex}9"
        user = json_object(auth.register(email, password), 201)
        session = LabSession(auth)
        session.authenticate(email, password, MailpitCodeReader(mail_api, email))
        assert json_object(auth.me(session.headers()))["id"] == user["id"]
        documents = DocumentsClient(api, session)
        response = documents.upload("docker.txt", b"Docker SMTP PostgreSQL flow", str(uuid4()))
        body = json_object(response, 201)
        document_id = body["id"]
        downloaded = documents.download(document_id)
        assert hashlib.sha256(downloaded.body()).hexdigest() == body["sha256"]
        assert documents.delete(document_id).status == 204
        assert documents.metadata(document_id).status == 404
        document_id = None
        session.refresh()
        assert auth.me(session.headers()).status == 200
        session.logout()
    finally:
        try:
            if document_id and documents:
                assert documents.delete(document_id).status == 204
            if session and session.state == "authenticated":
                session.logout()
        finally:
            mail_context.dispose()
            context.dispose()
