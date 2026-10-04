from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from playwright.sync_api import sync_playwright
from sqlalchemy import func, select

from api_framework.clients.lab.auth_client import LabAuthClient
from api_framework.core.api_client import ApiClient
from api_framework.core.responses import json_object
from framework_lab.models import AuthSession

pytestmark = [
    pytest.mark.lab,
    pytest.mark.auth,
    pytest.mark.database,
    pytest.mark.domain("persistence"),
]


def simultaneous_auth_requests(lab, operation, arguments):
    def send():
        with sync_playwright() as driver:
            context = driver.request.new_context(base_url=lab.base_url, timeout=10000)
            try:
                response = getattr(LabAuthClient(ApiClient(context)), operation)(*arguments)
                return response.status
            finally:
                context.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(lambda _index: send(), range(2)))


def test_one_challenge_can_create_only_one_session(lab):
    user, email, password = lab.register()
    challenge = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    code = lab.code_provider(user, email)(challenge)
    results = simultaneous_auth_requests(lab, "verify", (challenge, code))
    assert sorted(results) == [200, 401]
    with lab.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AuthSession)) == 1


def test_concurrent_refresh_rotates_once_and_detects_reuse(lab):
    _user, session, _documents = lab.signed_in()
    results = simultaneous_auth_requests(lab, "refresh", (session._refresh,))
    assert sorted(results) == [200, 401]
    assert lab.auth.me(session.headers()).status == 401


def test_login_and_verification_share_user_first_lock_order(lab):
    user, email, password = lab.register()
    challenge = json_object(lab.auth.login(email, password), 202)["challenge_id"]
    code = lab.code_provider(user, email)(challenge)
    ready = Barrier(2)

    def send(operation, arguments):
        with sync_playwright() as driver:
            context = driver.request.new_context(base_url=lab.base_url, timeout=10000)
            try:
                ready.wait(timeout=10)
                response = getattr(LabAuthClient(ApiClient(context)), operation)(*arguments)
                return response.status
            finally:
                context.dispose()

    with ThreadPoolExecutor(max_workers=2) as pool:
        login = pool.submit(send, "login", (email, password))
        verify = pool.submit(send, "verify", (challenge, code))
        assert login.result(timeout=20) == 202
        # Either verification wins, or the new login invalidates its old challenge.
        assert verify.result(timeout=20) in {200, 401}
    with lab.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(AuthSession)) <= 1
