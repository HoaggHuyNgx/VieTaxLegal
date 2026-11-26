# VieTaxLegal Frontend

React (Vite) app with the landing page, the legal chat, account settings and an admin page. The
frontend never touches the database: all data goes through the FastAPI backend using HTTP-only
session cookies.

## Requirements

- Node.js 20.19+, 22.13+ or 24+, and npm. CI runs the latest Node 20.
- The backend running at `http://localhost:5000` for real sign-in and chat.

## Install and run

```powershell
cd D:\VieTaxLegal\frontend
npm install
npm run dev
```

Open <http://localhost:3000>. Vite forwards every `/api` request to `http://localhost:5000`, so the
browser sees one origin and session cookies work during development.

`npm install` also runs the `prepare` script, which installs the Husky git hook at the repository
root.

## Environment variables

There is a single variable, usually left alone:

| Variable       | Default | Description                                            |
| -------------- | ------- | ------------------------------------------------------ |
| `VITE_API_URL` | `/api`  | API prefix. Keep `/api` locally to use the Vite proxy. |

Copy `.env.example` to `.env` only to point at a backend on another host, for example in a
production build served from a different domain. Never put a Supabase key or an Anthropic / OpenAI
key in the frontend: every `VITE_*` variable is bundled and readable by users.

## Scripts

| Command                | What it does                                                  |
| ---------------------- | ------------------------------------------------------------- |
| `npm run dev`          | Dev server on port 3000 with the `/api` proxy.                |
| `npm run test`         | `vitest run`.                                                 |
| `npm run lint`         | `eslint src --max-warnings 0`.                                |
| `npm run format`       | Prettier, rewriting files.                                    |
| `npm run format:check` | Prettier, check only.                                         |
| `npm run build`        | `vite build` into `dist/`.                                    |
| `npm run preview`      | Serve the production build locally.                           |
| `npm run check`        | Test + lint + format check + build. Also the pre-commit hook. |

`.husky/pre-commit` runs `npm run check`, so a commit is blocked if any of the four steps fails.

## Startup flow

1. `index.html` loads `src/main.jsx`.
2. `main.jsx` renders `<App />` inside `I18nProvider` and loads `styles/index.css`.
3. `App.jsx` wraps everything in `ErrorBoundary` → `AuthProvider` → `BrowserRouter` and maps routes.
4. `AuthProvider` calls `GET /api/auth/me` once to restore the session (a `401` here just means
   "not signed in").
5. `/` renders `LandingPage` (`Hero` with the `AuthCard` sign-in form, then the other sections).
   The chat, settings and admin pages are lazy-loaded, so `react-markdown` is only downloaded after
   sign-in.

## `src/` layout

```text
src/
├── components/
│   ├── admin/       # AdminUsersTable, useAdminUsers
│   ├── auth/        # AuthCard, LoginForm, RegisterForm, email verification, Google button,
│   │                # ProtectedRoute, password rules, auth-styles.js
│   ├── chat/        # sidebar, topbar, workspace, messages, sources panel, useChatStream
│   ├── common/      # ErrorBoundary, LanguageToggle, PageLoading
│   └── landing/     # Hero, Features, Process, FAQ, Footer
├── context/         # AuthContext, auth-context, useAuth
├── data/            # static landing content and chat suggestions
├── i18n/            # provider, translator, error translation, locales/{vi,en}.js
├── pages/           # LandingPage, ChatPage, SettingsPage, AdminPage
├── services/        # api, auth, chat, admin: every HTTP call
└── styles/          # index.css: Tailwind tokens (@theme), breakpoint variants, base rules
```

Pure logic lives in `.js` files with a sibling `.test.js`; hooks are named `use*.js`. No TypeScript.

### Styling

The UI uses Tailwind CSS v4 (`@tailwindcss/vite`) with utilities written directly in JSX; there are
no per-component CSS files. `src/styles/index.css` is the only stylesheet.

- **Tokens** (colors, radii, shadows, gradients) are declared once in the `@theme` block and used as
  utilities such as `bg-chat-surface`, `rounded-chat`, `shadow-chat-soft`. No hex codes in JSX
  (brand SVG fills excepted).
- **Breakpoints** are the variants `lte-1220`, `lte-1100`, `lte-1024`, `lte-968`, `lte-768`,
  `lte-760`, `lte-640` (desktop-first, inclusive). Add a new one with `@custom-variant`, ordered from
  wide to narrow; do not use `max-*`.
- **Class names must be full strings** so Tailwind can find them: use a lookup table or a ternary,
  never `tint-${x}`. Shared class strings live in a `.js` module (for example
  `components/auth/auth-styles.js`); one repeated more than 3 times in a file becomes a constant.
- What utilities cannot express stays in `index.css`: markdown content styles (react-markdown),
  `@keyframes` and the chat base rules scoped by `chat-dashboard`. The `@layer base` block keeps a
  "pre-migration rendering" section for images, SVGs and form controls; removing it switches fully
  to Preflight (form controls change from Arial to Inter).
- Some classes have no styles on purpose: they are markers queried by tests (`language-toggle`,
  `conversation-select`, `send-button`, `source-card*`, `thread-scroll` and others).

## Routes

| Route       | Description                                                                 |
| ----------- | --------------------------------------------------------------------------- |
| `/`         | Landing page with sign-in and registration.                                 |
| `/chat`     | Chat. Wrapped in `ProtectedRoute`; signed-out users go back to `/`.         |
| `/settings` | Account settings: link a Google account. Requires sign-in.                  |
| `/admin`    | User list, role and active status. Requires the `admin` role, else `/chat`. |

The `admin` check in `ProtectedRoute` is only a UX gate; the backend enforces the role on every admin
endpoint.

## Authentication

`AuthProvider` restores the session with `GET /api/auth/me` on startup and exposes `user`,
`isLoading`, `register`, `login`, `logout` and `refreshSession` through `useAuth`.

Tokens live in HTTP-only cookies set by the backend, so JavaScript cannot read them. Every API call
uses `credentials: 'include'`; nothing is stored in `localStorage` or `sessionStorage`.

`authFetch` in `services/api.js` handles expiry: on a `401` it calls `POST /api/auth/refresh` once
(shared between parallel requests, so the token is not rotated twice) and retries. If the server
refuses the refresh token, the user is signed out and `ProtectedRoute` returns to `/`; network
errors or `5xx` during refresh do not sign anyone out.

While `isLoading`, `ProtectedRoute` shows a loading state instead of redirecting, so reloading
`/chat` does not sign the user out by mistake.

Registration: the form requests an email code, verifies it, and sends the returned proof with the
register payload. Password rules tick off live while typing (`password-rules.js`, mirroring the
backend policy). Google sign-in and linking are full-page redirects to `/api/auth/google/*`; a refused
callback comes back as `/?authError=CODE`.

## Chat streaming

`streamChatMessage` in `services/chat.js` sends `POST /api/chat/messages/stream`, reads
`response.body` as a `ReadableStream`, splits the SSE blocks and calls `onEvent` for each event.
`components/chat/useChatStream.js` applies them:

| Event   | Effect                                                                    |
| ------- | ------------------------------------------------------------------------- |
| `meta`  | Replace the temporary message with the real conversation and message ids. |
| `delta` | Append text to the assistant message on screen.                           |
| `done`  | Set the final text, token usage, citations and `completed` status.        |
| `error` | Show the safe error message and mark the message `failed`.                |

The stop button uses `AbortController`; the backend notices the disconnect and saves the message as
`cancelled` with the text received so far.

The chat only auto-scrolls when the reader is near the bottom. Answers render as GitHub Markdown
(`remark-gfm`: tables, lists; a single `~` stays as is). A URL pointing at a conversation that cannot
be opened (`404` / `422`) returns to an empty chat with a notice. A question being typed, or not yet
received by the server, is kept in the tab's `sessionStorage`, tied to the account, and cleared on
sign-out.

**Sources**: the sources panel lists only the citations the backend returns (sources the model
actually cited as `[n]`). Optional fields such as URL, excerpt, locator, document number and issue
date are shown only when present; nothing is filled in. With RAG off there are no citations and the
panel stays empty. Remaining daily messages come from `GET /api/chat/usage`.

## Bilingual UI

`I18nProvider` serves Vietnamese and English from `src/i18n/locales/vi.js` and `en.js`;
`catalog.test.js` checks that both have the same keys. Users switch with `LanguageToggle`; the choice
is stored in `localStorage` and Vietnamese is the default. All visible text, including aria-labels
and error messages, comes from `t` or `tList`.

## Error handling

`services/api.js` turns the backend error envelope into an `ApiError` with `status`, `code`,
`message` and `fields`. The UI translates by `code` in the current locale (`i18n/errors.js`); the
backend's Vietnamese `message` is only a fallback for unknown codes. `fields` attaches errors to
form inputs.

The full list of error codes is in [backend/README.md](../backend/README.md#error-format).

## Tests

```powershell
npm run test
```

Tests run with Vitest and jsdom, without a backend or real network:

- `services/*.test.js`: SSE parsing, error envelopes, the refresh-and-retry flow.
- `components/chat/*.test.*`: message state, stream lifecycle (retry, cancel), sources, conversation
  grouping, message times, workspace and assistant message rendering.
- `components/auth/*.test.*`: auth card, validation, password rules, email verification,
  `ProtectedRoute`.
- `components/admin`, `components/common`, `pages/*.test.jsx`: admin users hook, error boundary, chat
  and settings pages.
- `i18n/*.test.js` and `i18n/locales/catalog.test.js`: translator, error mapping, catalog parity.

## Conventions

- Prettier: single quotes, no semicolons, `printWidth` 110, LF line endings.
- ESLint runs with `--max-warnings 0`; a warning fails CI.
- File names are kebab-case for logic modules, PascalCase for components.

## Production build

```powershell
npm run build
npm run preview
```

`dist/` is static and can go on any static host; `nginx.conf` is the setup used by Docker Compose
(gzip, caching, security headers, `/api` proxy). If the frontend and backend are on different
domains, set `VITE_API_URL` to the API, add the frontend origin to the backend's `CORS_ORIGINS`, and
run the backend with `APP_ENV=production` so cookies get the `Secure` flag.
