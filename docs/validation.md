# Phase 1 validation record

Validated on **2026-10-04** in a Linux workspace using Python **3.12.14**.
The local checks below were followed by successful GitHub Actions quality and live API runs.

## Executed checks

| Check | Command | Outcome |
| --- | --- | --- |
| Editable package install | `uv pip install --python .venv/bin/python -e '.[dev]'` | Passed |
| Dependency resolution | `uv pip compile pyproject.toml --extra dev -o requirements-dev.txt` | Passed; exact pins recorded |
| Lint | `ruff check .` | Passed |
| Formatting | `ruff format --check .` | Passed |
| Deterministic suite | `python -m pytest -m "not external" --junitxml=reports/local-results.xml` | **38 passed; 11 live cases deselected** |
| Distribution build | `python -m build` | Wheel and source distribution built successfully |
| One live probe | `python -m pytest 'tests/functional/test_products.py::test_get_products[live]' --run-external -q` | Failed before receiving HTTP response; see limitation below |

The 38 executed checks include 16 unit cases, 11 local HTTP framework cases, and
11 functional scenarios on the local target. The suite has 49 collected cases when
including the 11 opt-in live versions.

Validated dependency versions: Playwright **1.63.0**, Pytest **9.1.1**,
python-dotenv **1.2.4**, and Ruff **0.16.10**. Use `requirements-dev.txt` for all pins.

## GitHub Actions and live-service verification

The separate public repository was created and the complete source was published on `main`.
The first [quality run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37200416290)
passed on Python **3.11, 3.12, and 3.13**. Each quality job ran lint, formatting,
and the 38 deterministic cases.

The explicitly enabled [live verification run](https://github.com/Pranay2444/playwright-python-enterprise-api-framework/actions/runs/37200593976)
also passed all three quality jobs and the `live-dummyjson` job. The live job ran
on Python 3.12 and reported **11 passed; 38 local cases deselected**, including
login, refresh, current-user identity, products/search/pagination, users/carts,
and simulated cart creation. JUnit results were uploaded as workflow artifacts.

These runs validate the Phase 1 source published in commit `3f9148a`.
The later documentation/workflow maintenance change keeps that Python source unchanged
and upgrades the official Actions to exact Node.js 24 release tags:
`checkout@v7.0.1`, `setup-python@v7.0.0`, and `upload-artifact@v7.0.1`.
The push workflow verifies the maintained configuration separately.

### Original workspace limitation

The live Playwright probe could not obtain an HTTP response from DummyJSON in this
workspace. A separate network attempt also encountered a forbidden response/timeout.
These are execution-environment observations, not confirmed DummyJSON product bugs.
The full live suite could not be run from this workspace, but subsequently passed
through GitHub Actions as recorded above. The original local transport failure is
retained here to distinguish environment reachability from service compatibility.

Run it from a machine with access or through the manually enabled CI live job:

```bash
python -m pytest -m external --run-external --junitxml=reports/live-results.xml
```

Do not change expected statuses or mark failures as passed to hide a network
limitation. The simulated cart-add `201` expectation was confirmed in the successful
live run.

## Other limits

- Local execution used Python 3.12; CI additionally verified Python 3.11 and 3.13.
- The live result is a point-in-time compatibility check, not an uptime guarantee.
- Local responses are a minimal test double, not verified full DummyJSON contracts.
- No JWT cryptographic validation, schema validator, security audit, load test, UI,
  database, MFA, persistent cart, or process-parallel execution is claimed.
