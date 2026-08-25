# Library API

REST API for managing a library collection. It supports adding and listing books, borrowing and returning them, and deleting them.

The project is based on the [Minimal FastAPI PostgreSQL template](https://github.com/rafsaf/minimal-fastapi-postgres-template).

## Tech stack

- Python 3.14
- FastAPI
- PostgreSQL
- SQLAlchemy (asyncio)
- Alembic
- Pydantic
- Docker Compose
- uv
- pytest
- Ruff
- mypy

## Running locally

Copy the example environment file once, then start the application:

```bash
cp .env.example .env
docker compose up --build
```

Database migrations run automatically when the API container starts.

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/`
- Health probe: `GET http://localhost:8000/probe/health`

The API port can be changed with `API_PORT`.

## Tests and checks

Tests use PostgreSQL and create isolated test databases automatically. With the local database service running, use the same command as CI:

```bash
docker compose up -d postgres_db
uv run pytest
```

Run static checks with:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy .
```
