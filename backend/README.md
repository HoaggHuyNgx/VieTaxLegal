# VieTaxLegal Backend

Backend FastAPI cung cấp xác thực tài khoản, quản lý phiên, lịch sử hội thoại và streaming câu trả
lời AI. Dữ liệu được lưu trong PostgreSQL; frontend chỉ giao tiếp qua API của backend.

## Thành phần chính

```text
app/
├── api/routes/           # health, auth và chat endpoints
├── core/                 # settings, JWT, cookie và error handlers
├── db/                   # SQLAlchemy engine/session
├── models/               # users, conversations, messages, usage events
├── schemas/              # Pydantic schemas
└── services/
    ├── auth.py           # đăng ký và đăng nhập
    ├── chat.py           # orchestration, rate limit và SSE
    ├── chat_provider.py  # Anthropic/OpenAI providers
    └── chat_retriever.py # Retriever interface; V1 dùng NullRetriever
```

## Yêu cầu

- Python 3.12 trở lên.
- Một project Supabase đang hoạt động (PostgreSQL do Supabase quản lý; không cài PostgreSQL trên máy).
- API key Anthropic hoặc OpenAI để gọi chat thật.

## 1. Kết nối database (Supabase)

1. Supabase Dashboard → **Connect** → tab **Direct** → **Connection Method: Session pooler**, Type `URI`,
   copy URL dạng `postgresql://postgres.<project-ref>:[YOUR-PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`.
   Không dùng *Direct connection* (chỉ IPv6, máy Windows thường không kết nối được) hay *Transaction pooler*
   (cổng 6543, không hợp với prepared statement của psycopg3).
2. Copy `.env.example` thành `.env`:

```powershell
cd D:\VieTaxLegal\backend
Copy-Item .env.example .env
notepad .env
```

3. Dán URL vào `DATABASE_URL`, thay `[YOUR-PASSWORD]` (bỏ cả dấu ngoặc) bằng DB password. Quên password thì
   reset ở **Project Settings → Database**.
4. Nếu password chứa `@`, `:`, `/`, `#` hoặc `%`, phải URL-encode password trước khi đặt vào URL
   (hoặc đặt password chỉ gồm chữ và số).
5. Tạo JWT secret:

```powershell
py -c "import secrets; print(secrets.token_urlsafe(48))"
```

Không gửi `.env`, database password, JWT secret hoặc API key lên chat và không commit chúng.

## 2. Biến môi trường

Chỉ hai biến sau là bắt buộc. Thiếu một trong hai thì backend không khởi động được:

| Biến           | Mô tả                                                            |
| -------------- | ---------------------------------------------------------------- |
| `DATABASE_URL` | URL kết nối PostgreSQL (`postgresql+psycopg://...`).             |
| `JWT_SECRET`   | Chuỗi ngẫu nhiên tối thiểu 32 ký tự; không được giữ giá trị mẫu. |

Backend tự chuẩn hóa `DATABASE_URL`: tiền tố `postgres://` hoặc `postgresql://` được đổi thành
`postgresql+psycopg://`. Nếu dùng PostgreSQL Supabase (host chứa `supabase.com`), `sslmode=require`
được thêm tự động khi URL chưa có.

Các biến còn lại đều có giá trị mặc định, chỉ đặt khi muốn đổi:

| Biến                         | Mặc định                | Mô tả                                                        |
| ---------------------------- | ----------------------- | ------------------------------------------------------------ |
| `APP_ENV`                    | `development`           | `production` bật thêm cookie `Secure`.                       |
| `SESSION_COOKIE_NAME`        | `vietaxlegal_session`   | Tên cookie phiên.                                            |
| `SESSION_TOKEN_HOURS`        | `24`                    | Hạn token khi đăng nhập không chọn ghi nhớ.                  |
| `REMEMBER_ME_DAYS`           | `30`                    | Hạn token và cookie khi đăng nhập với `rememberMe: true`.    |
| `JWT_ALGORITHM`              | `HS256`                 | Thuật toán ký JWT.                                           |
| `CORS_ORIGINS`               | `http://localhost:3000` | Danh sách origin phân tách bằng dấu phẩy; không dùng `*`.    |
| `CHAT_PROVIDER`              | `anthropic`             | `anthropic` hoặc `openai`.                                   |
| `CHAT_MODEL`                 | `claude-sonnet-5`       | Model ID tương ứng với provider đang chọn.                   |
| `ANTHROPIC_API_KEY`          | trống                   | Cần khi `CHAT_PROVIDER=anthropic`, nếu không chat sẽ báo lỗi. |
| `OPENAI_API_KEY`             | trống                   | Cần khi `CHAT_PROVIDER=openai`, nếu không chat sẽ báo lỗi.   |
| `CHAT_MAX_OUTPUT_TOKENS`     | `1500`                  | Token đầu ra tối đa; chỉ chấp nhận `1–8192`.                 |
| `CHAT_HISTORY_MESSAGES`      | `20`                    | Số message gần nhất gửi lại model; chỉ chấp nhận `1–100`.    |
| `CHAT_RATE_LIMIT_PER_MINUTE` | `10`                    | Số câu hỏi tối đa mỗi người dùng trong một phút.             |
| `CHAT_DAILY_MESSAGE_LIMIT`   | `100`                   | Số câu hỏi tối đa mỗi người dùng trong một ngày UTC.         |
| `RAG_ENABLED`                | `false`                 | Bật truy xuất RAG vào chat (cần Qdrant đã ingest).           |
| `RAG_RETRIEVAL_MODE`         | `hybrid`                | `dense`, `sparse` hoặc `hybrid` (xem phần AI và RAG).        |
| `RAG_REQUIRE_IN_FORCE`       | `true`                  | Chỉ trả văn bản `status = in_force`; `false` chỉ để dev.     |
| `EMBEDDING_PROVIDER`         | `openai`                | `openai`, `bkai` (extra `local-embed`) hoặc `fake` (test).   |
| `EMBEDDING_MODEL`            | `text-embedding-3-small` | Model nhúng; tên collection Qdrant suy ra từ model này.     |
| `EMBEDDING_DIMENSIONS`       | trống                   | Chỉ OpenAI: rút ngắn vector; trống = mặc định của model.     |
| `EMBEDDING_BATCH_SIZE`       | `64`                    | Số chunk mỗi lần gọi nhúng (`1–512`).                        |
| `EVAL_GENERATOR_MODEL`       | trống                   | Model sinh câu hỏi đánh giá; trống = `CHAT_MODEL`.           |
| `RAG_CHUNK_SET`              | `article`               | Cách chia chunk; chỉ `a-z`, `0-9`, `_` (tối đa 32 ký tự).   |
| `RAG_TOP_K`                  | `5`                     | Số đoạn luật lấy về; chỉ chấp nhận `1–50`.                   |
| `RAG_MIN_SIMILARITY`         | `0`                     | Ngưỡng cosine tối thiểu `0–1`; `0` là giữ tất cả.            |
| `QDRANT_URL`                 | `http://127.0.0.1:6333` | Địa chỉ Qdrant (`http://` hoặc `https://`).                  |
| `QDRANT_API_KEY`             | trống                   | Chỉ đặt khi dùng Qdrant ngoài máy local.                     |
| `LOGIN_MAX_FAILED_ATTEMPTS`  | `5`                     | Số lần đăng nhập sai tối đa trước khi bị khóa tạm thời.      |
| `LOGIN_ATTEMPT_WINDOW_MINUTES` | `15`                  | Khung thời gian (phút) dùng để đếm số lần đăng nhập sai.     |

Ngoài `CHAT_HISTORY_MESSAGES`, lịch sử gửi lại model còn bị chặn bởi hằng số
`MAX_HISTORY_CHARACTERS` (40.000 ký tự) trong `app/services/chat.py`. Hội thoại có nội dung dài
sẽ bị cắt sớm hơn số message đã cấu hình.

Ví dụ Anthropic:

```env
CHAT_PROVIDER=anthropic
CHAT_MODEL=claude-sonnet-5
ANTHROPIC_API_KEY=sk-ant-...
```

Ví dụ OpenAI:

```env
CHAT_PROVIDER=openai
CHAT_MODEL=gpt-6-luna
OPENAI_API_KEY=sk-...
```

Chỉ API key của provider được chọn là bắt buộc. Đổi provider không làm thay đổi route hoặc định
dạng SSE mà frontend đang sử dụng.

## 3. Cài dependencies

```powershell
cd D:\VieTaxLegal\backend
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -c constraints.txt -e ".[dev]"
```

`constraints.txt` ghim phiên bản đã được kiểm thử của mọi package để mỗi lần cài cho kết quả giống
nhau (CI cũng dùng file này). Sau khi nâng package có chủ đích, tạo lại file bằng
`.\.venv\Scripts\python.exe -m pip freeze --exclude-editable`.

Công cụ xử lý kho văn bản (`scripts/extract_corpus_text.py`, `scripts/corpus_report.py`) cần thêm
`pymupdf` để đọc PDF: `.\.venv\Scripts\python.exe -m pip install -e ".[corpus]"`. App và CI không cần gói này.

Không cần kích hoạt virtualenv nếu luôn gọi Python bằng đường dẫn
`.\.venv\Scripts\python.exe`.

## 4. Migration

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m alembic current
```

Migration hiện tại:

| Revision                       | Nội dung                                                                 |
| ------------------------------ | ------------------------------------------------------------------------ |
| `0001_create_users`            | Tạo bảng users và unique index cho email/username.                       |
| `0002_lock_down_public_tables` | Chỉ trên Supabase: bật RLS và khóa users/alembic_version khỏi Data API.  |
| `0003_chat`                    | Tạo conversations, messages, chat_usage_events, index và ràng buộc chat. |
| `0004_message_citations`       | Thêm cột `messages.citations` (JSON, nullable) lưu nguồn trích dẫn.      |
| `0005_roles_refresh_tokens`    | Thêm `users.role` (user/admin) và bảng `refresh_tokens`.                 |
| `0006_oauth_identities`        | Thêm bảng `oauth_identities` (Google); `users.password_hash` cho phép null. |
| `0007_email_otps`              | Thêm bảng `email_otps` (mã xác minh email trước khi đăng ký).             |

Kết quả `alembic current` phải chứa `0007_email_otps (head)`. Database sẽ có các bảng `users`,
`conversations`, `messages`, `chat_usage_events`, `refresh_tokens`, `oauth_identities`, `email_otps` và `alembic_version`.

Phần RLS/REVOKE của migration 0002 và 0003 chỉ chạy khi cả hai role `anon` và `authenticated` tồn
tại (tức là trên Supabase). Trên PostgreSQL thường, các bước đó được bỏ qua.

Supabase Auth không được dùng trong kiến trúc này. Bảng `users` và phiên FastAPI là nguồn xác thực
duy nhất.

## 5. Chạy API

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
```

Giữ terminal này mở. Khi thấy `Application startup complete`, kiểm tra:

- Health: <http://127.0.0.1:5000/api/health>
- Swagger UI: <http://127.0.0.1:5000/docs>
- OpenAPI JSON: <http://127.0.0.1:5000/openapi.json>

Health thành công:

```json
{
  "status": "ok",
  "database": "ok"
}
```

## API xác thực

| Method | Endpoint             | Mô tả                               |
| ------ | -------------------- | ----------------------------------- |
| `POST` | `/api/auth/register` | Tạo tài khoản và đặt cookie phiên.  |
| `POST` | `/api/auth/login`    | Đăng nhập bằng email hoặc username. |
| `POST` | `/api/auth/logout`   | Xóa cookie phiên.                   |
| `GET`  | `/api/auth/me`       | Lấy người dùng hiện tại.            |

Payload đăng ký:

```json
{
  "email": "huy@example.com",
  "username": "huy_legal",
  "fullName": "Hoàng Huy",
  "phone": "0901234567",
  "password": "Mat-khau-an-toan-2026!",
  "acceptTerms": true
}
```

Payload đăng nhập:

```json
{
  "identifier": "huy@example.com",
  "password": "Mat-khau-an-toan-2026!",
  "rememberMe": false
}
```

Đăng nhập sai liên tiếp bị giới hạn theo cặp (địa chỉ client, email/username): quá
`LOGIN_MAX_FAILED_ATTEMPTS` lần sai trong `LOGIN_ATTEMPT_WINDOW_MINUTES` phút thì `/api/auth/login`
trả `429 AUTH_RATE_LIMITED`, kể cả khi mật khẩu đúng, cho đến khi hết khung thời gian. Đăng nhập
thành công xóa bộ đếm. Bộ đếm nằm trong bộ nhớ của tiến trình nên được đặt lại khi khởi động lại
server và không chia sẻ giữa nhiều worker. Phía sau reverse proxy, mọi client có thể dùng chung
một địa chỉ; cần xử lý lại khi triển khai thật.

Cookie phiên có `HttpOnly`, `SameSite=Lax` và `Path=/`. Khi `APP_ENV=production`, cookie có thêm
`Secure`.

## API chat

Tất cả chat endpoints yêu cầu cookie đăng nhập.

| Method   | Endpoint                           | Mô tả                                                |
| -------- | ---------------------------------- | ---------------------------------------------------- |
| `GET`    | `/api/chat/conversations?limit=50` | Danh sách hội thoại mới nhất trước.                  |
| `GET`    | `/api/chat/conversations/{id}`     | Metadata và messages của hội thoại thuộc người dùng. |
| `DELETE` | `/api/chat/conversations/{id}`     | Xóa hội thoại và cascade messages.                   |
| `POST`   | `/api/chat/messages/stream`        | Gửi câu hỏi và nhận SSE stream.                      |

`limit` nhận giá trị từ `1` đến `50`, mặc định `50`. `DELETE` trả `204` khi thành công, nhưng trả
`409 CHAT_IN_PROGRESS` nếu hội thoại còn assistant message đang `pending`; client phải dừng stream
trước khi xóa.

Payload tạo chat mới:

```json
{
  "conversationId": null,
  "content": "Điều kiện khấu trừ thuế GTGT là gì?"
}
```

Để gửi tiếp vào hội thoại cũ, truyền UUID vào `conversationId`. Nội dung câu hỏi phải có từ 1 đến
4.000 ký tự.

### SSE events

| Event   | Nội dung                                                        |
| ------- | --------------------------------------------------------------- |
| `meta`  | Conversation, user message và assistant message đang `pending`. |
| `delta` | Phần text mới nhận từ model.                                    |
| `done`  | Assistant message hoàn chỉnh, token usage và citations.         |
| `error` | Mã lỗi an toàn, thông báo và khả năng retry.                    |

Backend lưu user message và assistant `pending` trước khi gọi AI. Khi stream hoàn thành, trạng thái
chuyển thành `completed`; lỗi thành `failed`; người dùng dừng stream thành `cancelled`. Phần nội
dung đã nhận vẫn được lưu.

Mỗi hội thoại chỉ có tối đa một assistant message `pending`. Nếu stream bị ngắt đột ngột (server
chết) khiến một message kẹt ở `pending` hơn 5 phút, lần gửi tiếp theo hoặc lần xóa hội thoại sẽ tự
đánh dấu nó là `failed` để hội thoại không bị khóa. Truy cập UUID hội thoại của người khác
trả `404` để không tiết lộ tài nguyên có tồn tại hay không.

## Định dạng lỗi

Mọi lỗi HTTP đều dùng chung một envelope. Không có route nào trả lỗi ở định dạng khác:

```json
{
  "error": {
    "code": "EMAIL_TAKEN",
    "message": "Email này đã được sử dụng.",
    "fields": { "email": "Email đã tồn tại." }
  }
}
```

`fields` chỉ xuất hiện với lỗi gắn với từng ô nhập liệu. `message` luôn là tiếng Việt và an toàn để
hiển thị trực tiếp cho người dùng.

| Status | Code                       | Khi nào xảy ra                                              |
| ------ | -------------------------- | ----------------------------------------------------------- |
| `401`  | `UNAUTHENTICATED`          | Thiếu cookie phiên, hoặc phiên sai/hết hạn/tài khoản bị khóa. |
| `401`  | `INVALID_CREDENTIALS`      | Sai email/username hoặc mật khẩu khi đăng nhập.              |
| `404`  | `CONVERSATION_NOT_FOUND`   | UUID hội thoại không tồn tại hoặc thuộc người dùng khác.     |
| `409`  | `EMAIL_TAKEN`              | Email đã được đăng ký.                                       |
| `409`  | `USERNAME_TAKEN`           | Username đã được đăng ký.                                    |
| `409`  | `REGISTRATION_CONFLICT`    | Trùng dữ liệu phát hiện ở tầng database khi đăng ký.         |
| `409`  | `CHAT_IN_PROGRESS`         | Hội thoại còn assistant message `pending`.                   |
| `422`  | `VALIDATION_ERROR`         | Payload sai định dạng; luôn kèm `fields`.                    |
| `429`  | `CHAT_RATE_LIMITED`        | Vượt `CHAT_RATE_LIMIT_PER_MINUTE`.                           |
| `429`  | `CHAT_DAILY_LIMIT_REACHED` | Vượt `CHAT_DAILY_MESSAGE_LIMIT` trong ngày UTC.              |
| `429`  | `AUTH_RATE_LIMITED`        | Đăng nhập sai quá `LOGIN_MAX_FAILED_ATTEMPTS` lần trong khung thời gian. |

Riêng `/api/chat/messages/stream`: mọi lỗi trên đều xảy ra **trước** khi SSE bắt đầu, nên client vẫn
đọc được status code thật. Sau khi stream đã mở, status bị ghim ở `200` và lỗi chỉ còn được báo qua
event `error` in-band với hai mã `CHAT_NOT_CONFIGURED` (không retry được) và
`CHAT_PROVIDER_UNAVAILABLE` (retry được).

## Database và bảo mật

Quan hệ hiện tại:

```text
users 1 ── n conversations 1 ── n messages
  └── 1 ── n chat_usage_events
```

- Xóa user cascade conversations, messages và usage events.
- Xóa conversation cascade messages nhưng giữ usage ledger để rate limit không bị reset.
- `messages.role` chỉ nhận `user|assistant`.
- `messages.status` chỉ nhận `pending|completed|failed|cancelled`.
- `provider`, `model` và token usage được lưu theo assistant message.
- Frontend không bao giờ kết nối database; mọi dữ liệu đi qua FastAPI.
- Nếu chạy trên Supabase, RLS được bật và quyền `anon`, `authenticated` bị thu hồi trên các bảng
  ứng dụng (xem migration 0002, 0003).
- Backend luôn lọc conversation theo `current_user.id`.
- API key AI dùng `SecretStr` và không được log.
- Prompt và nội dung hội thoại không được ghi vào application log.

## AI và RAG

Luồng chat:

```text
RAG_ENABLED=false  ChatOrchestrator → NullRetriever   → ModelProvider   (không nguồn)
RAG_ENABLED=true   ChatOrchestrator → QdrantRetriever → ModelProvider   (có nguồn)
```

Khi không có nguồn, system prompt yêu cầu model không bịa số hiệu, điều khoản hoặc hiệu lực văn
bản. Khi có nguồn, mỗi đoạn được đưa vào prompt trong thẻ `<reference id="n">`; model được yêu cầu
ghi `[n]` sau mỗi nhận định. Chỉ những nguồn thực sự được trích `[n]` mới được trả về và lưu vào
`messages.citations` (ảnh chụp tại thời điểm trả lời, nên nạp lại sẽ giữ nguyên). Số `[n]` không
tồn tại bị bỏ qua. Nếu Qdrant hoặc embedding lỗi, retriever trả kết quả rỗng và chat vẫn chạy.

### Kho văn bản và chỉ mục

- Nguồn gốc dữ liệu là `corpus/` trong git: `manifest.json` (do con người duy trì), `raw/` (file
  tải về) và `texts/` (văn bản đã trích xuất). Qdrant chỉ là chỉ mục dẫn xuất, xóa đi dựng lại được.
- `status`, `effective_from`, `effective_to` trong manifest do con người điền sau khi kiểm tra
  nguồn chính thức, không bao giờ tự suy ra. Với `RAG_REQUIRE_IN_FORCE=true` (mặc định) chỉ văn bản
  `in_force` được truy xuất; khi chưa điền thì không có nguồn nào được trả về.
- `truncated: true` đánh dấu file tải về chỉ là một phần văn bản; `ingest: false` loại file khỏi
  chỉ mục. Phụ lục/biểu mẫu không được lập chỉ mục.
- Ba bộ chunk: `article` (mỗi Điều, tách theo Khoản khi dài), `article_s256` (cắt nhỏ cho model 256
  token) và `fixed` (cửa sổ cố định, dùng cho thí nghiệm). Mỗi bộ + mỗi model embedding là một
  collection riêng `legal_<chunk_set>_<model>`.

Chạy từ thư mục `backend` (Qdrant: `scripts/start-qdrant.ps1`, cần Docker Desktop):

```powershell
pip install -e ".[corpus]"                                   # chỉ cần để đọc PDF
.\.venv\Scripts\python.exe scripts\extract_corpus_text.py    # raw/ → texts/
.\.venv\Scripts\python.exe scripts\corpus_report.py          # kiểm tra parser, thoát 1 nếu có lỗi
.\.venv\Scripts\python.exe scripts\ingest_corpus.py --chunk-set article --dry-run
.\.venv\Scripts\python.exe scripts\ingest_corpus.py --chunk-set article
.\.venv\Scripts\python.exe scripts\backfill_sparse.py --chunk-set article   # chỉ khi cần dựng lại sparse
```

`ingest_corpus.py` chạy lại được nhiều lần: chỉ nhúng chunk mới, cập nhật `status` mà không nhúng
lại, và xóa điểm cũ của văn bản đã sửa. Biến môi trường liên quan nằm trong `.env.example`
(`RAG_*`, `QDRANT_*`, `EMBEDDING_*`, `EVAL_GENERATOR_MODEL`). `RAG_RETRIEVAL_MODE` nhận `dense`,
`sparse` hoặc `hybrid` (dense + sparse hợp nhất bằng RRF, hòa điểm được phá theo thứ hạng dense).

### Đánh giá

```powershell
.\.venv\Scripts\python.exe scripts\eval_generate.py          # sinh câu hỏi (trạng thái pending)
.\.venv\Scripts\python.exe scripts\eval_review.py            # con người duyệt: a/r/e/s/q
.\.venv\Scripts\python.exe scripts\run_eval.py rag_eval/configs/hybrid-article.json
.\.venv\Scripts\python.exe scripts\export_results.py         # rag_eval/results/SUMMARY.md + CSV
```

Chỉ câu hỏi `approved` được chấm; `--provisional` chấm cả câu chưa duyệt để chỉnh tham số và kết
quả được đánh dấu `provisional`, không dùng làm số liệu trong luận văn. Tầng `retrieval` chỉ tốn
một lần nhúng truy vấn; tầng `generation` gọi model chat (đo citation precision/recall, tham chiếu
bịa, từ chối câu ngoài phạm vi, độ trễ và token).

### Quyền riêng tư

Câu hỏi của người dùng được gửi tới OpenAI để nhúng truy vấn (khi `EMBEDDING_PROVIDER=openai`) và
để sinh câu trả lời. Dữ liệu chỉ mục là văn bản pháp luật công khai. Dùng `EMBEDDING_PROVIDER=bkai`
(extra `.[local-embed]`) để nhúng truy vấn ngay trên máy; câu hỏi vẫn tới model chat khi trả lời.

## Kiểm thử

```powershell
cd D:\VieTaxLegal\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app tests
.\.venv\Scripts\python.exe -m ruff format --check app tests
```

Tests sử dụng SQLite trong bộ nhớ và fake provider. Chúng không gọi database thật, Anthropic hoặc
OpenAI và không phát sinh chi phí API.

Các nhóm test bao gồm:

- `test_auth.py` — đăng ký, đăng nhập, đăng xuất, cookie phiên, ghi nhớ đăng nhập, validation và
  tài khoản không hoạt động.
- `test_chat.py` — tạo, stream, lưu, mở và xóa hội thoại; ownership isolation; dừng stream và lưu
  partial content; rate limit theo phút/ngày; giới hạn lịch sử.
- `test_chat_provider.py` — provider selection, lỗi thiếu API key và dịch stream của OpenAI.
- `test_config.py` — chuẩn hóa connection string, từ chối JWT secret yếu và CORS wildcard.

## Xử lý lỗi thường gặp

### Backend không khởi động: `JWT_SECRET phải là một chuỗi ngẫu nhiên có ít nhất 32 ký tự`

`.env.example` ship sẵn giá trị mẫu `replace-with-a-long-random-secret`. Backend từ chối cả secret
ngắn hơn 32 ký tự lẫn secret còn giữ tiền tố `replace-with-`, nên copy `.env.example` mà chỉ điền
`DATABASE_URL` sẽ không chạy được. Sinh secret thật bằng lệnh ở mục 1 rồi dán vào `.env`.

### Cổng 5000 bị chiếm hoặc WinError 10013

```powershell
Get-NetTCPConnection -LocalPort 5000 -State Listen |
    Select-Object LocalAddress, LocalPort, OwningProcess
Stop-Process -Id <PID> -Force
```

Sau đó chạy lại Uvicorn. Không đổi sang cổng khác nếu frontend vẫn proxy tới `5000`.

### Database authentication failed

- Kiểm tra DB password của project Supabase (reset được ở Project Settings → Database).
- URL-encode ký tự đặc biệt trong password.
- Copy lại Session pooler URL từ Dashboard; `sslmode=require` được thêm tự động.

### Health trả database error

Kiểm tra `DATABASE_URL`, kết nối mạng và project Supabase có đang bị pause không (free tier tự pause sau
7 ngày không hoạt động; vào Dashboard bấm **Restore project**). Chạy:

```powershell
.\.venv\Scripts\python.exe -m alembic current
```

### Chat trả `CHAT_NOT_CONFIGURED`

API key của provider được chọn đang thiếu hoặc vẫn là placeholder. Cập nhật `.env` rồi khởi động
lại backend.

### Chat trả `CHAT_PROVIDER_UNAVAILABLE`

Kiểm tra API key, model ID, credit/billing, kết nối mạng và trạng thái dịch vụ của provider. Backend
cố ý không gửi chi tiết lỗi upstream nhạy cảm xuống frontend.

### Supabase hiển thị RLS nhưng không có policy

Chỉ áp dụng khi chạy trên Supabase. Đây là cấu hình chủ ý: frontend không truy cập bảng bằng
Supabase Data API. RLS kết hợp với việc thu hồi quyền `anon`/`authenticated` khóa đường truy cập
trực tiếp; mọi dữ liệu đi qua FastAPI.
