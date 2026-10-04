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
    public_suite = any(
        part in {"functional", "contract", "contracts", "negative", "boundary", "booker", "reqres"}
        for part in item.path.parts
    )
    domain = (
        marker.args[0]
        if marker and marker.args
        else ("public-apis" if public_suite else "framework")
    )
    if domain not in DOMAINS:
        domain = "framework"
    worker = getattr(item.config, "workerinput", {}).get("workerid", "main")
    if item.get_closest_marker("lab"):
        service = "lab"
        target = (
            "container"
            if item.get_closest_marker("deployment")
            else (
                "postgres" if item.config.getoption("--lab-postgres", default=False) else "sqlite"
            )
        )
    elif public_suite:
        service = (
            "booker"
            if item.get_closest_marker("booker")
            else ("reqres" if item.get_closest_marker("reqres") else "dummyjson")
        )
        target = "public-api" if item.get_closest_marker("external") else "local-http"
    else:
        service, target = "framework", "local-check"
    receipt = failure_receipt(report.nodeid, domain, report.when, report.duration, service, target)
    try:
        write_receipt(Path(folder), item.config._defect_run_id, worker, receipt)
    except (OSError, ValueError):
        report.sections.append(
            (
                "Defect receipt unavailable",
                "Could not write the domain receipt; check the report directory",
            )
        )
