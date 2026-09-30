# Defect write-up: defect 1

An example of how a defect from this suite is reported. It covers [defect 1](../README.md#defects-found), pinned by the strict xfail `test_current_user_response_hides_sensitive_data`. The evidence is row 7 of `context/schema-validation-report.md`.

---

**Title:** `GET /auth/me` returns the user's password, SSN, EIN, full card details, IBAN and crypto wallet in plain text

| | |
|---|---|
| **Severity** | Critical (security: exposure of credentials and personal/financial data) |
| **Priority** | P1 |
| **Environment** | dev: public DummyJSON instance, `https://dummyjson.com` |
| **Endpoint** | `GET /auth/me` (Bearer-protected) |
| **Found by** | `tests/auth/test_002_current_user.py::TestCurrentUser::test_current_user_response_hides_sensitive_data` |
| **First observed** | 2026-09-27; still reproduces on 2026-09-30 |
| **Reproducibility** | Always (every user, every valid token) |

### Steps to reproduce

1. Log in as any test user to get an access token:

   ```bash
   curl -s -X POST https://dummyjson.com/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username": "<USERNAME>", "password": "<PASSWORD>"}'
   ```

   Take `accessToken` from the response.

2. Call the current-user endpoint with that token:

   ```bash
   curl -s https://dummyjson.com/auth/me \
     -H "Authorization: Bearer <ACCESS_TOKEN>"
   ```

3. Inspect the top-level fields of the JSON body.

### Expected result

`200` with the user's identity and profile only (for example `id`, `username`, `email`, `firstName`, `lastName`, `image`). An identity response never includes the password, in any form, or government IDs, payment card data, bank account numbers or wallet addresses.

### Actual result

`200`, and the body also contains, in plain text:

| Field | What it holds |
|---|---|
| `password` | The user's login password, as they typed it (not a hash) |
| `ssn` | Social Security number |
| `ein` | Employer Identification Number |
| `bank.cardNumber`, `bank.cardExpire` | Full payment card number and its expiry date |
| `bank.iban` | Bank account number (IBAN) |
| `crypto.wallet` | Cryptocurrency wallet address |

(Values withheld from this report; the field names are enough to reproduce.)

### Impact

- Anyone holding a valid access token gets the account's password. A token leaked from logs, a browser or a proxy becomes a permanent account takeover, and a reused password spreads that to other services.
- The body carries enough to support identity theft and payment fraud (SSN, card number with expiry, IBAN).
- It makes the token-handling defects worse: a refresh token is also accepted here (defect 2), for 30 days, so one leaked refresh token exposes all of the above.
- For a real service this would be a reportable data breach (PCI DSS for card data, privacy law for SSNs).

### Suggested fix

Return an explicit allow-list of profile fields from `/auth/me`, never the stored user record. Store passwords only as salted hashes, and never return them, even hashed.

### Notes

DummyJSON is a public sandbox and its users are fictional, so no real person is exposed. The report treats the data as real, because the same behavior in production would be a critical defect. The regression test asserts the correct behavior (the fields are absent) as a strict xfail: the suite stays green, and the test turns red as soon as the API is fixed, so the marker gets removed.
