# Examiner demonstration guide

## 1. Start the application
Install requirements, copy `.env.example` to `.env`, configure the secret and run `uvicorn app.main:app --reload`.

## 2. Demonstrate deterministic triggers
Open `/decoy-lab`.
- `weather_search` should return CLEAN.
- `system_secrets` should return FLAGGED.
- Repeat the same input to show deterministic results.

## 3. Demonstrate CVE request checks
Open `/cve-protection`.
- Leave token blank: expect HTTP 401.
- Enter a wrong token: expect HTTP 403.
- Enter the correct token with an unapproved Host: expect HTTP 400.
- Use the allowed token, Host and Origin: expect HTTP 200.

## 4. Demonstrate the unique evidence ledger
Open `/evidence` and select Verify evidence integrity. The record count should increase after lab actions and the chain should remain VALID.

## 5. Explain the limitations honestly
The CVE page is a local gateway-control prototype. It is not an upstream patch and the demo endpoint is not connected to a live vulnerable server. Explain the network isolation and gateway requirements for a real deployment.
