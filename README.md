# VieTaxLegal

VieTaxLegal is a Vietnamese-language assistant for looking up tax and business law. It has a React
frontend, a FastAPI backend, a PostgreSQL database (Supabase) and an AI layer that can switch between
Anthropic and OpenAI.

The current version has accounts, a legal chat with per-user history, and a RAG pipeline: legal
corpus → Qdrant index → retrieval (dense, sparse or hybrid) → an answer that cites real sources. RAG
is off by default (`RAG_ENABLED=false`); see [backend/README.md](backend/README.md#ai-and-rag) to
build the index and turn it on.

This is a graduation thesis project.

## Feature status

| Feature                                                        | Status          |
| -------------------------------------------------------------- | --------------- |
| Register, sign in, sign out, session check                     | Done            |
| Email verification code before registration (needs SMTP)       | Done            |
| Google sign-in and account linking (needs OAuth client)        | Done            |
| HTTP-only session cookies, Argon2id passwords                  | Done            |
| Rotating refresh tokens, admin role, login throttling          | Done            |
| Streaming chat over SSE                                        | Done            |
| Save, open and delete conversations                            | Done            |
| Anthropic and OpenAI providers (via LangChain)                 | Done            |
| Per-minute and per-day chat limits                             | Done            |
| Vietnamese / English interface                                 | Done            |
| Legal corpus (323 documents indexed) and Điều/Khoản parser     | Done            |
| Qdrant index, OpenAI embeddings, dense / sparse / hybrid       | Done            |
| Query rewriting, Cohere reranking, "no source" gate (optional) | Done            |
| Whole-article expansion of each source (optional)              | Done            |
| English questions answered in English from the same sources    | Done            |
| Real citations: stored, returned and shown                     | Done            |
| RAG evaluation (questions, metrics, runner, comparison, export) | Done            |

When RAG is off or finds nothing, the assistant shows no sources, never invents document numbers or
articles, and always reminds the user to check that a document is still in force.

## Architecture

```mermaid
flowchart LR
    U["User"] --> F["React / Vite"]
    F -->|"/api proxy"| B["FastAPI"]
    B --> D["PostgreSQL (Supabase)"]
    B --> A["Anthropic or OpenAI"]
    B -->|"RAG_ENABLED"| Q["Qdrant (rebuildable index)"]
    B -->|"query embedding"| E["OpenAI Embeddings"]
```

The backend is the only layer that touches application data; the frontend never connects to the
database. The database is Supabase-managed PostgreSQL reached through the Session pooler, so no
local PostgreSQL install is needed. Qdrant runs in Docker.

## Tech stack

- Frontend: React 18, Vite 5, React Router 6, Tailwind CSS v4, React Markdown (JavaScript, no
  TypeScript).
- Backend: Python 3.12+, FastAPI, Uvicorn, Pydantic.
- Database: PostgreSQL on Supabase, SQLAlchemy 2, Alembic, Psycopg 3.
- Auth: Argon2id (`pwdlib`), JWT (`PyJWT`), HTTP-only cookies.
- AI: LangChain (`langchain-anthropic` or `langchain-openai` Responses API) for chat and OpenAI
  embeddings. Qdrant retrieval, sparse vectors, RRF fusion, chunking and citations are hand-written.
- RAG: Qdrant (Docker), OpenAI `text-embedding-3-small`, dense, sparse (hand-written BM25) and hybrid
  (RRF) retrieval.
- Streaming: Server-Sent Events (SSE).
- Quality: Pytest, Ruff, Vitest, ESLint, Prettier; GitHub Actions CI for both sides.

## Repository layout

```text
VieTaxLegal/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routes and dependencies (current user, roles)
│   │   ├── core/          # settings, security, errors, logging
│   │   ├── db/            # SQLAlchemy engine and session
│   │   ├── models/        # database models
│   │   ├── schemas/       # Pydantic request/response schemas
│   │   └── services/      # admin.py, auth/, chat/, rag/{ingest,index,retrieve}
│   ├── corpus/            # legal documents: source of truth for the index
│   ├── rag_eval/          # evaluation harness, configs and results
│   ├── scripts/           # corpus_*, eval_*, admin_create
│   ├── migrations/        # Alembic migrations
│   ├── tests/             # backend tests
│   └── README.md          # backend details
├── frontend/
│   ├── src/
│   │   ├── components/    # admin/, auth/, chat/, common/, landing/
│   │   ├── context/       # AuthContext and useAuth
│   │   ├── data/          # static landing and chat content
│   │   ├── i18n/          # translator and VI/EN catalogs
│   │   ├── pages/         # Landing, Chat, Settings, Admin
│   │   ├── services/      # API calls and SSE client
│   │   └── styles/        # index.css: Tailwind tokens and base rules
│   ├── nginx.conf         # production static server + /api proxy
│   └── README.md          # frontend details
├── docker-compose.yml     # Qdrant + backend + frontend
└── .github/workflows/     # backend and frontend CI
```

## Requirements

- Node.js 20.19+, 22.13+ or 24+, and npm.
- Python 3.12 or newer.
- A Supabase project (its Session pooler URL is `DATABASE_URL`).
- An Anthropic or OpenAI API key for real chat answers.
- Docker Desktop, only for Qdrant (RAG) or the Compose setup.

## Quick start on Windows

### 1. Backend

```powershell
cd D:\VieTaxLegal\backend
Copy-Item .env.example .env
notepad .env
```

Put the Supabase Session pooler URL in `DATABASE_URL` (see
[backend/README.md](backend/README.md#1-connect-the-database-supabase)), generate a `JWT_SECRET` of at
least 32 characters and configure one AI provider. Never commit the database password, JWT secret or
API keys.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
```

`alembic upgrade head` changes the real Supabase database. Keep the backend terminal open and check:

- Health: <http://127.0.0.1:5000/api/health>
- Swagger UI: <http://127.0.0.1:5000/docs>

### 2. Frontend

In a second terminal:

```powershell
cd D:\VieTaxLegal\frontend
npm install
npm run dev
```

Open <http://localhost:3000>. Vite forwards every `/api` request to `http://localhost:5000`.

## Docker Compose

One command starts Qdrant, the backend and the frontend (nginx serving the build and proxying
`/api`). There is no Postgres container: the database is still Supabase, passed in as
`DATABASE_URL`. The backend does **not** run migrations on start, because the database holds real
data; run them by hand when needed with `docker compose run --rm backend alembic upgrade head`.

```powershell
$env:DATABASE_URL = "postgresql://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres"
$env:JWT_SECRET = "a-random-string-of-at-least-32-characters"
$env:ANTHROPIC_API_KEY = "..."   # or OPENAI_API_KEY + CHAT_PROVIDER=openai
docker compose up --build
```

Open <http://localhost:3000>. The port is published on `127.0.0.1` only, so other machines on your
network cannot reach the app. To open it from a phone, change `127.0.0.1:3000:80` to `3000:80` in
`docker-compose.yml`, knowing that the connection is plain HTTP.

The same variables can live in a `.env` file at the repository root (gitignored). Compose does not
read `backend/.env`. The backend gets every variable in the root `.env`; those listed under
`environment` in `docker-compose.yml` (such as `QDRANT_URL`) keep the Compose value. If a standalone
Qdrant container is running (`scripts/start-qdrant.ps1`), stop it first: both use port 6333.

### RAG under Docker

`docker compose up` alone gives chat without RAG: `RAG_ENABLED` is false and the index is empty. For
the evaluated setup, put these in the root `.env`, next to `DATABASE_URL`, `JWT_SECRET`,
`OPENAI_API_KEY` and `COHERE_API_KEY`:

```text
CHAT_PROVIDER=openai
CHAT_MODEL=gpt-6-luna
CHAT_MAX_OUTPUT_TOKENS=4000
RAG_ENABLED=true
RAG_CHUNK_SET=vbpl
RAG_QUERY_PLANNER_MODEL=gpt-4.1-mini
RAG_RERANK_MODEL=rerank-v5.0-fast
RAG_MIN_TOP_SCORE=0.5
RAG_EXPAND_ARTICLES=true
```

Then build the index inside the backend image. This calls the OpenAI embedding API (about US$0.10 by
the dry-run estimate) and keeps the index in the `qdrant_data` volume; `backend/corpus/` is mounted
read-only.

```powershell
docker compose run --rm backend python scripts/corpus_ingest.py --chunk-set vbpl --extra-manifest corpus/vbpl/manifest.json --extra-manifest corpus/vbpl/manual/manifest.json
```

Add `--dry-run` to see the chunk count and cost estimate without calling the API.

## Authentication and roles

- **Access token**: short-lived JWT (`ACCESS_TOKEN_MINUTES`, default 15) in the HTTP-only cookie
  `vietaxlegal_session`.
- **Refresh token**: random string, stored only as a SHA-256 hash in `refresh_tokens`, in the
  HTTP-only cookie `vietaxlegal_refresh` scoped to `/api/auth`. Each use revokes it and issues a new
  one; reusing an old token revokes the whole session family. Lifetime is 24 hours, or 30 days with
  "remember me".
- **Sign-out** revokes the session on the server. Deactivating a user (`isActive=false`) revokes all
  of that user's sessions.
- **Roles**: `users.role` is `user` or `admin`; `require_role(...)` returns `403 FORBIDDEN`. The
  first admin can only be created with `scripts/admin_create.py`; there is no HTTP path to promote
  yourself.
- **Registration** needs a verified email: request a 6-digit code, verify it, and send the returned
  proof with the register payload. New passwords need 12+ characters, an uppercase letter, a digit
  and a symbol, and must not contain the username or email name.
- **Rate limits**: failed logins 5 per 15 minutes per `ip|identifier` and 30 per 15 minutes per IP;
  registration `REGISTER_MAX_PER_HOUR` (10) per IP; chat 10 messages per minute and 100 per day per
  user. These counters (except chat, which is stored in the database) live in process memory, so
  they are correct for a single worker only.
- The frontend calls `/auth/refresh` once on a `401` and retries the request (`authFetch` in
  `frontend/src/services/api.js`).

## Frontend routes

| Route       | Description                                          |
| ----------- | ---------------------------------------------------- |
| `/`         | Landing page with sign-in and registration.          |
| `/chat`     | Legal chat; requires sign-in.                        |
| `/settings` | Account settings (link a Google account).            |
| `/admin`    | User management; requires the `admin` role.          |

## API

All endpoints are under `/api`.

| Method   | Endpoint                       | Description                                         |
| -------- | ------------------------------ | --------------------------------------------------- |
| `GET`    | `/api/health`                  | API and database check; `503` if the DB is down.    |
| `POST`   | `/api/auth/email-code`         | Email a verification code (needs SMTP).             |
| `POST`   | `/api/auth/email-code/verify`  | Check the code; returns the `proof` for registering. |
| `GET`    | `/api/auth/google/login`       | Redirect to Google to sign in.                      |
| `GET`    | `/api/auth/google/link`        | Redirect to Google to link an account (signed in).  |
| `GET`    | `/api/auth/google/callback`    | Google callback; creates the session, back to app.  |
| `POST`   | `/api/auth/register`           | Register and start a session.                       |
| `POST`   | `/api/auth/login`              | Sign in with email or username.                     |
| `POST`   | `/api/auth/refresh`            | Rotate the refresh token, issue a new access token. |
| `POST`   | `/api/auth/logout`             | Sign out and revoke the refresh token.              |
| `GET`    | `/api/auth/me`                 | Current user.                                       |
| `GET`    | `/api/admin/users`             | (admin) List users.                                 |
| `PATCH`  | `/api/admin/users/{id}`        | (admin) Change `role` or `isActive`.                |
| `GET`    | `/api/chat/usage`              | Messages used and left today.                       |
| `GET`    | `/api/chat/conversations`      | List conversations.                                 |
| `GET`    | `/api/chat/conversations/{id}` | One conversation with its messages.                 |
| `DELETE` | `/api/chat/conversations/{id}` | Delete a conversation.                              |
| `POST`   | `/api/chat/messages/stream`    | Send a question and receive an SSE stream.          |

Every error uses one envelope: `{"error": {"code", "message", "fields"}}`. The frontend translates by
`code` into the selected language; the backend's Vietnamese `message` is only a fallback. The full
error code table is in [backend/README.md](backend/README.md#error-format).

## RAG

```text
Legal documents (backend/corpus/, tracked in git)
  → text extraction (DOCX / PDF / portal HTML)
  → split by Điều / Khoản / Điểm, check numbering order and gaps
  → dense embedding (OpenAI) + sparse vector (hand-written BM25)
  → Qdrant (rebuildable from corpus/)
  → [optional] rewrite the question into several queries
  → dense / sparse / hybrid (RRF) search, in-force documents only
  → [optional] "no source" gate, rerank (Cohere), expand each source to its whole Điều
  → the model answers in the question's language and writes [n]; only cited sources are
    stored and shown
```

`backend/corpus/` is the source of truth; the Qdrant index can be deleted and rebuilt at any time
(rebuilding calls the embedding API). Steps for building the index and running the evaluation are in
[backend/README.md](backend/README.md#ai-and-rag).

### Corpus

| Set                                        | Documents       | Used for                               |
| ------------------------------------------ | --------------- | -------------------------------------- |
| `corpus/manifest.json` (hand-collected)    | 23 (21 indexed) | `article` chunk set, early experiments |
| plus `corpus/vbpl/` (imported + by hand)   | 323 indexed     | `vbpl` chunk set, the evaluated app    |

The 323 documents are 23 laws, 95 decrees, 203 circulars and 2 consolidated texts on tax and
household business (103), enterprise and investment (138), and labour, social insurance and wages
(82), the newest issued in July 2026. All but 7 older laws were issued in 2020 or later.

Most of `corpus/vbpl/texts/` comes from the dataset
[th1nhng0/vietnamese-legal-documents](https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents)
(revision `8977887`, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)), a snapshot of the
vbpl.vn portal. Changes made here: only the selected documents were kept, their HTML was turned into
plain text, and documents that failed the structure checks were left out. Documents missing or broken
in the dataset were added from Công báo files (`corpus/vbpl/manual/`). The selection lists are in
`corpus/vbpl/selection/`. Whether each document is still in force comes from that snapshot and from
scans of effect clauses; no person has verified it.

### Evaluation results

Test split, run once on 2026-11-28 at commit `3543dea` with the settings the app uses: `vbpl` set,
hybrid search, query planner `gpt-4.1-mini`, Cohere `rerank-v5.0-fast` (no fallbacks), gate 0.5,
whole-article expansion, 5 sources, answers by OpenAI `gpt-6-luna`. Parameters were chosen on the
dev split only.

| Measure (40 answerable questions)              | Result                   |
| ---------------------------------------------- | ------------------------ |
| Gold article ranked first / in the top 5       | 72.5% / 92.5% (MRR 0.81) |
| Answer correct / partial / incorrect           | 32 (80%) / 6 / 2         |
| Citation precision / recall                    | 0.70 / 0.89              |
| Answers with a reference not in their sources¹  | 0 of all 44              |
| Time to full answer, median / 95th percentile  | 7.8 s / 11.9 s           |

¹ A document number or article found neither in the retrieved passages nor in the question. 3
answers name an article by the law's name only, which cannot be checked automatically.

Both incorrect answers followed a search that missed the gold article.

The run also had 4 out-of-corpus questions, and the gate stopped none of them. After seeing the
results, the project author removed 2 of the 4 from the question set (`q069`, a traffic fine, and
`q070`, a land-use certificate). The result files still contain all 4, and the question file used in
the run is the one at commit `3543dea`. A keyword search of the 323 documents found no answer to the
other 2, and the project author read both answers and marked them as refusals. `SUMMARY.md` shows no
refusal rate for this run, because the 2 removed questions are unmarked in its result file.

How far these numbers can be trusted:

- The sample is small: for 32 of 40, a 95% interval is roughly 65% to 90%.
- All answerable questions were written from the 23 hand-collected documents, not from the other 300.
- Questions and gold answers were written by AI and checked against the law text by AI. The project
  author spot-checked 20 of them, 10 from the test split. No lawyer has reviewed them.
- "Correct" is the verdict of an LLM judge (`gpt-4.1-mini`) comparing with the gold answer.

All result tables are generated into `backend/rag_eval/results/SUMMARY.md` by
`scripts/eval_export_results.py`. Results measured before 2026-11-26 are archived in
`rag_eval/results/superseded-261126/` because the scoring changed; do not compare them with new
results.

## Quality checks

```powershell
cd D:\VieTaxLegal\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m ruff format --check app tests
```

```powershell
cd D:\VieTaxLegal\frontend
npm run check
```

`npm run check` runs Vitest, ESLint (0 warnings), the Prettier check and a production build; the
Husky pre-commit hook runs it too. Backend tests use in-memory SQLite, a fake AI provider and an
in-memory Qdrant client: they never touch a real database, a paid API or a Qdrant server. CI also
runs `alembic upgrade head` and `alembic check` against Postgres 15.

## Security

- Passwords are hashed with Argon2id and never stored in plain text.
- JWTs live in HTTP-only, `SameSite=Lax` cookies; production adds `Secure`.
- The backend refuses a weak JWT secret and a CORS wildcard.
- Every conversation query is filtered by the current user; another user's UUID returns `404`.
- On Supabase, migrations enable RLS and revoke `anon` / `authenticated` on application tables; on
  plain PostgreSQL that step is skipped because those roles do not exist.
- nginx adds CSP, `X-Content-Type-Options`, `Referrer-Policy` and `X-Frame-Options`. With
  `APP_ENV=production`, `/docs`, `/redoc` and `/openapi.json` are turned off.
- AI API keys exist only in the backend and are never logged or sent to the frontend. Logs never
  contain prompts, passwords, tokens, query strings or request bodies.
- `.env` files, keys, certificates, database dumps, uploads and logs are never committed.

## Logging

Configured in `backend/app/core/logging.py`. `LOG_LEVEL` (default `INFO`) and `LOG_JSON` (`true` =
one JSON object per line; Compose turns it on). Each request gets an `X-Request-ID` (taken from the
client if valid, otherwise generated), returned in the response header and attached to every log
line of that request. The access log records only method, path, status and duration.
