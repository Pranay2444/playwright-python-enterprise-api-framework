# Phase 3 walkthrough: persistent resources

Phase 1 built shared HTTP/auth foundations. Phase 2 made response rules explicit.
Phase 3 adds a second service with a different auth style and real resource mutations.
Read [the Phase 3 plan](phase-3-test-plan.md) beside the code for expectations and limits.

## Read the code in this order

| Order | File | Question it answers |
| --- | --- | --- |
| 1 | `src/api_framework/config.py` | How do the two service settings share origin rules but keep credentials separate? |
| 2 | `src/api_framework/clients/restful_booker/auth_client.py` | How is a cookie token acquired and kept out of repr/logs? |
| 3 | `src/api_framework/clients/restful_booker/bookings_client.py` | How do endpoint methods reuse generic transport? |
| 4 | `src/api_framework/data/booking_factory.py` | How are synthetic markers and valid dates generated? |
| 5 | `src/api_framework/contracts/restful_booker.json` | How do booking objects differ from ID-array responses? |
| 6 | `tests/support/booking_lifecycle.py` | Why is the ID tracked before assertions and ownership checked before delete? |
| 7 | `tests/booker/conftest.py` | What setup/teardown order keeps cleanup clients alive? |
| 8 | `tests/booker/test_bookings.py` | How do GET calls prove PUT/PATCH persistence? |
| 9 | `tests/local/test_booking_cleanup.py` | What happens when assertions, schemas, or deletion fail? |

## Setup and selection

Update your local checkout and install the project as shown in the root README.
The same dependencies support this phase; no browser download is needed. If an
existing `.env` lacks Booker settings, the documented public-demo defaults apply.
You can add the `BOOKER_*` lines from `.env.example`; do not overwrite private settings.

```bash
python -m pip install -r requirements-dev.txt
python -m pip install --no-deps -e .
python -m pytest -m "booker and not external"
python -m pytest tests/local/test_booking_cleanup.py
```

To contact the real shared demo explicitly:

```bash
python -m pytest -m "booker and external" --run-external
```

`-m external --run-external` now selects both services. To retain the older
DummyJSON-only selection, use `-m "external and not booker" --run-external`.
Each CI live service has a separate input/job/report, so one outage does not hide
which service failed. A live test is not run automatically on a PR.

## Why not reuse TokenManager?

DummyJSON has obtain/refresh operations and Bearer injection. Booker returns a token
used as `Cookie: token=...` for writes, with no refresh endpoint. Reusing the HTTP
client is useful; forcing this session into the refresh protocol would invent a
service capability. `BookerSession` stores the token in memory per test, validates
that it cannot inject another cookie/header, and hides it in repr. Reading a token
contract does not validate a JWT signature or prove RBAC.

`booker_auth` logs in on its own context. `bookings` is public, while
`authenticated_bookings` attaches the session header only to mutations. Both send
requests on the separate Booker business context. Anonymous rejection tests call
the public API without receiving the session header or a login-cookie jar.

## Fixture lifecycle

Pytest resolves `booking_tracker` dependencies first: target settings, request
contexts, clients, and a valid cookie session. Only then can a test call `create`.
The context-manager fixture yields the tracker to the test. When the test finishes,
Pytest resumes the fixture and runs cleanup before destroying its dependencies.
This order keeps GET/DELETE available even when an assertion fails.

```python
owned = booking_tracker.create(booking_payload())
changes = {"firstname": "Patched", "additionalneeds": "Late checkout"}
expected = {**owned.payload, **changes}
response = authenticated_bookings.patch(owned.booking_id, changes)
assert_booking(response, expected)
assert_booking(bookings.get(owned.booking_id), expected)
```

The client returns the PATCH response; the first assertion validates it. The second
GET proves the state actually changed rather than merely being echoed. The unique
lastname remains intact for cleanup. The test sends synthetic data, not a personal
name/address, and never chooses a seed booking ID.

## Creation registration and cleanup

Do not put registration after `contract_json`: a response could contain a usable
ID but violate the booking schema. The tracker parses the ID first, registers it,
then checks status/schema. A loopback regression removes a required field from
creation and later GET responses; cleanup still uses the intact ownership marker
and deletes that resource while the original contract failure remains visible.

Cleanup checks only the JSON envelope and marker, so an unrelated schema defect
does not block deletion of a provably owned record. Changed markers stop deletion.
After a successful DELETE, GET must return 404. A test that already deleted the
record gets an absence check, not a second DELETE. Failures on one ID do not stop
attempts for other IDs, and failed cleanup is reported separately from test results.

The tracker is test support, not a production resource manager. It cannot clean up
an unidentified creation, survive forced process termination, make shared-demo
operations atomic, or compensate for arbitrary connectivity/auth failures. Read
the plan's cleanup limitations before extending it.

## Full replacement versus partial change

The lifecycle sends a full PUT body with modified name, price, deposit flag, needs,
and dates, followed by GET comparison. PATCH sends only the intended changed fields;
the result and later GET are compared with original fields plus those changes.
The separate PATCH boundary case proves that zero and false are retained. Avoid
truthiness-based merge code that accidentally drops these values.

The simple local model treats PUT as replacement and PATCH as a top-level merge.
Provider implementation details can differ for omitted fields or nested PATCH data;
this phase does not claim to test every replacement/deep-merge rule.

## Debugging and practice

```bash
python -m pytest 'tests/booker/test_bookings.py::test_complete_booking_lifecycle[local]'
python -m pytest 'tests/booker/test_bookings.py::test_complete_booking_lifecycle[live]' --run-external
```

Use the smallest failing node and safe method/path/status logs. Separate a business
failure from a teardown error. Do not paste cookie values or enable `--showlocals`
in shared artifacts. The demo reset is a possible data cause to investigate; do
not label it confirmed without evidence or hide it with retry loops.

Practice:

1. Trace fixture teardown and explain why contexts remain usable during cleanup.
2. Run the changed-marker regression and explain why deleting that ID is withheld.
3. Add a non-sensitive PATCH field change while retaining the unique marker.
4. Inject a delete failure for the first of two loopback resources; inspect why the
   second is still removed and the first remains reported.
5. Explain how an owned API could use resource versions/conditional deletes to
   reduce the public demo's GET-then-DELETE race.

## Interview explanation

“I extended the same transport and contract engine to Restful Booker while keeping
cookie auth and target fixtures separate from DummyJSON. The lifecycle creates
its own booking, proves PUT/PATCH persistence with independent GET calls, and
verifies deletion. I register IDs before assertions and test cleanup under injected
failures. Ownership markers prevent obvious ID reuse mistakes, while shared-demo
resets and non-atomic cleanup remain explicit limitations.”
