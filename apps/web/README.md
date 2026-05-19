# AI CFO Platform Web

Next.js 15 frontend for the AI CFO Platform. This app provides the public pages, auth screens, financial dashboard, and AI CFO chat workspace.

## Tech Stack

- Next.js App Router
- React 19
- Tailwind CSS 4
- Next API routes as a backend proxy

## Main Routes

```text
/               Landing page
/signin         Login
/signup         Signup
/dashboard      CFO dashboard
/text-generator AI CFO chat
```

## Local Setup

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

The app runs on:

```text
http://localhost:3000
```

## Environment

```env
OPENAI_API_KEY=
CFO_BACKEND_CHAT_URL=http://localhost:8000
CFO_COMPANY_ID=
CFO_BACKEND_API_KEY=
```

`CFO_BACKEND_CHAT_URL` can point to either the backend base URL or the `/ask` endpoint. The frontend sends chat traffic through `/api/chat`, which then calls the FastAPI backend.

## Build

```powershell
npm run build
npm run start
```
