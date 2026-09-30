# CineMatch deployment

This project deploys the FastAPI backend to Render and the Next.js frontend to Vercel. Supabase remains the PostgreSQL/Auth provider and TMDB remains a backend-only integration.

## 1. Push the repository to GitHub

Run these commands from the repository root. Replace the placeholder remote with your own repository URL.

```bash
git add .
git commit -m "prepare CineMatch for deployment"
git branch -M main
git remote add origin <GITHUB_REPOSITORY_URL>
git push -u origin main
```

Do not commit `.env`, `frontend/.env.local`, or any file containing credentials.

## 2. Deploy the backend on Render

1. In Render, choose **New → Blueprint** and select the GitHub repository.
2. Render will read [`render.yaml`](../render.yaml).
3. Set every `sync: false` variable in the Render dashboard.
4. Use the Supabase pooler `DATABASE_URL`, not a local PostgreSQL URL.
5. Set `ALLOWED_ORIGINS` temporarily to `http://localhost:3000` while testing, then append the final Vercel URL after frontend deployment:

```text
http://localhost:3000,https://<VERCEL_FRONTEND_URL>
```

6. Deploy and wait for the service to become healthy.
7. Verify:

```text
https://<RENDER_BACKEND_URL>/api/health
https://<RENDER_BACKEND_URL>/docs
https://<RENDER_BACKEND_URL>/openapi.json
```

Render uses `0.0.0.0` and its platform-provided `$PORT` through the start command in `render.yaml`.

## 3. Deploy the frontend on Vercel

1. In Vercel, choose **Add New → Project** and select the same repository.
2. Set the project root directory to `frontend`.
3. Use the detected Next.js install/build settings, or set:

```text
Install command: pnpm install --frozen-lockfile
Build command: pnpm build
```

4. Add this browser-safe environment variable in Vercel:

```text
NEXT_PUBLIC_API_URL=https://<RENDER_BACKEND_URL>
```

Do not add database URLs, TMDB tokens, Supabase service-role keys, or `sb_secret_*` keys to Vercel.

## 4. Finish CORS configuration

Copy the Vercel deployment URL into Render's `ALLOWED_ORIGINS` value, preserving localhost if local development is still needed. Redeploy the backend after changing it.

## 5. Smoke-test the deployed application

Verify the home page, search, movie details, signup, login, logout, watchlist, ratings, history, recommendations, and profile/preferences from the Vercel URL. An unauthenticated request to a protected endpoint must return `401`.

If movie endpoints fail while `/api/health` succeeds, inspect Render logs for TMDB provider errors. The backend logs the endpoint and error type only; it never logs tokens or authorization headers.

## Required Render variables

`DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `TMDB_ACCESS_TOKEN`, and `ALLOWED_ORIGINS` are required secrets/configuration. `APP_ENV`, `APP_LOG_LEVEL`, `TMDB_API_BASE_URL`, `TMDB_LANGUAGE`, `TMDB_REGION`, `EMBEDDING_MODEL`, and `EMBEDDING_VERSION` are included in `render.yaml`.

## Required Vercel variables

Only `NEXT_PUBLIC_API_URL` is required by the frontend.
