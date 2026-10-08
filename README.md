# School Management System API

Spring Boot 3.5.0 / Java 21 monolith: JWT auth (ADMIN, TEACHER), student CRUD with offset/limit pagination, Oracle persistence and Kafka student events through a transactional outbox.

## Run

```bash
docker compose up -d --build        # oracle + kafka + app
# Swagger UI:  http://localhost:8000/docs
# Health:      http://localhost:8000/health
```

The `oracle` service is built from `docker/oracle/Dockerfile` (gvenzl/oracle-free:23-slim plus a startup guard).
On hosts where `kernel.shmmax`/`shmall` read as 2^64-1, Oracle otherwise dies with ORA-00600 [ksmcsg] / ORA-27300;
the guard bind-mounts sane values only in that case (needs `cap_add: SYS_ADMIN`, dropped before Oracle starts) and is a no-op elsewhere.

Local development: start only infra (`docker compose up -d oracle kafka`), then `mvn spring-boot:run` (defaults point at `localhost:1521` and `localhost:29092`).

Default admin (seeded on first start): `admin` / `admin123`. Override via `.env` (see `.env.example`), and always set a real `JWT_SECRET` (>= 32 chars).

## API (all under `/api/v1`, bearer JWT unless noted)

| Method | Path | Roles | Notes |
|---|---|---|---|
| POST | `/auth/login` | public | access token (2h) + refresh token |
| POST | `/auth/refresh` | public | rotates the refresh token |
| POST | `/auth/register` | ADMIN | creates a user (ADMIN/TEACHER) |
| GET | `/students?grade=&offset=0&limit=20` | ADMIN, TEACHER | `limit` 1-100, response `{items, offset, limit, total}` |
| GET | `/students/count` | ADMIN, TEACHER | response `{count}` |
| GET | `/students/{id}` | ADMIN, TEACHER | |
| POST | `/students` | ADMIN | 201 + `Location` |
| PUT | `/students/{id}` | ADMIN | full replace |
| DELETE | `/students/{id}` | ADMIN | 204, hard delete |

Errors use one envelope: `{status, error, message, correlationId, timestamp}`; the correlation id is also in the logs.

## Kafka

Topic `student-events` (3 partitions), key = student id, value `{eventId, type: created|updated|deleted, studentId, timestamp}`.
Events are written to an `OUTBOX_EVENT` table in the same transaction as the change; a single background relay publishes them, so API calls never wait on the broker (broker outage = events delayed, never lost). The consumer commits offsets after processing, de-duplicates on `eventId` (`PROCESSED_EVENT`) and sends poison messages to `student-events.dlq`.

## Layout

`controller` (HTTP) -> `service` (business rules) -> `repository` (JPA); `security`, `kafka`, `exception`, `config`, `dto`, `model`, `seed`.

## Tests

`tests-artifacts/api_test_report.xlsx` and `project_report.docx` come from a live run (HTTP + real Kafka + Oracle).

Re-run: `python tests/run_api_tests.py` (stack up) then `python tests/generate_reports.py`.
