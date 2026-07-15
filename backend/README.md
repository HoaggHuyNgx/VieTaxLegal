# VieTaxLegal Backend

## Supabase setup

1. Create a Supabase project. Use its existing `postgres` database; do not create a separate
   `vietaxlegal` database inside the project.
2. In Supabase Dashboard, select **Connect** and copy the **Session pooler** connection string.
   Session mode on port `5432` is the recommended option for this persistent FastAPI backend on
   an IPv4 development machine.
3. Copy `.env.example` to `.env`, then replace `YOUR_PROJECT_REF`,
   `YOUR_URL_ENCODED_DB_PASSWORD`, `YOUR_POOLER_HOST`, and the placeholder `JWT_SECRET`.
4. Generate a secure JWT secret and paste it into `.env`:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

5. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -e ".[dev]"
   ```

6. Apply the Alembic schema to Supabase and start the API:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
   ```

The API documentation is available at `http://localhost:5000/docs`.

After migration, Supabase Table Editor should contain `public.users` and
`public.alembic_version`. This project uses Supabase only as managed PostgreSQL; Supabase Auth is
not enabled, so the existing FastAPI authentication flow remains the source of truth.

Keep the database password in `.env` only. The frontend does not need a Supabase anon key or
service-role key for this architecture.

## Authentication endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/auth/register` | Create an account and start a session. |
| `POST` | `/api/auth/login` | Sign in with either email or username. |
| `POST` | `/api/auth/logout` | Clear the current session cookie. |
| `GET` | `/api/auth/me` | Return the signed-in user. |

Authentication uses an HTTP-only, `SameSite=Lax` session cookie. Set `APP_ENV=production`
when deploying so the cookie is also marked `Secure`.

`JWT_SECRET` must be a random string of at least 32 characters. Set `CORS_ORIGINS` to explicit
frontend origins; wildcard (`*`) values are rejected because the API uses cookie authentication.

The frontend development server proxies `/api` to `http://localhost:5000`, so run both
applications during local development.

## Checks

```powershell
pytest
ruff check app tests
```

Tests use an in-memory SQLite database and never connect to the configured Supabase database.
