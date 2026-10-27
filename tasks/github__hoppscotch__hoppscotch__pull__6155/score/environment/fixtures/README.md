# Local Hoppscotch fixtures

The source-built self-host services use Hoppscotch's official ports: Web at
`http://localhost:3000`, Admin at `http://localhost:3100`, and Backend at
`http://localhost:3170`. PostgreSQL is `hoppscotch-db:5432` with the upstream
example database and credentials. Mailpit receives EMAIL-provider magic links
at `hoppscotch-mailpit:1025`; its API is
`http://hoppscotch-mailpit:8025`.

## Echo service

The environment provides an immutable HTTP echo service for deterministic Web
request and response interactions. From the main container and its Chromium
browser, use `http://echo:8080`; the same value is available as
`ECHO_BASE_URL`. Do not depend on the public `https://echo.hoppscotch.io` during
reproduction or replay.

All ordinary paths accept `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, `OPTIONS`,
and `HEAD`, return status 200, and produce the following JSON shape:

```json
{
  "method": "POST",
  "args": { "tag": "one, two" },
  "data": "{\"name\":\"Alice\"}",
  "headers": { "content-type": "application/json" },
  "path": "/api/users",
  "isBase64Encoded": false
}
```

Repeated query values are joined with `, `, matching the public service's
observable behavior. Text request bodies remain strings. Non-UTF-8 bodies are
returned as base64 with `isBase64Encoded: true`. The body limit is 1 MiB. CORS
preflights reflect requested header names so the Web client can exercise custom
headers without an external proxy.

Environment fixture controls live under a reserved namespace and are not presented
as behavior of the public Hoppscotch service:

- `ANY /__fixture/status/:code` returns the requested status from 200 through
  599 with the normal echo body. Statuses 204 and 304 have no response body.
- `ANY /__fixture/delay/:milliseconds` delays a normal 200 response by at most
  5000 milliseconds.
- `GET /healthz` returns plain-text `ok` for Compose health checks.

The service is stateless. Reproduction `setup.sh` and `cleanup.sh` should not
start, stop, or modify it; select the required behavior through the request URL.
