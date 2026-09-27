# DummyJSON API Test Automation

![CI](https://github.com/Anusreepsuresh074/ecommerce-api-automation/actions/workflows/ci.yml/badge.svg)
**[Live test report](https://anusreepsuresh074.github.io/ecommerce-api-automation/)**

A Python + pytest API test automation suite for [DummyJSON](https://dummyjson.com), a public fake e-commerce API with a real **JWT Bearer auth** flow (login → access + refresh token → protected routes → expiry → refresh) and a 194-product catalog with pagination, field selection, sorting, date filtering, search and categories.

**91 tests from 75 reviewed test cases.** They cover the full token lifecycle and the products resource across happy, negative, boundary, auth/authz, contract/schema and error-shape cases, each traced to a business rule. Every response is checked for status, JSON content type and its JSON Schema (strict wherever the docs define the full shape), down to every nested review of every product. Results are reported through [Allure](https://allurereport.org/).

```
77 passed, 14 xfailed in ~80s (parallel, -n auto)  →  https://dummyjson.com (live)
```

## Why this project

This is the companion to my [Restful-Booker suite](https://github.com/Anusreepsuresh074/restful-booker-api-automation). Both repos were built by the **same reusable AI skill workflow** (see [How it was built](#how-it-was-built)), aimed at an API with a very different auth model: JWT with refresh and expiry, instead of a cookie token.

- **The whole Bearer token lifecycle, tested for real.** The suite logs in, decodes the JWT and checks its claims and lifetime, then calls a protected route. It then lets a 1-minute token **actually expire** and confirms `401 "Token Expired!"`. Finally it refreshes and confirms the new token works. Nothing is faked: that one test waits for the token's real `exp` (~65 s, marked `slow`).
- **Security defects found and pinned, not ignored.** The suite found these:
  - `/auth/me` returns the user's **password, SSN, card number, IBAN and crypto wallet**;
  - a **refresh token works as an access token** and the other way round;
  - a **used refresh token keeps working** for 30 days;
  - malformed or forged tokens **crash with 500** instead of returning 401.

  Each is a strict `xfail` test that asserts the *correct* behavior. The suite stays green, and if DummyJSON fixes one, that test turns red so the marker gets removed.
- **Schemas from the docs, required-ness from the data.** There's no OpenAPI spec, so schemas come from the docs' example outputs. Before any field was made required, all 194 products were checked: `brand` exists on only 102 of them, so it's optional.
- **Correct tests for a simulated API.** DummyJSON validates writes and echoes the result, but never saves anything. Every write test therefore reads the product back and asserts the documented **non**-persistence. It does not assert a save that can't happen.
- **No credentials in reports.** One shared redaction module masks passwords, tokens and the `Authorization`/`Cookie` headers in logs, Allure attachments and assertion messages. Allure steps record titles only, never arguments, and tracebacks run in short form. After every run, the reports are scanned for JWTs and the password: 0 found.

## Defects found

| # | What happens | Should be | Test |
|---|---|---|---|
| 1 | `/auth/me` returns password, SSN, EIN, card, IBAN, crypto wallet | not exposed | `test_current_user_response_hides_sensitive_data` |
| 2 | Refresh token accepted as an access token | `401` | `test_refresh_token_cannot_be_used_as_access_token` |
| 3 | Access token accepted as a refresh token | `403` | `test_access_token_cannot_be_used_as_refresh_token` |
| 4 | A used refresh token is accepted again (no rotation) | `403` | `test_used_refresh_token_cannot_be_reused` |
| 5 | Token without the `Bearer ` prefix accepted | `401` | `test_token_without_bearer_prefix_is_rejected` |
| 6 | Malformed token → `500 "invalid token"` | `401` | `test_malformed_token_is_rejected_with_401` |
| 7 | Forged signature → `500 "invalid signature"` | `401` | `test_forged_signature_is_rejected_with_401` |
| 8 | `Authorization: Basic <token>` → `500` | `401` | `test_wrong_auth_scheme_is_rejected_with_401` |
| 9 | `expiresInMins: 43201` → `500` | `400` | `test_login_rejects_lifetime_above_maximum` |
| 10 | `expiresInMins: -1` → `500` with a misleading message | `400` | `test_login_rejects_negative_lifetime` |
| 11 | Add product with an empty body → `201` | `400` | `test_add_product_with_empty_body_is_rejected` |
| 12 | Add product with `price: "free"` → `201` | `400` | `test_add_product_with_wrong_price_type_is_rejected` |
| 13 | `PUT`/`PATCH` return 11 fields; `GET` returns 22 | same shape | `test_update_response_has_same_shape_as_get` |

Full evidence is in `context/schema-validation-report.md`.

## Architecture

A layered structure, so a change to one thing (a field name, an endpoint path) means editing one file:

```
src/
├── config/                # config.yaml loader (+ BASE_URL / TIMEOUT env overrides)
├── constants/endpoints/   # URL paths, as named constants
├── payload/               # pure request-body factories (test data)
├── schema/                # JSON Schema "rulebooks" for valid responses (success + error)
├── helper/                # AuthHelper, ProductHelper — HTTP call + checks, combined
├── utils/                 # logger, JWT decode/tamper, date pivots, redaction, report steps
└── core/
    ├── api_base.py        # the ONE place every HTTP call goes through
    └── assert_helper.py   # the ONE place every assertion goes through
tests/
├── auth/                  # login, current user (Bearer), refresh
├── products/              # list, get, search, categories, add, update/delete, /auth/ routes
└── conftest.py            # session login, bearer_header, helpers
```

No test or helper calls `requests` directly, and no test writes a bare `assert`. Every helper checks the status first, then validates the success schema on 2xx or the standard error schema otherwise. That way a negative test gets its error-shape check for free.

### The Page Object Model, adapted for an API

| POM concept (UI testing) | This project's equivalent |
|---|---|
| A Page Object class per screen | A Helper class per feature: `AuthHelper`, `ProductHelper` |
| Page methods (`login_page.submit()`) | Helper methods (`auth_helper.login(...)`, `product_helper.search_products(...)`) |
| Locators centralized in the page object | Endpoint paths centralized in `src/constants/endpoints/` |
| Tests never call Selenium directly | Tests never call `requests` directly; everything goes through `ApiBase` |
| A `BasePage` with shared driver logic | `ApiBase`, the one class every HTTP call goes through |

Helpers *hold* an `ApiBase` rather than inheriting from it (composition over inheritance).

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt   # runtime deps (pinned) + ruff, pre-commit
pre-commit install                    # lint + format on every commit

cp .env.example .env                  # fill in one of the users published at https://dummyjson.com/users

pytest --env dev -v
```

Subsets:
```bash
pytest -m smoke          # 9 tests, a few seconds: the PR gate
pytest -m regression     # all 91
pytest -m "not slow"     # skip the ~65s real-expiry test
pytest -m auth           # or: -m products
pytest -n auto --dist loadscope
ruff check . && ruff format --check .
```

Allure report from a run:
```bash
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
```

## CI

`.github/workflows/ci.yml`:

- **Lint** (ruff check + format) gates every run.
- **Smoke suite** on every push and PR; **full regression suite** nightly at 02:30 UTC and on demand. Both run in parallel by file, with 2 reruns 5 s apart for network errors only (assertion failures are never retried).
- **JUnit test summary** on each run page, and a failure summary with the breaking schema findings.
- **Run history** (last 20 runs, via `actions/cache`) so flaky tests can be detected across runs.
- **Allure report** with trend history, published to GitHub Pages after every non-PR run.
- **Dependabot** proposes dependency and action updates weekly.

It needs two repository secrets (Settings → Secrets and variables → Actions): `AUTH_USERNAME` and `AUTH_PASSWORD`.

## How it was built

Every file in `src/`, `tests/`, `context/` and the CI config was produced by running my own reusable Claude Code skills (`skills/`, with the agent template in `agents/`), in the agent's fixed order:

| Step | Skill | Output here |
|---|---|---|
| 1 | `create-framework-structure` | The empty layered framework, built one explained phase at a time |
| 2 | `get-context` | `context/api-context.md`: 13 endpoints + the `/auth/` mirror, 28 business rules, each from the docs or a live call |
| 3 | `get-api-auth` | `context/api-auth.md`: the JWT flow, token lifetimes, and how to produce every negative auth state |
| 4 | `api-test-design` | `context/test-case-matrix.md`: 75 cases, **human-reviewed before any code was written** |
| 5 | `pytest-api` | The suite, then a live run + schema validation → `context/schema-validation-report.md` |
| 6 | `teardown` | Skipped: DummyJSON never persists writes, so there is nothing to clean up |
| 7 | `create-report` | `reports/test-report.md` + the Allure HTML report |
| 8 | `ci-integration` | The GitHub Actions pipeline above |

The skills are identical to the ones in the Restful-Booker repo. Only the agent's project config differs. That's the point: one workflow, applied unchanged to a second and very different API.

## What's in this repo

| Path | What it is |
|---|---|
| `context/api-context.md` | Resolved API surface and business rules |
| `context/api-auth.md` | How Bearer JWT auth works here, and every negative-auth state |
| `context/test-case-matrix.md` | The 75-case inventory the suite was generated from |
| `context/schema-validation-report.md` | Findings from running the suite live, including the defects |
| `src/`, `tests/` | The framework and test suite |
| `config/config.yaml` | Environment config (one real environment: the public instance) |
| `skills/`, `agents/` | The reusable AI skill workflow and agent template |
