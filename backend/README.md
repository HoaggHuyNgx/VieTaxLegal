# VieTaxLegal Backend

FastAPI backend for accounts, sessions, conversation history, streaming AI answers and the RAG
pipeline. Data lives in PostgreSQL (Supabase); the frontend only talks to this API.

## Layout

```text
app/
├── main.py               # creates the FastAPI app: middleware, error handlers, routers
├── api/
│   ├── router.py         # mounts every route module under /api
│   ├── deps.py           # get_current_user, require_role
│   └── routes/           # health, auth, auth_email, auth_google, admin, chat (thin HTTP layer)
├── core/                 # config, security (JWT, Argon2id), errors, logging, request log
├── db/                   # SQLAlchemy engine and session
├── models/               # user, chat, refresh_token, oauth_identity, email_otp
├── schemas/              # Pydantic schemas (auth, chat, admin)
└── services/             # business logic and DB access
    ├── admin.py          # user management
    ├── auth/             # register/login, refresh tokens, throttles, email codes, Google, mailer
    ├── chat/
    │   ├── service.py    # two-phase stream: prepare (DB) → SSE → finalize
    │   ├── provider.py   # ModelProvider: LangChain over Anthropic / OpenAI
    │   ├── prompt.py     # system prompt (no invented citations)
    │   ├── citations.py  # parse [n] markers, keep only cited sources
    │   ├── history.py    # history window and retrieval query
    │   ├── limits.py     # per-minute / per-day limits, stuck "pending" replies
    │   └── retriever.py  # Retriever interface and get_retriever()
    └── rag/              # one folder per pipeline stage
        ├── ingest/       # 1. text extraction, Điều/Khoản parser, chunking, ingest
        ├── index/        # 2. embeddings, sparse vectors, Qdrant store
        └── retrieve/     # 3. query planner, hybrid search, RRF, rerank
corpus/                   # manifest.json, raw/, texts/: source of truth for the index
rag_eval/                 # evaluation harness, configs/{retrieval,generation}/, data/, results/
scripts/                  # corpus_*, eval_*, admin_create.py, start-qdrant.ps1
migrations/               # Alembic (head: 0007_email_otps)
tests/                    # API and service tests, tests/rag/, tests/eval/
```

Layering is **routes → services → models**: routes stay thin, logic and DB access live in services.
Errors are raised as `AppError(status, "CODE", "Vietnamese message")`.

## Requirements

- Python 3.12 or newer.
- A Supabase project (managed PostgreSQL; no local PostgreSQL install).
- An Anthropic or OpenAI API key for real chat answers.
- Docker Desktop for Qdrant, only when RAG is used.

## 1. Connect the database (Supabase)

1. Supabase Dashboard → **Connect** → **Connection Method: Session pooler**, type `URI`, and copy a
   URL like
   `postgresql://postgres.<project-ref>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`.
   Do not use *Direct connection* (IPv6 only, often unreachable from Windows) or *Transaction pooler*
   (port 6543, does not work with psycopg 3 prepared statements).
2. Copy `.env.example` to `.env`:

```powershell
cd D:\VieTaxLegal\backend
Copy-Item .env.example .env
notepad .env
```

3. Paste the URL into `DATABASE_URL` and replace `[YOUR-PASSWORD]` (brackets included) with the
   database password. A forgotten password can be reset in **Project Settings → Database**.
4. If the password contains `@`, `:`, `/`, `#` or `%`, URL-encode it (or use letters and digits only).
5. Generate a JWT secret:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Never share or commit `.env`, the database password, the JWT secret or API keys.

## 2. Environment variables

Only two variables are required; the backend will not start without them:

| Variable       | Description                                                          |
| -------------- | -------------------------------------------------------------------- |
| `DATABASE_URL` | PostgreSQL URL.                                                      |
| `JWT_SECRET`   | Random string of at least 32 characters; the sample value is refused. |

`DATABASE_URL` is normalized: a `postgres://` or `postgresql://` prefix becomes
`postgresql+psycopg://`, and `sslmode=require` is added for Supabase hosts when missing.

Everything else has a default (all listed in `.env.example`). Model IDs are configuration only;
check the provider's documentation before changing them.

**App, auth and logging**

| Variable                       | Default                 | Description                                                          |
| ------------------------------ | ----------------------- | -------------------------------------------------------------------- |
| `APP_ENV`                      | `development`           | `development`, `testing` or `production` (`Secure` cookies, no docs). |
| `CORS_ORIGINS`                 | `http://localhost:3000` | Comma-separated origins; `*` is refused.                             |
| `SESSION_COOKIE_NAME`          | `vietaxlegal_session`   | Access-token cookie.                                                 |
| `REFRESH_COOKIE_NAME`          | `vietaxlegal_refresh`   | Refresh-token cookie.                                                |
| `ACCESS_TOKEN_MINUTES`         | `15`                    | Access JWT lifetime.                                                 |
| `SESSION_TOKEN_HOURS`          | `24`                    | Refresh-token lifetime without "remember me".                        |
| `REMEMBER_ME_DAYS`             | `30`                    | Refresh-token lifetime with "remember me".                           |
| `JWT_ALGORITHM`                | `HS256`                 | `HS256`, `HS384` or `HS512`.                                         |
| `REGISTER_MAX_PER_HOUR`        | `10`                    | Registration attempts per client address per hour.                   |
| `LOGIN_MAX_FAILED_ATTEMPTS`    | `5`                     | Failed logins allowed per address + identifier.                      |
| `LOGIN_ATTEMPT_WINDOW_MINUTES` | `15`                    | Window for counting failed logins.                                   |
| `LOG_LEVEL`                    | `INFO`                  | `DEBUG`, `INFO`, `WARNING`, `ERROR` or `CRITICAL`.                   |
| `LOG_JSON`                     | `false`                 | One JSON object per log line.                                        |

**Email codes and Google sign-in** (both off until configured)

| Variable               | Default                                          | Description                                    |
| ---------------------- | ------------------------------------------------ | ---------------------------------------------- |
| `SMTP_HOST`            | empty                                            | Without it, password registration is off.      |
| `SMTP_PORT`            | `587`                                            | `587` = STARTTLS, `465` = implicit TLS.        |
| `SMTP_USER`            | empty                                            | SMTP login.                                    |
| `SMTP_PASSWORD`        | empty                                            | SMTP password.                                 |
| `SMTP_FROM`            | `SMTP_USER`                                      | Sender address.                                |
| `GOOGLE_CLIENT_ID`     | empty                                            | Google sign-in needs both id and secret.       |
| `GOOGLE_CLIENT_SECRET` | empty                                            |                                                |
| `GOOGLE_REDIRECT_URI`  | `http://localhost:5000/api/auth/google/callback` | Must match the Google Cloud console.           |
| `FRONTEND_URL`         | `http://localhost:3000`                          | Where the callback sends the browser back.     |

**Chat**

| Variable                     | Default           | Description                                            |
| ---------------------------- | ----------------- | ------------------------------------------------------ |
| `CHAT_PROVIDER`              | `anthropic`       | `anthropic` or `openai`.                               |
| `CHAT_MODEL`                 | `claude-sonnet-5` | Model ID for the selected provider.                    |
| `ANTHROPIC_API_KEY`          | empty             | Needed when `CHAT_PROVIDER=anthropic`.                 |
| `OPENAI_API_KEY`             | empty             | Needed when `CHAT_PROVIDER=openai` and for embeddings. |
| `CHAT_MAX_OUTPUT_TOKENS`     | `1500`            | `1–8192`.                                              |
| `CHAT_HISTORY_MESSAGES`      | `20`              | Recent messages sent back to the model, `1–100`.       |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `10`              | Questions per user per minute.                         |
| `CHAT_DAILY_MESSAGE_LIMIT`   | `100`             | Questions per user per UTC day.                        |

History is also capped at 40,000 characters (`MAX_HISTORY_CHARACTERS` in
`app/services/chat/history.py`), so long conversations are cut before `CHAT_HISTORY_MESSAGES`.

**RAG**

| Variable                     | Default                  | Description                                                     |
| ---------------------------- | ------------------------ | --------------------------------------------------------------- |
| `RAG_ENABLED`                | `false`                  | Use retrieval in chat (needs an ingested Qdrant collection).    |
| `RAG_CHUNK_SET`              | `article`                | Chunk set / collection to search.                               |
| `RAG_TOP_K`                  | `5`                      | Passages returned, `1–50`.                                      |
| `RAG_RETRIEVAL_MODE`         | `hybrid`                 | `dense`, `sparse` or `hybrid`.                                  |
| `RAG_MIN_SIMILARITY`         | `0`                      | Minimum cosine `0–1`; `0` keeps everything.                     |
| `RAG_REQUIRE_IN_FORCE`       | `true`                   | Only return documents marked `in_force`; `false` for dev only.  |
| `RAG_QUERY_PLANNER_PROVIDER` | `openai`                 | Provider of the query planner.                                  |
| `RAG_QUERY_PLANNER_MODEL`    | empty                    | Rewrites the question before search; empty = off.               |
| `RAG_RERANK_MODEL`           | empty                    | Cohere Rerank model (e.g. `rerank-v5.0-fast`); empty = off.     |
| `COHERE_API_KEY`             | empty                    | Needed when `RAG_RERANK_MODEL` is set.                          |
| `RAG_MIN_TOP_SCORE`          | `0`                      | "No source" when the best dense cosine is lower; `0` = off.     |
| `RAG_EXPAND_ARTICLES`        | `false`                  | Replace a matched Khoản chunk by its whole Điều (one per Điều). |
| `EMBEDDING_PROVIDER`         | `openai`                 | `openai`, `bkai` (local, experiment only) or `fake` (tests).    |
| `EMBEDDING_MODEL`            | `text-embedding-3-small` | Embedding model; the Qdrant collection name is derived from it. |
| `EMBEDDING_DIMENSIONS`       | empty                    | OpenAI only: shorter vectors; empty = model default.            |
| `EMBEDDING_BATCH_SIZE`       | `64`                     | Chunks per embedding call, `1–512`.                             |
| `QDRANT_URL`                 | `http://127.0.0.1:6333`  | Qdrant address.                                                 |
| `QDRANT_API_KEY`             | empty                    | Only for a remote Qdrant.                                       |
| `EVAL_GENERATOR_MODEL`       | empty                    | Model that writes eval questions; empty = `CHAT_MODEL`.         |

Example (Anthropic):

```env
CHAT_PROVIDER=anthropic
CHAT_MODEL=claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-...
```

Only the selected provider's key is required. Switching provider does not change any route or the
SSE format.

## 3. Install dependencies

```powershell
cd D:\VieTaxLegal\backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt -e ".[dev]"
```

`constraints.txt` pins tested versions of every package so installs are reproducible (CI uses it
too). After a deliberate upgrade, regenerate it with
`.\.venv\Scripts\python.exe -m pip freeze --exclude-editable`.

Optional extras, none needed by the app or CI:

| Extra           | For                                                                  |
| --------------- | -------------------------------------------------------------------- |
| `corpus`        | PDF extraction and vbpl import (`pymupdf`, `pyarrow`, `beautifulsoup4`). |
| `eval-baseline` | The stock LangChain baseline in the evaluation.                      |
| `local-embed`   | The local BKAI embedding model (large CPU torch download).           |

No need to activate the virtualenv when Python is always called as `.\.venv\Scripts\python.exe`.

## 4. Migrations

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

The database is a real Supabase project: back up or check before upgrading.

| Revision                       | Change                                                                  |
| ------------------------------ | ----------------------------------------------------------------------- |
| `0001_create_users`            | `users` table with unique email / username.                             |
| `0002_lock_down_public_tables` | Supabase only: enable RLS and hide `users` / `alembic_version`.         |
| `0003_chat`                    | `conversations`, `messages`, `chat_usage_events` with indexes and checks. |
| `0004_message_citations`       | `messages.citations` (JSON, nullable).                                  |
| `0005_roles_refresh_tokens`    | `users.role` (user / admin) and `refresh_tokens`.                       |
| `0006_oauth_identities`        | `oauth_identities` (Google); `users.password_hash` becomes nullable.    |
| `0007_email_otps`              | `email_otps` (email verification before registration).                  |

`alembic current` should print `0007_email_otps (head)`. The RLS / REVOKE steps only run when both
the `anon` and `authenticated` roles exist (Supabase); on plain PostgreSQL they are skipped.
Supabase Auth is not used: the `users` table and FastAPI sessions are the only source of identity.

## 5. Run the API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
```

On `Application startup complete`, check:

- Health: <http://127.0.0.1:5000/api/health> → `{"status": "ok", "database": "ok"}`
- Swagger UI: <http://127.0.0.1:5000/docs> (development only)

Startup reads and validates settings, builds the app, adds CORS, request logging and the error
handlers, and mounts the routers. The database connects on the first request that needs it; the
Qdrant client is created on the first RAG search and closed on shutdown.

## Auth API

| Method | Endpoint                      | Description                                            |
| ------ | ----------------------------- | ------------------------------------------------------ |
| `POST` | `/api/auth/email-code`        | Email a 6-digit code (needs SMTP); `204`.              |
| `POST` | `/api/auth/email-code/verify` | Check the code; returns `{"proof": "..."}`.            |
| `POST` | `/api/auth/register`          | Create the account and set session cookies; `201`.     |
| `POST` | `/api/auth/login`             | Sign in with email or username.                        |
| `POST` | `/api/auth/refresh`           | Rotate the refresh token and issue a new access token. |
| `POST` | `/api/auth/logout`            | Revoke the session and clear cookies; `204`.           |
| `GET`  | `/api/auth/me`                | Current user.                                          |
| `GET`  | `/api/auth/google/login`      | Redirect to Google to sign in.                         |
| `GET`  | `/api/auth/google/link`       | Redirect to Google to link the signed-in account.      |
| `GET`  | `/api/auth/google/callback`   | Google callback; back to `FRONTEND_URL`.               |

Registration: a code lives 10 minutes, can be resent after 60 seconds (at most 5 per hour) and
allows 5 attempts; the proof it returns is valid for 15 minutes.

```json
{
  "email": "user@example.com",
  "username": "user_legal",
  "fullName": "Nguyen Van A",
  "phone": "0901234567",
  "password": "A-safe-password-2026!",
  "acceptTerms": true,
  "emailProof": "<proof from /email-code/verify>"
}
```

New passwords need 12–128 characters, an uppercase letter, a digit and a symbol, and must not contain
the username or the part of the email before `@` (`app/services/auth/password_policy.py`, mirrored in
the frontend for live feedback). Login accepts any existing password.

```json
{ "identifier": "user@example.com", "password": "A-safe-password-2026!", "rememberMe": false }
```

Failed logins are limited per (client address, identifier): more than `LOGIN_MAX_FAILED_ATTEMPTS`
failures within `LOGIN_ATTEMPT_WINDOW_MINUTES` returns `429 AUTH_RATE_LIMITED`, even with the right
password, until the window ends. A successful login clears that counter. A second cap per address
alone, 6× higher (30 by default), stops one source from trying many accounts. These counters live in
process memory: they reset on restart and are not shared between workers. Behind a proxy that does
not forward the real IP, every client shares one address (the Compose nginx forwards it).

Cookies are `HttpOnly` and `SameSite=Lax`; the access cookie has `Path=/`, the refresh cookie
`Path=/api/auth`. With `APP_ENV=production` both add `Secure`.

## Admin API

| Method  | Endpoint                | Description                                    |
| ------- | ----------------------- | ---------------------------------------------- |
| `GET`   | `/api/admin/users`      | List users.                                    |
| `PATCH` | `/api/admin/users/{id}` | Change `role` or `isActive` (not on yourself). |

Both need the `admin` role. Create the first admin from the command line:

```powershell
.\.venv\Scripts\python.exe scripts\admin_create.py user@example.com
```

## Chat API

All chat endpoints need a signed-in session.

| Method   | Endpoint                           | Description                                         |
| -------- | ---------------------------------- | --------------------------------------------------- |
| `GET`    | `/api/chat/usage`                  | `dailyLimit`, `dailyUsed`, `dailyRemaining`.        |
| `GET`    | `/api/chat/conversations?limit=50` | Conversations, newest first (`limit` 1–50).         |
| `GET`    | `/api/chat/conversations/{id}`     | One conversation of the current user with messages. |
| `DELETE` | `/api/chat/conversations/{id}`     | Delete it and its messages; `204`.                  |
| `POST`   | `/api/chat/messages/stream`        | Send a question, receive an SSE stream.             |

`DELETE` returns `409 CHAT_IN_PROGRESS` while an assistant reply is still `pending`; stop the stream
first.

```json
{ "conversationId": null, "content": "Điều kiện khấu trừ thuế GTGT là gì?" }
```

Pass a UUID as `conversationId` to continue a conversation. `content` must be 1–4,000 characters.

### SSE events

| Event   | Payload                                                              |
| ------- | -------------------------------------------------------------------- |
| `meta`  | Conversation, user message and the `pending` assistant message.      |
| `delta` | `{messageId, text}`: the next piece of text from the model.          |
| `done`  | The final assistant message, token usage and citations.              |
| `error` | Safe error code, message and whether a retry can help.               |

The stream runs in two phases: `prepare_chat_stream` saves the user message and a `pending`
assistant message (synchronous DB work), then the async stream calls the model, and
`_finalize_message` stores the result. A finished reply becomes `completed`, an error `failed`, a
user stop `cancelled`; text received so far is always kept. A reply that hits
`CHAT_MAX_OUTPUT_TOKENS` is still `completed`, with a note that it was cut.

A conversation has at most one `pending` reply. If the server dies mid-stream and a reply stays
`pending` for over 5 minutes, opening, continuing or deleting the conversation marks it `failed`.
Another user's conversation UUID returns `404`, so its existence is not revealed.

## Error format

Every HTTP error uses one envelope:

```json
{
  "error": {
    "code": "EMAIL_TAKEN",
    "message": "Email này đã được sử dụng.",
    "fields": { "email": "Email đã tồn tại." }
  }
}
```

`fields` only appears for errors tied to form inputs. `message` is always Vietnamese and safe to show;
the frontend translates by `code` (`frontend/src/i18n/errors.js`). A new code goes into both locale
files.

| Status | Code                                | When                                                                |
| ------ | ----------------------------------- | ------------------------------------------------------------------- |
| `400`  | `OTP_INVALID`, `OTP_EXPIRED`        | Wrong or expired email code / proof.                                |
| `401`  | `UNAUTHENTICATED`                   | Missing, invalid or expired session, or deactivated account.        |
| `401`  | `INVALID_CREDENTIALS`               | Wrong identifier or password.                                       |
| `401`  | `GOOGLE_AUTH_FAILED`                | Google sign-in was refused or could not be checked.                 |
| `403`  | `FORBIDDEN`                         | Role not allowed.                                                   |
| `403`  | `EMAIL_NOT_VERIFIED`                | Registration without a valid email proof.                           |
| `404`  | `CONVERSATION_NOT_FOUND`            | Unknown conversation or one owned by another user.                  |
| `404`  | `USER_NOT_FOUND`, `NOT_FOUND`       | Unknown user (admin) or route.                                      |
| `405`  | `METHOD_NOT_ALLOWED`                | Wrong HTTP method.                                                  |
| `409`  | `EMAIL_TAKEN`, `USERNAME_TAKEN`     | Already registered.                                                 |
| `409`  | `REGISTRATION_CONFLICT`             | Duplicate caught by the database during registration.               |
| `409`  | `CHAT_IN_PROGRESS`                  | The conversation still has a `pending` reply.                       |
| `409`  | `CANNOT_MODIFY_SELF`                | An admin tried to change their own role or status.                  |
| `409`  | `GOOGLE_ALREADY_LINKED`, `GOOGLE_ACCOUNT_TAKEN` | Google account already linked here or to another user.  |
| `409`  | `GOOGLE_EMAIL_NEEDS_PASSWORD_LOGIN` | The Google email belongs to a password account; sign in first.      |
| `422`  | `VALIDATION_ERROR`                  | Malformed payload; always has `fields`.                             |
| `429`  | `AUTH_RATE_LIMITED`                 | Too many failed logins.                                             |
| `429`  | `REGISTER_RATE_LIMITED`             | Too many registrations from one address.                            |
| `429`  | `OTP_RATE_LIMITED`, `OTP_VERIFY_RATE_LIMITED`, `OTP_TOO_MANY_ATTEMPTS` | Too many code requests or checks. |
| `429`  | `CHAT_RATE_LIMITED`                 | Over `CHAT_RATE_LIMIT_PER_MINUTE`.                                  |
| `429`  | `CHAT_DAILY_LIMIT_REACHED`          | Over `CHAT_DAILY_MESSAGE_LIMIT` for the UTC day.                    |
| `502`  | `EMAIL_SEND_FAILED`                 | The SMTP server refused the message.                                |
| `503`  | `EMAIL_NOT_CONFIGURED`, `GOOGLE_NOT_CONFIGURED` | SMTP or Google sign-in is not configured.               |

On `/api/chat/messages/stream` all of these happen **before** the stream opens, so the client sees
the real status. Once the stream is open the status is fixed at `200` and errors arrive as an
`error` event: `CHAT_NOT_CONFIGURED` (no retry) or `CHAT_PROVIDER_UNAVAILABLE` (retry possible).

## Database and security

```text
users 1 ── n conversations 1 ── n messages
  ├── 1 ── n chat_usage_events
  ├── 1 ── n refresh_tokens
  └── 1 ── n oauth_identities
email_otps (keyed by email, not by user)
```

- Deleting a user cascades to conversations, messages, usage events, tokens and identities.
- Deleting a conversation cascades to its messages but keeps the usage ledger, so limits are not
  reset.
- `messages.role` is `user|assistant`; `messages.status` is `pending|completed|failed|cancelled`.
- Provider, model and token usage are stored per assistant message.
- Every conversation query filters by `current_user.id`.
- On Supabase, RLS is on and `anon` / `authenticated` are revoked on application tables.
- API keys use `SecretStr` and are never logged. Prompts and conversation text are never written to
  the application log; SQL errors hide bound parameters.

## AI and RAG

```text
RAG_ENABLED=false  chat service → NullRetriever                        → ModelProvider (no sources)
RAG_ENABLED=true   chat service → [planner] → QdrantRetriever → [rerank] → [gate] → ModelProvider
```

`get_retriever()` in `app/services/chat/retriever.py` is the only place RAG plugs in; the stream code
does not change. The retrieval query is the last user message, prefixed with the previous question
when the last one has 8 words or fewer (a follow-up like "còn trường hợp khác?").

With no sources, the system prompt forbids inventing document numbers, articles or effective
dates. With sources, each passage goes into the prompt as `<reference id="n">` and the model must
write `[n]` after each claim. Only sources actually cited are returned and stored in
`messages.citations` (a snapshot, so reloading shows the same sources). Unknown numbers are dropped;
`[1, 2]`, `[1; 2]` and ranges like `[1-3]` are understood. If Qdrant, embedding or retriever setup
fails while RAG is on, chat still works but uses the "no source" rules, so the model never answers a
legal question from memory because retrieval broke.

Timeouts: chat provider 60 s, query embedding 15 s, planner and reranker 8 s each.

### Corpus and index

- `corpus/` is the source of truth: `manifest.json` (maintained by a person), `raw/` (downloaded
  files), `texts/` (extracted text) and `vbpl/` (the larger set, see below). Qdrant is a derived
  index that can be deleted and rebuilt.
- `status`, `effective_from` and `effective_to` in the manifest are filled by a person after checking
  the official source, never inferred. With `RAG_REQUIRE_IN_FORCE=true`, only `in_force` documents
  are returned. The manifest has 23 documents; 21 are indexed.
- `truncated: true` marks a partial download; `ingest: false` keeps a file out of the index (for
  example the base Labour Code 45/2019 and VAT Law 48/2024, replaced by their consolidated texts).
  Appendices and forms are not indexed.
- Chunk sets: `article` (one Điều, split by Khoản when long), `article_s256` (smaller pieces for
  256-token models), `fixed` (fixed windows, experiments only) and `vbpl` (imported documents). Each
  chunk set and embedding model has its own collection, `legal_<chunk_set>_<model>`.

From `backend/` (start Qdrant with `scripts/start-qdrant.ps1`, needs Docker Desktop):

```powershell
.\.venv\Scripts\python.exe -m pip install -c constraints.txt -e ".[corpus]"   # PDF support
.\.venv\Scripts\python.exe scripts\corpus_extract_text.py                     # raw/ → texts/
.\.venv\Scripts\python.exe scripts\corpus_report.py                           # parser check, exit 1 on errors
.\.venv\Scripts\python.exe scripts\corpus_ingest.py --chunk-set article --dry-run
.\.venv\Scripts\python.exe scripts\corpus_ingest.py --chunk-set article
.\.venv\Scripts\python.exe scripts\corpus_backfill_sparse.py --chunk-set article  # rebuild sparse vectors only
.\.venv\Scripts\python.exe scripts\corpus_review_sheets.py                    # human checklists → plans/reports/
```

`corpus_ingest.py` can be rerun: it only embeds new chunks or changed headings, updates `status`
without re-embedding, and deletes old points of edited or excluded documents. The token limits in
chunking are under-estimates; the ingest command prints the real counts.

Retrieval options:

- `RAG_RETRIEVAL_MODE=hybrid` fuses dense and sparse results with RRF (k = 60); ties break by dense
  rank.
- `RAG_QUERY_PLANNER_MODEL` rewrites the question into up to 2 extra queries; the original is always
  searched and results are fused with RRF. On failure only the original is searched. Adds one model
  call per question.
- `RAG_RERANK_MODEL` reorders the candidates with the Cohere Rerank API (`/v2/rerank`, needs
  `COHERE_API_KEY`); on an API error or timeout the fused order is kept and counted as
  `rerank_fallbacks` in eval results. Without the key RAG does not start (chat answers with no sources).
- `RAG_MIN_TOP_SCORE` returns "no source" when the original question's best dense cosine is below
  the threshold. A question with no Vietnamese letters (English, or Vietnamese typed without marks)
  is searched by the planner's Vietnamese rewrites only, and the gate and the reranker judge the
  first of them: cross-lingual cosine is far lower (English ~0.4 vs Vietnamese ~0.65 for the same
  question), so the English text would always be gated, and its own hits crowd out the right ones.
  Without the planner or a Vietnamese rewrite, the question is searched as written. The answer
  follows the question's language and keeps document, article and clause numbers as in the sources.
- `RAG_EXPAND_ARTICLES` (small-to-big): a long Điều is indexed as an intro plus one chunk per
  Khoản, so search matches a precise Khoản; after rerank each source becomes its whole Điều
  (all its chunks in order, kept as the Khoản when over 3000 tokens) and later chunks of the same
  Điều are dropped, so the reranker returns spare candidates.

### The `vbpl` set

`corpus/vbpl/` is committed, so the index of the evaluated app can be rebuilt without the original
dataset. `.gitattributes` stops git from changing line endings there, because the manifests hash the
texts and chunk ids depend on their bytes.

```powershell
.\.venv\Scripts\python.exe scripts\corpus_ingest.py --chunk-set vbpl --extra-manifest corpus/vbpl/manifest.json --extra-manifest corpus/vbpl/manual/manifest.json
```

Then set `RAG_CHUNK_SET=vbpl`. This indexes 323 documents (13,733 chunks) and calls the embedding
API. `--extra-manifest` is repeatable; a full run without `corpus/vbpl/manifest.json` is refused,
because it would delete everything imported.

`scripts/corpus_import_vbpl.py` (extra `corpus`) made the imported part from the dataset
[th1nhng0/vietnamese-legal-documents](https://huggingface.co/datasets/th1nhng0/vietnamese-legal-documents)
(revision `8977887`, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)); the texts are plain
text extracted from the dataset's HTML. It takes the dataset's `metadata` and `content` parquet files
and an inventory CSV (`tier`, `fields`, `id`): only `A_core` rows are imported, documents already in
`corpus/manifest.json` are skipped, and each document gets the field `tax`, `enterprise` or `labor`
from its inventory tags. Amending documents are kept and marked in `notes`. Documents whose dataset
copy is missing or broken are added by hand from Công báo files in `corpus/vbpl/manual/` (own
`manifest.json`, `raw/`, `texts/`; the import never touches it).

`corpus/vbpl/selection/` records which documents were chosen and dropped: `inventory.csv` (every
candidate with its tier; the import input), `expiry-findings.csv` and `parent-findings.csv` (what the
scans of effect clauses and of parent laws found, with the decision taken) and `import-skipped.csv`
(documents not imported). The status of these documents comes from a snapshot of the vbpl portal and
those scans, and has not been checked by a person.

### Evaluation

```powershell
.\.venv\Scripts\python.exe scripts\eval_generate.py        # write questions (status pending)
.\.venv\Scripts\python.exe scripts\eval_review.py          # human review: a/r/e/s/q
.\.venv\Scripts\python.exe scripts\eval_run.py rag_eval/configs/retrieval/hybrid-article.json --split dev
.\.venv\Scripts\python.exe scripts\eval_judge_answers.py rag_eval/results/<file>.json --model <id>
.\.venv\Scripts\python.exe scripts\eval_faithfulness.py rag_eval/results/<file>.json --model <id>
.\.venv\Scripts\python.exe scripts\eval_export_results.py  # rag_eval/results/SUMMARY.md + CSV
.\.venv\Scripts\python.exe scripts\eval_compare.py rag_eval/results/A.json rag_eval/results/B.json
```

Configs live in `rag_eval/configs/`, split by `tier`: `retrieval/` (measures search) and
`generation/` (measures answers). Results are written to `rag_eval/results/`.

- **Questions**: only `approved` questions are scored. `--provisional` also scores unreviewed ones
  for tuning; those results are marked `provisional` and are not thesis numbers.
  `eval_generate.py --multi N` adds multi-part questions as `pending` and never overwrites reviewed
  ones.
- **Splits**: each approved question has a fixed `split` (`dev` or `test`), balanced by field ×
  question type and assigned by `eval_review.py`. Tune parameters on `--split dev`; take thesis
  numbers from `--split test`. Questions written after parameters were fixed can be set by hand to
  `"split": "holdout"`; only `--split holdout` scores them. Without `--split`, everything except
  `holdout` is scored. Result files get a `-dev` / `-test` suffix.
- **Rate limits**: `eval_run.py ... --pause 7` runs one question at a time with a wait between
  them, e.g. for a Cohere trial key; the wait is not counted in latency. A rerank run is only valid
  when `rerank_fallbacks` is 0. Generation results from before 2026-11-28 ran 3 questions at once and
  did not record `rerank_fallbacks`.
- **Retrieval tier**: one query embedding per question (plus planner / rerank if on), scoring the
  same `top_k` passages the app receives. The metric is **Hit@k**: the share of questions with at
  least one gold article in the top k (older files call it `recall@k`); MRR is MRR@5.
- **Generation tier** calls the chat model and measures citation precision / recall, errors, cut
  answers, tokens and latency (end-to-end includes planner and rerank), plus:
  - `unsupported ref`: a document number or article not in the retrieved passages or the question.
    This is **not** a hallucination rate (real documents outside the passages count too); empty for
    no-RAG runs.
  - `unknown doc`: a document number not in the corpus manifest; comparable between RAG and no-RAG.
  - `needs review`: an article tied to a law name without a number, which cannot be checked
    automatically.
  - `OOC refused (hand)`: refusal rate on out-of-corpus questions. Set `"refused"` to `true` /
    `false` on each `out_of_corpus` row of the result file, then rerun `eval_export_results.py`.
  - `eval_judge_answers.py` scores stored answers against `gold_answer` with a judge model (use a
    different model from the one that answered).
  - `eval_faithfulness.py` checks the claims of stored answers against the sources they were given,
    rebuilt from the Qdrant index; the corpus and retrieval code must be those of the run.
- **Baseline**: `langchain-baseline.json` runs a textbook RAG pipeline (LangChain
  `RecursiveCharacterTextSplitter` 1200/200 characters, dense only, in memory) against the same
  questions and article-level scoring. Needs the `eval-baseline` extra and one full corpus
  embedding through OpenAI; no Qdrant.
- **Comparison**: `eval_compare.py` reports a 95% bootstrap interval of the difference, McNemar's
  test for Hit@k and the questions whose rank changed. Treat a difference as real only when the
  interval excludes 0 and, for Hit@k, McNemar p < 0.05. It warns when the two files differ in
  `chunk_set`, `top_k`, corpus or gold. RRF sensitivity: `retrieval/hybrid-article-rrfk{20,40,100}.json`.

Each result file records the commit (`git_sha`, `git_dirty`), hashes of the manifest, texts and
questions, and the collection name. Only quote results with `git_dirty: false`. Results from before
2026-11-26 are in `rag_eval/results/superseded-261126/`: retrieval depth and scoring changed, so do
not quote them or compare them with new results. Comparing hallucination between two setups
requires reading and labelling the answers by hand.

### Privacy

User questions are sent to OpenAI for query embedding (when `EMBEDDING_PROVIDER=openai`) and to the
chat provider for the answer. The index only holds public legal texts.

## Tests

```powershell
cd D:\VieTaxLegal\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m ruff format --check app tests
```

Tests use in-memory SQLite, a fake chat provider and `QdrantClient(":memory:")`. They never call a
real database, Anthropic, OpenAI, Cohere or a Qdrant server, and cost nothing. `tests/conftest.py` disables
`backend/.env` during tests.

- `tests/test_*.py`: auth, sessions and roles, login throttle, password policy, email codes, Google
  sign-in, chat (stream, history, citations, prompt, provider, stream failures), config and request
  logging.
- `tests/rag/`: corpus manifest, text extraction, legal parser, chunking, ingest, vbpl import,
  embeddings, sparse / hybrid search, RRF fusion, Qdrant store and retriever, query planner and
  reranker.
- `tests/eval/`: dataset, metrics, runner, reference check, answer judge, comparison, export and the
  LangChain baseline.

CI (`.github/workflows/backend-quality.yml`) runs pytest, Ruff and the format check, then
`alembic upgrade head` and `alembic check` on Postgres 15.

## Troubleshooting

### Startup fails: `JWT_SECRET phải là một chuỗi ngẫu nhiên có ít nhất 32 ký tự`

`.env.example` ships the sample `replace-with-a-long-random-secret`. The backend refuses secrets
shorter than 32 characters and any secret starting with `replace-with-`. Generate a real one with the
command in step 1.

### Port 5000 busy or WinError 10013

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess
```

```powershell
Stop-Process -Id <PID> -Force
```

Then start Uvicorn again. Do not move to another port while the frontend still proxies to 5000.

### Database authentication failed

- Check the Supabase database password (reset in Project Settings → Database).
- URL-encode special characters in the password.
- Copy the Session pooler URL again; `sslmode=require` is added automatically.

### Health returns a database error

Check `DATABASE_URL`, the network, and whether the Supabase project is paused (the free tier pauses
after 7 days without activity; use **Restore project** in the Dashboard). Then run
`.\.venv\Scripts\python.exe -m alembic current`.

### Chat returns `CHAT_NOT_CONFIGURED`

The selected provider's API key is missing or still a placeholder. Fix `.env` and restart.

### Chat returns `CHAT_PROVIDER_UNAVAILABLE`

Check the API key, model ID, credit / billing, the network and the provider's status page. The
backend deliberately does not pass upstream error details to the frontend.

### Supabase shows RLS without policies

Intended. The frontend never uses the Supabase Data API; RLS plus revoking `anon` / `authenticated`
blocks direct access, and all data goes through FastAPI.
