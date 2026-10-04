from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, Playwright

from api_framework.clients.reqres.demo_users_client import DemoUsersClient
from api_framework.clients.reqres.records_client import RecordsClient
from api_framework.config import ReqResSettings
from api_framework.core.api_client import ApiClient
from tests.conftest import PROJECT_ROOT, create_context
from tests.support.record_lifecycle import RecordTracker


def target_settings(request: pytest.FixtureRequest) -> ReqResSettings:
    if request.param == "local":
        server = request.getfixturevalue("local_reqres")
        return ReqResSettings(
            base_url=server.base_url, api_key="local-manage-key", project_id="local-project"
        )
    return ReqResSettings.from_env(PROJECT_ROOT / ".env")


@pytest.fixture(params=["local", pytest.param("live", marks=pytest.mark.external)])
def reqres_demo_settings(request: pytest.FixtureRequest) -> ReqResSettings:
    return target_settings(request)


@pytest.fixture(params=["local", pytest.param("live", marks=pytest.mark.external)])
def reqres_project_settings(request: pytest.FixtureRequest) -> ReqResSettings:
    settings = target_settings(request)
    settings.require_project()  # Missing live credentials fail before making requests.
    return settings


@pytest.fixture
def demo_users(
    playwright: Playwright, reqres_demo_settings: ReqResSettings
) -> Iterator[DemoUsersClient]:
    context = create_context(playwright, reqres_demo_settings)
    try:
        yield DemoUsersClient(ApiClient(context))
    finally:
        context.dispose()


@pytest.fixture
def reqres_project_context(
    playwright: Playwright, reqres_project_settings: ReqResSettings
) -> Iterator[APIRequestContext]:
    context = create_context(playwright, reqres_project_settings)
    try:
        yield context
    finally:
        context.dispose()


@pytest.fixture
def reqres_project_api(reqres_project_context: APIRequestContext) -> ApiClient:
    # No default key/cookies: the RecordsClient sends its API key per request.
    return ApiClient(reqres_project_context)


@pytest.fixture
def records(
    reqres_project_api: ApiClient, reqres_project_settings: ReqResSettings
) -> RecordsClient:
    return RecordsClient(reqres_project_api, reqres_project_settings)


@pytest.fixture
def record_tracker(records: RecordsClient) -> Iterator[RecordTracker]:
    with RecordTracker(records) as tracker:
        yield tracker
