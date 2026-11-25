# Deployment Information

## Public URL

https://day14-agent-production-439d8b50.up.railway.app

## Platform

Railway — project `day14-production-agent`, environment `production`, service `day14-agent`.

## Live checks (2026-11-26)

| Check | Observed result |
|---|---|
| `GET /health` | HTTP 200 `{"status":"ok"}` |
| `GET /ready` | HTTP 200 `{"ready":true}` |
| `POST /ask` without `X-API-Key` | HTTP 401, as expected |
| `POST /ask` with valid `X-API-Key` | HTTP 200; CP6 completion confirmed by the user |
| Redis credential | Regenerated and service connection restored; CP6 completion confirmed by the user |

## Test commands

```bash
BASE='https://day14-agent-production-439d8b50.up.railway.app'
read -rsp 'Agent API key: ' AGENT_API_KEY; echo
curl -i "$BASE/health"
curl -i "$BASE/ready"
curl -i -X POST "$BASE/ask" \
  -H 'Content-Type: application/json' \
  -H "X-API-Key: $AGENT_API_KEY" \
  -d '{"question":"Hello"}'
```

Expected statuses: `200`, `200`, `200`.

## Environment variables

Set in the Railway service: `AGENT_API_KEY`, `DAILY_BUDGET_USD`, `ENVIRONMENT`, `RATE_LIMIT_PER_MINUTE`, and `REDIS_URL`. Keep values and credentials out of this file and source control. `REDIS_URL` should reference the Redis service variable rather than a copied credential.

## Deployment notes

- Secret values are intentionally omitted from this file and from source control.
- Keep the Railway agent's `REDIS_URL` connected to the Redis service variable reference.
- Capture the latest dashboard and authenticated test output for submission if required.
