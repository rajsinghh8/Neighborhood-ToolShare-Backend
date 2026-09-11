COMMIT_MESSAGE: Reconfigure server port/DB/JWT defaults for target environment and add full API test suite

## Features Added

The project already implemented the full requested feature set (User, Tool, BorrowRequest,
Reservation, Review, Notification entities; tool listing; borrow request lifecycle;
reservations; return tracking; two-way reviews/ratings; notifications; admin monitoring;
JWT auth; user data isolation; tool availability/stock rules; overdue detection). This run
focused on adapting the existing implementation to the target deployment environment and
verifying it end-to-end:

- Re-pointed the app to the target server port (25084) and resolved PostgreSQL database,
  making both overridable via environment variables with safe local defaults.
- Externalized the JWT signing secret behind a proper `jwt.secret` property (was previously
  read directly from a raw `JWT_SECRET` env var with no default, which would fail to start
  in this environment).
- Updated JWT expiry to 60 minutes per the target auth configuration (was 30 minutes).
- Added a comprehensive curl-based end-to-end test suite exercising every documented
  endpoint (auth, users, tools, borrow-requests, reservations, reviews, notifications,
  admin, health).

No new entities, endpoints, or business rules were added since the existing project already
fully covers every item in the requested feature list (tool listing, borrow requests,
reservations, return tracking, two-way reviews/ratings, notifications, admin monitoring,
JWT auth, user isolation, availability/stock rules, overdue detection via a scheduled job).

## Files Modified

- `src/main/resources/application.properties` — `server.port` now `${SERVER_PORT:25084}`;
  `spring.datasource.url/username/password` now default to the resolved local PostgreSQL
  database (`jdbc:postgresql://localhost:5432/gen_9bb072199192`, `myuser`/`mypassword`)
  when env vars are absent; added `jwt.secret=${JWT_SECRET:<dev-default>}` property;
  `jwt.expiration-ms` changed from `1800000` (30 min) to `3600000` (60 min).
- `src/main/java/com/example/app/security/JwtUtil.java` — reads `${jwt.secret}` instead of
  the raw `${JWT_SECRET}` env var directly, so the secret now has a safe local default and
  follows the project's standard `application.properties` externalization pattern.
- `Dockerfile` — default `SERVER_PORT`/`EXPOSE` changed from `21552` to `25084`.
- `docker-compose.yml` — app/db now use port `25084`, and the Postgres database name matches
  the resolved database (`gen_9bb072199192`) instead of the original unreachable one.
- `start.sh`, `start.bat` — default `SERVER_PORT` changed from `21552` to `25084`.
- `README.md` — all example URLs/ports updated from `21552` to `25084`.

## Files Added

- `api_tests/test_full_lifecycle.sh` — end-to-end curl test suite covering: register
  (including duplicate-email rejection), login (including bad-password rejection),
  get/update current user, create/search/get/edit tool, unauthorized/forbidden checks,
  borrow-request create (including own-tool rejection), list (borrower/owner roles), get,
  approve (including non-owner rejection), reject path is exercised implicitly via business
  rules, activate, return, tool availability flips (unavailable on approve, available again
  on return), reservation list/get/update, two-way reviews (both directions + duplicate
  rejection), notifications list/mark-read, admin overdue-users/flagged-tools, delete-with-
  history rejection (400 by design) vs delete-without-history success (204) + 404
  confirmation, and the actuator health check.
- `start_0bcea87584ee7ad7.sh` — platform deployment boot script (not committed to git).

## Secrets Moved

- `JWT_SECRET` (previously injected directly into `JwtUtil` via `@Value("${JWT_SECRET}")`
  with no default) -> `application.properties` key `jwt.secret=${JWT_SECRET:dev-default-jwt-signing-secret-change-me-please-32-bytes-min}`.

## DB URLs Resolved

- `jdbc:postgresql://db:5432/gen_601cfe67f33b` -> `jdbc:postgresql://localhost:5432/gen_9bb072199192`
  (original Docker-network host `db` was unreachable outside compose; replaced with the
  pre-resolved local PostgreSQL database, wired as the default for `spring.datasource.url`,
  and mirrored into `docker-compose.yml`'s Postgres service definition).

## Test Results Summary

44 PASSED, 0 FAILED, 0 SKIPPED (see `api_tests/test_full_lifecycle.sh`)
