# VieTaxLegal

Nền tảng hỗ trợ tra cứu pháp lý và thuế bằng tiếng Việt, gồm giao diện React và API FastAPI.
Phiên bản hiện tại đã hoàn thiện xác thực tài khoản và khu vực chat được bảo vệ.

## Công nghệ

- Frontend: React 18, Vite, React Router DOM
- Backend: Python 3.12+, FastAPI, Uvicorn
- Database: Supabase PostgreSQL, SQLAlchemy 2.0, Alembic, Psycopg
- Xác thực: Argon2 (`pwdlib`), JWT (`PyJWT`) và HTTP-only cookie
- Chất lượng: Pytest, Ruff, ESLint, Prettier và GitHub Actions

## Chạy frontend

```bash
cd frontend
npm install
npm run dev
```

## Cấu trúc frontend

```
src/
├── components/     # Reusable components
│   ├── Hero.jsx
│   ├── Features.jsx
│   ├── Process.jsx
│   ├── FAQ.jsx
│   └── Footer.jsx
├── pages/          # Page components
│   ├── LandingPage.jsx
│   └── ChatPage.jsx
├── styles/         # Global styles
└── App.jsx         # Main app component
```

## Routes frontend

- `/` - Landing page
- `/chat` - Chat interface (yêu cầu đăng nhập; dữ liệu chat hiện là minh họa)

## Kiểm tra frontend

- Dev server: `npm run dev` (http://localhost:3000)
- Build: `npm run build`
- Preview: `npm run preview`

## Backend và xác thực

Backend cung cấp đăng ký, đăng nhập, đăng xuất, kiểm tra phiên và health check. Frontend Vite
proxy `/api` tới FastAPI, nên cookie phiên được sử dụng trực tiếp trong quá trình phát triển.

```text
Browser → React/Vite (localhost:3000) → /api proxy → FastAPI (localhost:5000) → Supabase PostgreSQL
```

### Kết nối backend với Supabase

Yêu cầu: Python 3.12+ và một Supabase project. Project đã có sẵn database `postgres`, không cần
tạo thêm database `vietaxlegal`.

```powershell
cd D:\VieTaxLegal\backend
Copy-Item .env.example .env
```

Trong Supabase Dashboard, chọn **Connect** và sao chép chuỗi **Session pooler** cổng `5432`.
Mở `backend/.env`, điền project ref, pooler host và database password theo mẫu. Sau đó tạo JWT
secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Dán secret vào `JWT_SECRET`, rồi cài dependencies, migration và chạy API:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 5000
```

API chạy tại `http://localhost:5000`; tài liệu OpenAPI ở `http://localhost:5000/docs`.

### Biến môi trường backend

| Biến | Mô tả |
| --- | --- |
| `APP_ENV` | `development` hoặc `production`; production bật cookie `Secure`. |
| `DATABASE_URL` | Chuỗi Session pooler Supabase dùng `postgresql+psycopg://...` và `sslmode=require`. |
| `JWT_SECRET` | Chuỗi ngẫu nhiên ít nhất 32 ký tự. |
| `SESSION_COOKIE_NAME` | Tên cookie phiên; mặc định `vietaxlegal_session`. |
| `CORS_ORIGINS` | Các origin frontend, phân tách bằng dấu phẩy; không dùng `*`. |

### API xác thực

| Method | Endpoint | Mô tả |
| --- | --- | --- |
| `GET` | `/api/health` | Kiểm tra API và database. |
| `POST` | `/api/auth/register` | Tạo tài khoản và bắt đầu phiên đăng nhập. |
| `POST` | `/api/auth/login` | Đăng nhập bằng email hoặc tên tài khoản. |
| `POST` | `/api/auth/logout` | Xóa cookie phiên hiện tại. |
| `GET` | `/api/auth/me` | Lấy người dùng đang đăng nhập. |

Ví dụ payload đăng ký:

```json
{
  "email": "huy@example.com",
  "username": "huy_legal",
  "fullName": "Hoàng Huy",
  "phone": "0901234567",
  "password": "mat-khau-an-toan",
  "acceptTerms": true
}
```

### Kiểm tra backend

```powershell
cd D:\VieTaxLegal\backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check app tests
```

Test backend dùng SQLite trong bộ nhớ và không tác động tới Supabase. GitHub Actions chạy
test và lint khi có thay đổi trong `backend/`.

## Bảo mật và phạm vi

- Mật khẩu được băm bằng Argon2, không lưu plaintext.
- Phiên là JWT trong cookie HTTP-only, `SameSite=Lax`; production có thêm cờ `Secure`.
- JWT secret yếu và CORS wildcard bị từ chối khi backend khởi động.
- Email/tên tài khoản được chuẩn hóa, kiểm tra trùng và có validate dữ liệu đầu vào.
- Giao diện chat đang dùng dữ liệu minh họa; API chat, kho tài liệu pháp luật và tích hợp AI chưa
  nằm trong phiên bản này.

Xem chi tiết API tại [backend/README.md](backend/README.md).
