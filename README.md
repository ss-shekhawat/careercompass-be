# CareerCompass Backend

FastAPI + PostgreSQL backend for the CareerCompass platform.

## Stack

- **FastAPI** 0.115 — REST API framework
- **SQLAlchemy** 2.0 — ORM
- **Alembic** — database migrations
- **PostgreSQL** (Neon free tier in prod, any PG locally)
- **JWT** (HS256) for auth — Bearer tokens

## Local setup

```bash
# 1. Create and activate a virtualenv
python -m venv venv
. venv/bin/activate          # Linux/Mac
# venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — at minimum set DATABASE_URL and JWT_SECRET
# Generate a real JWT_SECRET with:
#   python -c "import secrets; print(secrets.token_urlsafe(64))"

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

API will be available at `http://localhost:8000`.
Swagger docs at `http://localhost:8000/docs`.

## Project layout

```
app/
├── main.py           # FastAPI app, middleware, route registration
├── core/
│   └── config.py     # Settings via pydantic-settings (reads .env)
├── db/
│   ├── base.py       # SQLAlchemy DeclarativeBase
│   └── session.py    # Engine + session factory + get_db dependency
├── models/
│   └── user.py       # User ORM model
├── schemas/          # Pydantic request/response models (Day 2)
└── api/v1/           # Route handlers (Day 2)

alembic/
├── env.py            # Alembic config — reads DATABASE_URL from settings
└── versions/         # Migration files
```

## Migrations

```bash
# Generate a new migration from model changes
alembic revision --autogenerate -m "describe_the_change"

# Apply pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Preview SQL without applying (useful before deploys)
alembic upgrade head --sql
```

## Endpoints (Day 1)

| Method | Path     | Purpose                           |
|--------|----------|-----------------------------------|
| GET    | `/`      | Service banner                    |
| GET    | `/health`| Liveness probe (Render uses this) |
| GET    | `/docs`  | Swagger UI                        |

Auth + profile endpoints land on Day 2.
