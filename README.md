# Neighborhood ToolShare Backend

A Spring Boot backend that lets neighbors list tools they own and borrow tools listed
by others in their neighborhood — with borrow requests, reservations, reviews and
notifications.

## Tech Stack

- Java 21, Spring Boot 3.5.0
- Spring Web, Spring Data JPA, Spring Security
- PostgreSQL 17.2 (Hibernate ORM 6.6.2)
- JWT (HS256) authentication via `io.jsonwebtoken`
- springdoc-openapi (Swagger UI) 2.8.9
- Maven (with Maven Wrapper)

## Authentication note

The business requirements mention a per-user "API Key" that is generated at
registration and returned again at login. This backend generates and exposes that
API key (`apiKey` field on the user, returned in the register/login responses and on
`GET /api/v1/users/me`) exactly as described. However, per this project's mandatory
security architecture, the actual mechanism used to **authenticate and authorize every
request** is a **JWT bearer token** (HS256, 30 minute expiry, no refresh flow), issued by
the same `/api/v1/auth/login` and `/api/v1/auth/register` endpoints. Send it as:

```
Authorization: Bearer <token>
```

All endpoints except `/api/v1/auth/**`, `/actuator/health`, and the API docs
(`/docs/**`, `/api-docs/**`, `/swagger-ui/**`) require this header.

RBAC is disabled for this project — there are no role/authority checks. The `Admin`
endpoints below are ordinary authenticated endpoints (any logged-in user may call
them) that surface aggregate/report data, since no per-role restriction was requested.

## Running locally (without Docker)

1. Ensure PostgreSQL is reachable and the credentials in
   `.env_3d186026-a490-405e-9a9b-e15f8ab6d64b` are correct (`DB_URL`, `DB_USER`,
   `DB_PASSWORD`, `JWT_SECRET`).
2. Run:

```bash
chmod +x ./start.sh
./start.sh
```

This loads `.env_3d186026-a490-405e-9a9b-e15f8ab6d64b`, builds the jar with the Maven
Wrapper, and starts the app on port `25084` (override with `SERVER_PORT=xxxx
./start.sh`).

On Windows, use `start.bat`.

## Running with Docker Compose

```bash
docker-compose up --build
```

This starts a `postgres:17.2` container plus the app container (built from the
multi-stage `Dockerfile`), wired together via the compose network. The app reads
`JWT_SECRET`, `DB_USER`, `DB_PASSWORD` from `.env_3d186026-a490-405e-9a9b-e15f8ab6d64b`
(loaded via `env_file:`) and connects to the `db` service by its compose service name.

## API Documentation

- Swagger UI: `http://localhost:25084/docs`
- OpenAPI JSON: `http://localhost:25084/api-docs`

Every endpoint is documented there with request/response schemas. To try an endpoint
that requires authentication, first call `POST /api/v1/auth/login`, copy the `token`
field from the response, and click "Authorize" in Swagger UI, entering
`Bearer <token>`.

## Environment variables (`.env_3d186026-a490-405e-9a9b-e15f8ab6d64b`)

| Variable      | Description                              |
|---------------|-------------------------------------------|
| `DB_URL`      | JDBC URL for PostgreSQL                    |
| `DB_USER`     | Database username                          |
| `DB_PASSWORD` | Database password                          |
| `JWT_SECRET`  | HS256 signing secret for JWT tokens        |

## Endpoints

Base path: `/api/v1`

| Method | Path                                    | Auth | Description |
|--------|------------------------------------------|------|--------------|
| POST   | `/auth/register`                         | No   | Register a new user; returns JWT + generated API key |
| POST   | `/auth/login`                            | No   | Login; returns JWT + the user's API key |
| GET    | `/users/me`                              | Yes  | Get current user's profile (includes API key) |
| PUT    | `/users/me`                              | Yes  | Update current user's profile |
| POST   | `/tools`                                  | Yes  | Add a new tool listing |
| GET    | `/tools?category=&neighborhood=&available=&page=&size=` | Yes  | Search/browse tools (paginated) |
| GET    | `/tools/mine`                             | Yes  | List tools owned by current user (paginated) |
| GET    | `/tools/{id}`                             | Yes  | Get a tool by id |
| PUT    | `/tools/{id}`                             | Yes  | Edit a tool (owner only) |
| PUT    | `/tools/{id}/availability?available=`     | Yes  | Mark tool available/unavailable (owner only) |
| DELETE | `/tools/{id}`                             | Yes  | Remove a tool (owner only) |
| POST   | `/borrow-requests`                        | Yes  | Request to borrow a tool |
| GET    | `/borrow-requests?role=borrower|owner`    | Yes  | List my borrow requests (paginated) |
| GET    | `/borrow-requests/{id}`                   | Yes  | Get a borrow request by id |
| PUT    | `/borrow-requests/{id}/approve`           | Yes  | Owner approves a pending request (creates a reservation) |
| PUT    | `/borrow-requests/{id}/reject`            | Yes  | Owner rejects a pending request |
| PUT    | `/borrow-requests/{id}/activate`          | Yes  | Mark an approved request active (tool picked up) |
| PUT    | `/borrow-requests/{id}/return`            | Yes  | Mark an active/overdue request returned |
| GET    | `/reservations?role=borrower|owner`       | Yes  | List my reservations (paginated) |
| GET    | `/reservations/{id}`                      | Yes  | Get a reservation by id |
| PUT    | `/reservations/{id}`                      | Yes  | Update pickup/return notes |
| POST   | `/reviews`                                | Yes  | Leave a rating/comment after a return |
| GET    | `/reviews/user/{userId}`                  | Yes  | List reviews received by a user (paginated) |
| GET    | `/reviews/{id}`                           | Yes  | Get a review by id |
| GET    | `/notifications`                          | Yes  | List my notifications (paginated) |
| PUT    | `/notifications/{id}/read`                | Yes  | Mark a notification read |
| GET    | `/admin/overdue-users?minCount=`          | Yes  | Users flagged for repeated overdue borrows |
| GET    | `/admin/flagged-tools?minCount=`          | Yes  | Tools flagged for repeated overdue borrows |
| GET    | `/actuator/health`                        | No   | Health check |

An overdue-flagging scheduled job runs every 5 minutes: any `ACTIVE` borrow request
whose reservation end date has passed is automatically transitioned to `OVERDUE`, with
notifications sent to both the borrower and the owner.

## Example requests

Register:

```bash
curl -X POST http://localhost:25084/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Jane Doe","email":"jane@example.com","password":"Secret123","neighborhood":"Maple Heights","phone":"555-1111"}'
```

Login:

```bash
curl -X POST http://localhost:25084/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jane@example.com","password":"Secret123"}'
```

Create a tool (replace `$TOKEN`):

```bash
curl -X POST http://localhost:25084/api/v1/tools \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Circular Saw","category":"Power Tools","description":"7 1/4 inch","condition":"GOOD","available":true}'
```

## Tests

Endpoint testing was performed with inline `curl` commands (see
`/api_tests/test_results.md` for the full pass/fail matrix) and an Excel report
(`api_test_report.xlsx`) is generated summarizing all results.

## Project structure

```
src/main/java/com/example/app/
  AppApplication.java
  config/        SecurityConfig, CorsConfig
  entity/        User, Tool, BorrowRequest, Reservation, Review, Notification, enums
  repository/    Spring Data JPA repositories
  service/       Business logic services
  controller/    REST controllers (/api/v1/...)
  dto/           Request/response DTOs
  security/      JwtUtil, JwtFilter, UserDetailsServiceImpl
  exception/     Custom exceptions + global exception handler
src/main/resources/
  application.properties
  data.sql
```
