# Troubleshooting

| Symptom | Check | Action |
| --- | --- | --- |
| `ModuleNotFoundError: api_framework` | Active interpreter and editable install | Activate `.venv`; run `python -m pip install --no-deps -e .` |
| Pytest command missing | Interpreter selection | Use `python -m pytest` after installing `requirements-dev.txt` |
| Live tests are skipped | `external` marker opt-in | Run `python -m pytest -m external --run-external` |
| All items are deselected | Marker expression or path | Use `python -m pytest --collect-only -q` to inspect node IDs |
| HTTP 403 or connection timeout on live API | Network/proxy vs actual API response | Compare with local tests; capture safe status details; do not disable TLS |
| Invalid origin/timeout configuration | `.env` and process environment | Fix the validation error; process environment wins over `.env` |
| Login expected 200 but returns another status | Credentials, public service health, current docs | Check published demo credentials; investigate before changing expectations |
| Cart ID cannot be fetched after add | DummyJSON simulated writes | Assert the add response; use a persistent service in a later phase |
| A user's carts are empty | Data assumption | An empty collection is valid; use discovered existing-cart owner for nonempty coverage |
| Refresh JWT matches the prior string | Token issuance timing | Validate authenticated identity; do not require different strings |
| VS Code cannot resolve imports | Selected Python interpreter | Select this project's `.venv` interpreter and reinstall editable package |
| `ContractValidationError` | Named contract, safe schema location, current provider response | Reproduce the smallest case; compare docs/contracts.md before changing rules |
| Pydantic rejects a numeric string or boolean | Strict request/view policy | Fix generated data; keep raw invalid dicts only in negative tests |
| Unknown contract name | Checked-in `$defs` names | Correct the name; this is configuration, not a product defect |
| Missing schema after wheel install | Package data and build artifact | Rebuild with contracts/*.json included; verify the installed resource |

Start a failure investigation with the smallest failing node:

```bash
python -m pytest 'tests/functional/test_auth.py::test_authenticated_user[local]'
python -m pytest 'tests/functional/test_auth.py::test_authenticated_user[live]' --run-external
```

Record local/live target, command, test ID, Python/dependency versions, timestamp,
and status. A proxy denial is not a proven product authorization defect. A local
pass with a live failure narrows the investigation; it does not prove the framework
is correct for every possible service response.

Do not use `--showlocals` on shared reports or paste raw Playwright transport logs
containing headers. The wrapper sanitizes transport errors; use a controlled manual
reproduction if more network evidence is required.
