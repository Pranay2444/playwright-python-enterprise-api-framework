import os
import secrets
from dataclasses import dataclass
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateSchema, DropSchema

from api_framework.auth.lab_session import LabSession
from api_framework.auth.mailpit import MailpitCodeReader
from api_framework.clients.lab.auth_client import LabAuthClient
from api_framework.clients.lab.documents_client import DocumentsClient
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_object
from framework_lab.app import create_app
from framework_lab.database import DatabaseProbe, create_database
from framework_lab.delivery import CapturedDelivery
from framework_lab.models import Base
from framework_lab.settings import LabSettings
from tests.support.lab_server import LabServer


class ControlledClock:
    def __init__(self):
        self.now = 1_800_000_010

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


@dataclass(repr=False)
class LabHarness:
    app: object
    api: ApiClient
    auth: LabAuthClient
    probe: DatabaseProbe
    clock: ControlledClock
    email_delivery: object
    sms_delivery: CapturedDelivery
    mail_api: ApiClient | None
    base_url: str

    def register(self, method="email"):
        email, password = f"qa-{uuid4().hex}@example.test", f"Qa!{uuid4().hex}9"
        user = json_object(self.auth.register(email, password, method), 201)
        return user, email, password

    def code_provider(self, user, email):
        if user["mfa_method"] == "totp":
            import pyotp

            return lambda _challenge: pyotp.TOTP(user["totp_secret"]).at(self.clock())
        if user["mfa_method"] == "sms":
            return lambda challenge: self.sms_delivery.code_for(email, challenge)
        if self.mail_api is not None:
            return MailpitCodeReader(self.mail_api, email)
        return lambda challenge: self.email_delivery.code_for(email, challenge)

    def signed_in(self, method="email"):
        user, email, password = self.register(method)
        session = LabSession(self.auth, clock=self.clock)
        session.authenticate(email, password, self.code_provider(user, email))
        return user, session, DocumentsClient(self.api, session)


@pytest.fixture
def lab_database(request, tmp_path):
    postgres = request.config.getoption("--lab-postgres")
    admin = None
    schema = None
    if postgres:
        url = os.getenv("LAB_TEST_DATABASE_URL", "")
        if not url.startswith("postgresql+psycopg://"):
            pytest.fail(
                "--lab-postgres requires LAB_TEST_DATABASE_URL for an owned disposable database"
            )
        admin = create_engine(url, hide_parameters=True)
        schema = f"lab_test_{uuid4().hex}"
        engine = admin.execution_options(schema_translate_map={None: schema})
    else:
        url = "sqlite:///" + str(tmp_path / "lab.db")
        engine, _sessions = create_database(url)
    created_schema = False
    try:
        if admin is not None:
            with admin.begin() as connection:
                connection.execute(CreateSchema(schema))
            created_schema = True
            Base.metadata.create_all(engine)
        yield url, engine
    finally:
        try:
            if admin is not None and created_schema:
                with admin.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
        finally:
            (admin if admin is not None else engine).dispose()


@pytest.fixture
def lab(request, lab_database, playwright):
    url, engine = lab_database
    use_mailpit = request.config.getoption("--lab-mailpit")
    clock, email_delivery, sms_delivery = ControlledClock(), CapturedDelivery(), CapturedDelivery()
    settings = LabSettings(
        url,
        secrets.token_urlsafe(48),
        smtp_host=os.getenv("LAB_SMTP_HOST", "127.0.0.1"),
        smtp_port=int(os.getenv("LAB_SMTP_PORT", "1025")),
    )
    app = create_app(
        settings,
        engine=engine,
        clock=clock,
        email_delivery=None if use_mailpit else email_delivery,
        sms_delivery=sms_delivery,
    )
    mail_context = None
    try:
        if use_mailpit:
            mail_url = os.getenv("LAB_MAILPIT_URL", "http://127.0.0.1:8025")
            if not mail_url.startswith("http://127.0.0.1:"):
                pytest.fail("Use a loopback Mailpit endpoint in the owned test environment")
            mail_context = playwright.request.new_context(base_url=mail_url, timeout=3000)
        with LabServer(app) as server:
            context = playwright.request.new_context(base_url=server.base_url, timeout=5000)
            try:
                api = ApiClient(context)
                yield LabHarness(
                    app,
                    api,
                    LabAuthClient(api),
                    DatabaseProbe(engine),
                    clock,
                    email_delivery,
                    sms_delivery,
                    ApiClient(mail_context) if mail_context else None,
                    server.base_url,
                )
            finally:
                context.dispose()
    finally:
        if mail_context:
            mail_context.dispose()
