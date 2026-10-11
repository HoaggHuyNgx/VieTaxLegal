# VieTaxLegal Frontend

Ứng dụng React (Vite) gồm landing page giới thiệu và giao diện chat pháp luật. Frontend không truy
cập database trực tiếp: mọi dữ liệu đi qua API của backend FastAPI bằng cookie phiên HTTP-only.

## Yêu cầu

- Node.js 20.19+, 22.13+ hoặc 24+ và npm. CI đang chạy phiên bản Node 20 mới nhất.
- Backend đang chạy ở `http://localhost:5000` nếu muốn dùng đăng nhập và chat thật.

## Cài đặt và chạy

```powershell
cd D:\VieTaxLegal\frontend
npm install
npm run dev
```

Mở <http://localhost:3000>. Vite proxy mọi request `/api` sang `http://localhost:5000`, nên trình
duyệt xem frontend và backend là cùng origin và cookie phiên hoạt động bình thường khi phát triển.

`npm install` chạy kèm script `prepare`, script này cài git hook husky ở thư mục gốc repository.

## Biến môi trường

Chỉ có một biến, và trong đa số trường hợp không cần đặt:

| Biến           | Mặc định | Mô tả                                                      |
| -------------- | -------- | ---------------------------------------------------------- |
| `VITE_API_URL` | `/api`   | Tiền tố API. Giữ `/api` để dùng Vite proxy khi chạy local. |

Copy `.env.example` thành `.env` nếu cần trỏ tới backend ở host khác, ví dụ khi build production
và frontend không nằm chung domain với API.

Không bao giờ đặt Supabase anon key, service-role key hoặc API key của Anthropic/OpenAI vào
frontend. Mọi biến `VITE_*` đều bị nhúng vào bundle và người dùng đọc được.

## Scripts

| Lệnh                   | Việc thực hiện                                               |
| ---------------------- | ------------------------------------------------------------ |
| `npm run dev`          | Dev server ở cổng 3000 kèm proxy `/api`.                     |
| `npm run test`         | `vitest run`.                                                |
| `npm run lint`         | `eslint src --max-warnings 0`.                               |
| `npm run format`       | Prettier ghi đè file.                                        |
| `npm run format:check` | Prettier kiểm tra, không sửa.                                |
| `npm run build`        | `vite build`, kết quả trong `dist/`.                         |
| `npm run preview`      | Xem thử bản build production.                                |
| `npm run check`        | Test + lint + format check + build. Cũng là pre-commit hook. |

Hook pre-commit ở `.husky/pre-commit` gọi đúng `npm run check`, nên commit sẽ bị chặn nếu một trong
bốn bước thất bại.

## Cấu trúc `src/`

```text
src/
├── components/
│   ├── auth/        # AuthCard, LoginForm, RegisterForm, ProtectedRoute
│   ├── chat/        # Sidebar, workspace, topbar và luồng stream
│   ├── common/      # Component dùng chung như LanguageToggle
│   └── landing/     # FAQ, Features, Footer, Hero, Process
├── context/         # AuthContext, auth-context, useAuth
├── data/            # Nội dung tĩnh của landing page và câu hỏi gợi ý
├── i18n/            # Provider, translator và catalog tiếng Việt/Anh
├── pages/           # LandingPage, ChatPage
├── services/        # api, auth, chat — toàn bộ lời gọi HTTP
└── styles/          # CSS toàn cục
```

CSS đặt cạnh component, không dùng CSS framework. Không có TypeScript.

## Routes

| Route   | Mô tả                                                                  |
| ------- | ---------------------------------------------------------------------- |
| `/`     | Landing page kèm form đăng ký và đăng nhập.                            |
| `/chat` | Giao diện chat. Bọc trong `ProtectedRoute`, chưa đăng nhập thì về `/`. |

## Xác thực

`AuthProvider` gọi `GET /api/auth/me` một lần khi ứng dụng khởi động để khôi phục phiên, rồi cung
cấp `user`, `isLoading`, `register`, `login`, `logout` và `refreshSession` qua hook `useAuth`.

Token nằm trong cookie HTTP-only do backend đặt, JavaScript không đọc được. Vì vậy mọi lời gọi API
đều dùng `credentials: 'include'`; frontend không lưu token vào `localStorage` hay `sessionStorage`.

Trong lúc `isLoading`, `ProtectedRoute` hiển thị trạng thái chờ thay vì đá người dùng về trang chủ,
tránh việc F5 ở `/chat` bị đăng xuất nhầm.

## Luồng chat streaming

`streamChatMessage` trong `src/services/chat.js` gửi `POST /api/chat/messages/stream` rồi đọc
`response.body` bằng `ReadableStream`, tự tách các block SSE và gọi lại `onEvent` cho từng event:

| Event   | Xử lý ở `ChatPage`                                                     |
| ------- | ---------------------------------------------------------------------- |
| `meta`  | Thay message tạm bằng id thật của conversation và message.             |
| `delta` | Nối thêm text vào message assistant đang hiển thị.                     |
| `done`  | Chốt nội dung cuối, token usage và trạng thái `completed`.             |
| `error` | Hiển thị thông báo an toàn từ backend và đánh dấu message là `failed`. |

Nút dừng dùng `AbortController`; backend nhận biết client ngắt kết nối và lưu message ở trạng thái
`cancelled` cùng phần nội dung đã nhận, nên nội dung dở không bị mất.

Hiện `NullRetriever` ở backend không trả citation nào, nên danh sách nguồn luôn rỗng và không hiển
thị. Đây là chủ ý: chưa có RAG thì không hiển thị số hiệu văn bản hay điều khoản nào cả.

## Giao diện song ngữ

`I18nProvider` cung cấp nội dung tiếng Việt và tiếng Anh từ các catalog trong
`src/i18n/locales/`. Người dùng chuyển ngôn ngữ bằng `LanguageToggle`; lựa chọn được lưu trong
`localStorage` với tiếng Việt là mặc định. Component lấy nội dung qua `t` hoặc `tList`, không viết
trực tiếp chuỗi hiển thị đã có khóa dịch.

## Xử lý lỗi

`src/services/api.js` chuyển envelope lỗi của backend thành `ApiError` với `status`, `code`,
`message` và `fields`. Tại lớp hiển thị, frontend ưu tiên dịch lỗi theo `code` bằng locale hiện tại.
`message` tiếng Việt từ backend chỉ là fallback cho mã lỗi chưa có trong catalog; `fields` dùng để
gắn lỗi vào từng ô nhập liệu trong form đăng ký và đăng nhập.

Danh sách mã lỗi đầy đủ nằm trong [backend/README.md](../backend/README.md).

## Kiểm thử

```powershell
npm run test
```

Test chạy bằng Vitest, không cần backend và không gọi mạng thật:

- `src/services/chat.test.js` — parse SSE, xử lý event lỗi và envelope lỗi HTTP.
- `src/components/chat/chat-messages.test.js` — gộp delta và cập nhật trạng thái message.
- `src/components/chat/conversation-groups.test.js` — gom hội thoại theo mốc thời gian.
- `src/components/chat/useChatStream.test.js` — kiểm tra vòng đời stream, retry và hủy request.
- `src/i18n/*.test.js` — kiểm tra catalog, translator và ánh xạ mã lỗi.

Logic thuần được tách khỏi component (`chat-messages.js`, `conversation-groups.js`) để test được
mà không cần render.

## Quy ước

- Prettier: nháy đơn, không dấu chấm phẩy, `printWidth` 110, xuống dòng LF.
- ESLint chạy với `--max-warnings 0`; cảnh báo cũng làm CI đỏ.
- Nội dung giao diện nằm trong catalog `src/i18n/locales/vi.js` và `en.js`; component dùng khóa
  dịch thay vì chứa trực tiếp chuỗi tiếng Việt hoặc tiếng Anh.

## Build production

```powershell
npm run build
npm run preview
```

`dist/` là thư mục tĩnh, deploy được lên bất kỳ static host nào. Khi frontend và backend khác
domain, đặt `VITE_API_URL` trỏ tới API và thêm origin của frontend vào `CORS_ORIGINS` của backend;
cookie phiên khi đó cần backend chạy `APP_ENV=production` để bật cờ `Secure`.
