"""Opt-in, xdist-safe pytest receipts. Never copy tracebacks, bodies, or exception strings."""

from pathlib import Path
from uuid import uuid4

import pytest

from api_framework.reporting.defects import DOMAINS, failure_receipt, write_receipt


def pytest_addoption(parser):
    parser.addoption("--defect-dir", default=None, help="Write allowlisted domain failure receipts")


def pytest_configure(config):
    config._defect_run_id = uuid4().hex


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    result = yield
    report = result.get_result()
    folder = item.config.getoption("--defect-dir")
    if not folder or not report.failed:
        return
    marker = item.get_closest_marker("domain")
    domain = marker.args[0] if marker and marker.args else "framework"
    if domain not in DOMAINS:
        domain = "framework"
    worker = getattr(item.config, "workerinput", {}).get("workerid", "main")
    receipt = failure_receipt(report.nodeid, domain, report.when, report.duration)
    write_receipt(Path(folder), item.config._defect_run_id, worker, receipt)
