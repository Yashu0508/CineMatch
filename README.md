# CineMatch

CineMatch is a movie discovery and recommendation web application. Users can browse locally stored movie collections, search for films, view movie details, receive personalized recommendations, rate movies, maintain a watchlist and viewing history, and set Google Calendar reminders for eligible upcoming releases.

The repository contains a Next.js frontend and a FastAPI backend. The browser communicates with FastAPI; provider credentials and database access remain server-side.

## Core features

- Movie discovery sections for trending, popular, top-rated, and upcoming movies.
- Movie search and movie detail pages.
- Personalized recommendations based on popularity, preferences, ratings, viewing history, and content similarity.
- User ratings, watchlist management, and viewing history.
- Supabase Authentication for registration, login, bearer-token validation, and protected user features.
- Onboarding and user preference updates.
- Horizontal movie rails and responsive movie grids in the frontend.
- Google Calendar reminders for upcoming movies with a valid future release date.
- Profile avatars: authenticated users can upload a personal image, choose a built-in CineMatch preset, and switch between the two.

### Profile avatars

Authenticated users can upload a custom profile picture from their device or choose a built-in CineMatch avatar preset. They can switch between the uploaded image and a preset; selecting a preset temporarily changes the active avatar without deleting the uploaded image.

Uploaded avatars are stored in the private Supabase Storage bucket `profile-avatars`. The browser does not access Supabase Storage directly: FastAPI handles authenticated uploads and generates signed display URLs. The API only permits a user to modify their own avatar, and uploaded files are validated for supported image formats, file signatures, and size limits.

Avatar uploads use `multipart/form-data`. The frontend API client must not force `Content-Type: application/json` for `FormData` requests. Signed URLs are generated on demand by the backend, which normalizes Supabase URLs to include `/storage/v1` when necessary.

### Google Calendar reminders

For an eligible upcoming movie, an authenticated user can select **Set reminder**. CineMatch creates a short-lived OAuth state, sends the user through Google consent, exchanges the callback code on the backend, encrypts and stores the Google authorization tokens server-side, and creates an all-day Google Calendar event containing the movie title and release date. Google credentials and authorization tokens are never sent to the frontend.

The Calendar feature requires the additional database migration and backend encryption key described below. Automated tests mock Google services; a real Google Calendar event requires manual OAuth setup and testing.

## Movie data provider

OMDb is the external movie-data provider currently used by the backend for title search and movie metadata/detail enrichment. OMDb does not provide TMDB-style trending, popular, upcoming, similar-movie, or recommendation feeds.

Accordingly, CineMatch uses the existing local PostgreSQL/SQLite catalog and recommendation system for discovery categories and recommendation behavior where OMDb has no direct equivalent. Existing internal identifiers and stored movie records remain compatible with that local system.

The ingestion script enriches existing catalog titles explicitly with OMDb; it does not invent broad OMDb pagination or discovery data.

## Technology stack

| Area | Technologies |
| --- | --- |
| Frontend | Next.js App Router, React, TypeScript, Tailwind CSS, TanStack Query, lucide-react |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, Uvicorn, httpx |
| Database | PostgreSQL/Supabase PostgreSQL, SQLite for local test-mode, pgvector |
| Authentication | Supabase Auth; backend JWKS/bearer-token validation |
| Movie provider | OMDb API (backend-only) |
| Recommendation/ML | NumPy, Pandas, scikit-learn TF-IDF/cosine similarity, Sentence Transformers, configurable hybrid scoring |
| Calendar | Google OAuth 2.0 and Google Calendar events API (backend-only) |

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers, including calendar OAuth/reminders
│   │   ├── core/             # Settings and security dependencies
│   │   ├── db/               # SQLAlchemy models, database access, SQL migrations
│   │   ├── ml/               # Popularity, TF-IDF, and hybrid scoring
│   │   ├── schemas/          # Pydantic request/response models
│   │   └── services/         # OMDb, auth, recommendation, embedding, calendar services
│   └── tests/
├── frontend/
│   ├── app/                  # Next.js routes and pages
│   ├── components/           # Layout, navigation, movie, auth, and common UI
│   ├── hooks/
│   ├── lib/                  # API client and auth context
│   └── types/
├── docs/API_CONTRACT.md
├── scripts/
├── requirements.txt
├── .env.example
└── frontend/.env.example
```

## Environment variables

### Backend

Copy the root `.env.example` to the repository-root `.env` and replace placeholders locally. Do not commit `.env`.

```env
APP_ENV=development
APP_LOG_LEVEL=INFO
API_PREFIX=/api
DATABASE_URL=<postgresql-or-local-sqlite-url>
SUPABASE_URL=<supabase-project-url>
SUPABASE_ANON_KEY=<supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<backend-only-supabase-service-key>
OMDB_API_KEY=<backend-only-omdb-key>
OMDB_API_BASE_URL=https://www.omdbapi.com/
OMDB_CACHE_TTL_SECONDS=300
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_VERSION=v1
RECOMMENDER_MODE=hybrid
CONTENT_WEIGHT=0.45
COLLAB_WEIGHT=0.35
POPULARITY_WEIGHT=0.10
PREFERENCE_WEIGHT=0.10
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
GOOGLE_CLIENT_ID=<backend-google-oauth-client-id>
GOOGLE_CLIENT_SECRET=<backend-only-google-oauth-client-secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback
GOOGLE_TOKEN_ENCRYPTION_KEY=<backend-only-fernet-key>
```

`GOOGLE_TOKEN_ENCRYPTION_KEY` is used to encrypt stored Google access and refresh tokens. Generate a Fernet key with:

```powershell
.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Frontend

The frontend requires only the public backend URL in `frontend/.env.example`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Never place `DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `OMDB_API_KEY`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_TOKEN_ENCRYPTION_KEY`, or Google access/refresh tokens in frontend environment variables or any `NEXT_PUBLIC_*` variable.

## Local development

Install backend dependencies from the repository root:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Start the backend:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Start the frontend in a second terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

Expected local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health check: `http://localhost:8000/api/health`
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Google Calendar local setup

Before testing reminders:

1. Enable the Google Calendar API in Google Cloud.
2. Configure the OAuth consent screen.
3. Create/configure a Web Application OAuth client.
4. Add this authorized redirect URI: `http://localhost:8000/api/calendar/oauth/callback`.
5. Add these authorized JavaScript origins:
   - `http://localhost:3000`
   - `http://127.0.0.1:3000`
6. If the OAuth application is in Testing mode, add the Google account used for testing as an approved test user.
7. Set the three Google client variables and the backend-only token encryption key in the root `.env`.

The implemented OAuth scope is `https://www.googleapis.com/auth/calendar.events`.

## Database and migrations

The SQL migrations are in `backend/app/db/migrations/`:

- `001_initial.sql` creates the core movie, user-interaction, embedding, and pgvector schema.
- `002_google_calendar.sql` creates encrypted-token, OAuth-state, and calendar-reminder tables.
- `003_profile_avatar.sql` adds `avatar_type`, `avatar_ref`, and `avatar_upload_ref` to the `users` table for preset and uploaded profile avatars.

Apply the SQL migrations to the Supabase database in order using the Supabase SQL editor. The Google Calendar and profile-avatar migrations must be applied before using their respective features. In development with SQLite, `scripts/seed_database.py` can create local tables from SQLAlchemy metadata for experimentation; it is not a substitute for applying the Supabase migrations.

### Profile avatar Supabase setup

Before using profile avatars:

1. Apply `backend/app/db/migrations/003_profile_avatar.sql` after the existing migrations.
2. Create a **private** Supabase Storage bucket named `profile-avatars`.
3. Ensure the backend has its required Supabase service-role configuration; never expose the service-role key to the frontend.
4. Restart the backend after changing environment or Supabase configuration.

## Data and recommendation workflows

Enrich an existing local catalog title with OMDb:

```powershell
python scripts/ingest_movies.py --title "The Matrix"
```

Generate or update changed movie embeddings:

```powershell
python scripts/generate_embeddings.py
```

Embeddings use `sentence-transformers/all-MiniLM-L6-v2` and are stored as 384-dimensional vectors in PostgreSQL/pgvector. The recommendation system exposes popularity, TF-IDF content similarity, collaborative-data extension points, and configurable hybrid scoring. The configured weights are not claimed to be optimal.

## API documentation

The frontend-facing API contract is documented in [docs/API_CONTRACT.md](docs/API_CONTRACT.md). FastAPI provides live documentation at `http://localhost:8000/docs` and the OpenAPI document at `http://localhost:8000/openapi.json`.

The API includes authentication, movie discovery/search/detail routes, ratings, watchlist, viewing history, preferences, recommendations, and Google Calendar OAuth/reminder routes.

Profile avatar endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/users/profile` | Return the authenticated user's profile, including the active avatar reference or signed display URL. |
| `POST` | `/api/users/avatar/upload` | Upload and activate a validated custom avatar using multipart form data. |
| `PUT` | `/api/users/avatar/preset` | Select and activate a built-in CineMatch avatar preset. |
| `PUT` | `/api/users/avatar/upload/activate` | Reactivate the user's previously uploaded avatar without re-uploading it. |

## Testing

Run the backend test suite from the repository root:

```powershell
.venv\Scripts\python.exe -m pytest backend/tests -q
```

The tests use SQLite fixtures and mocked external-provider behavior; they do not perform live OMDb, Supabase, or Google Calendar calls.

Run frontend checks:

```powershell
cd frontend
pnpm typecheck
pnpm lint
pnpm build
```

The repository contains no automated deployment configuration. Local build/test commands verify the checked-in application; deployment to a hosting provider and live Google OAuth/calendar behavior require provider-specific configuration and manual verification.

## Security notes

- Keep `.env` ignored and out of version control.
- Keep Supabase service-role credentials, OMDb credentials, Google client secrets, and the token-encryption key on the backend only.
- Google access and refresh tokens are encrypted before database persistence.
- OAuth state is short-lived, stored hashed, and validated by the callback.
- The frontend communicates with FastAPI and does not call OMDb or Google Calendar directly.
- CORS is controlled by `ALLOWED_ORIGINS`; it is not configured as a wildcard.
- Profile-avatar endpoints require authentication and do not accept arbitrary user IDs. Users can only modify their own avatar.
- The `profile-avatars` bucket remains private; uploaded images are displayed through backend-generated signed URLs.
- Avatar uploads are checked by MIME type, file signature, and size before storage.

Do not describe the application as deployed or production-verified unless the relevant external services, migrations, hosting configuration, and live user flows have been tested separately.

## Documentation maintenance

Whenever a new feature, API endpoint, database migration, environment variable, external service, or significant bug fix is introduced, update this README in the same change so the documentation remains synchronized with the implementation.
