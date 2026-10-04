import json
import subprocess
import sys

import pytest

from api_framework.reporting.defects import failure_receipt, write_receipt


def test_receipt_redacts_parameters_and_uses_separate_worker_domains(tmp_path):
    secret = "private-token-in-parameter"
    receipt = failure_receipt(
        f"tests/lab/test_authentication.py::test_login[{secret}]", "authentication", "call", 0.15
    )
    a = write_receipt(tmp_path, "a" * 32, "gw0", receipt)
    b = write_receipt(tmp_path, "a" * 32, "gw1", receipt)
    assert a != b and secret not in a.read_text()
    assert json.loads(a.read_text())["rca_status"] == "unknown"


@pytest.mark.parametrize("domain,phase", [("../escape", "call"), ("authentication", "unknown")])
def test_invalid_report_routes_are_rejected(domain, phase):
    with pytest.raises(ValueError):
        failure_receipt("test_case", domain, phase, 0)


def test_real_pytest_reports_setup_call_teardown_without_exception_text(tmp_path):
    source = tmp_path / "test_probe.py"
    source.write_text(
        "import pytest\n"
        '@pytest.fixture\ndef broken_setup():\n    raise RuntimeError("private-setup-credential")\n'
        "@pytest.fixture\ndef broken_teardown():\n    yield\n"
        '    raise RuntimeError("private-teardown-credential")\n'
        "def test_setup(broken_setup):\n    pass\n"
        'def test_call():\n    raise RuntimeError("private-call-credential")\n'
        "def test_teardown(broken_teardown):\n    pass\n"
    )
    reports = tmp_path / "receipts"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "api_framework.reporting.pytest_plugin",
            str(source),
            f"--defect-dir={reports}",
            "-q",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 1
    receipts = [json.loads(path.read_text()) for path in reports.rglob("*.json")]
    assert {receipt["phase"] for receipt in receipts} == {"setup", "call", "teardown"}
    assert all("private-" not in json.dumps(receipt) for receipt in receipts)
