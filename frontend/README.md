# CineMatch Frontend

Next.js App Router frontend for the CineMatch API. The browser talks only to FastAPI; TMDB credentials, database credentials, and Supabase service-role/secret keys are never used here.

## Run locally

```bash
cp .env.example .env.local
pnpm install
pnpm dev
```

Set `NEXT_PUBLIC_API_URL` to the running FastAPI origin (the development fallback is `http://localhost:8000`; production must set the deployed Render URL explicitly). The backend must already be configured and running. Production checks are `pnpm run typecheck`, `pnpm run lint`, and `pnpm run build`.

For Vercel, set only `NEXT_PUBLIC_API_URL=https://<RENDER_BACKEND_URL>`. Never add backend secrets to Vercel environment variables.

Authentication uses the backend `/api/auth/register`, `/api/auth/login`, and `/api/auth/me` contract. The access token is kept in browser local storage and sent only to the configured FastAPI origin. Logout removes it locally.
