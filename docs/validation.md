# Phase 1 validation record

Validated on **2026-10-04** in a Linux workspace using Python **3.12.14**.
This record describes local execution, not an executed GitHub Actions run.

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

## Live-service limitation

The live Playwright probe could not obtain an HTTP response from DummyJSON in this
workspace. A separate network attempt also encountered a forbidden response/timeout.
These are execution-environment observations, not confirmed DummyJSON product bugs.
**Real-service compatibility remains pending.** The full live suite was not run.

Run it from a machine with access or through the manually enabled CI live job:

```bash
python -m pytest -m external --run-external --junitxml=reports/live-results.xml
```

Do not change expected statuses or mark live failures as passed to hide the network
limitation. In particular, verify the simulated cart-add `201` expectation during
the first live run.

## Other limits

- The configured CI matrix includes Python 3.11/3.12/3.13; only 3.12 was executed here.
- GitHub Actions configuration is authored, but no remote workflow run is claimed.
- Local responses are a minimal test double, not verified full DummyJSON contracts.
- No JWT cryptographic validation, schema validator, security audit, load test, UI,
  database, MFA, persistent cart, or process-parallel execution is claimed.
