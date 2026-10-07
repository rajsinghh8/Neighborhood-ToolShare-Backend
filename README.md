# EventForge API

Event-planning REST API: events, tasks, guests, budget & expenses, schedule, vendors & payments, notifications, audit log.
Tornado 6.4 · SQLAlchemy 2 async · MySQL (prod) / SQLite (tests) · aiokafka · JWT (PyJWT) · bcrypt · pydantic v2.

## Run
    docker compose up -d --build        # app :8000, MySQL, Kafka
    # or locally
    pip install -r requirements.txt
    cp .env.example .env   # export the variables
    python -m app.main

- `GET /health`, `GET /docs` (Swagger UI), `GET /openapi.json` — public.
- API under `/api/v1` (Bearer JWT from `POST /api/v1/auth/login`).
- Errors: `{timestamp,status,error,message,path}`; lists: `{items,total,page,size,limit,offset}`.

## Test
    pip install -r requirements-dev.txt
    python -m pytest -q
Reports from the last verification run are in `tests-artifacts/`.

## Layout
`app/handlers` HTTP · `app/services` business rules · `app/repositories` data access · `app/models` ORM ·
`app/schemas` pydantic · `app/events` Kafka · `app/scheduler` periodic notifications · `app/openapi` spec.
