# CineMatch

Production-structured FastAPI backend and Next.js frontend for the CineMatch movie recommendation platform.

## Quick start

1. Create a virtual environment and install dependencies: `python -m venv .venv`, activate it, then `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set `DATABASE_URL`, Supabase values, and `TMDB_ACCESS_TOKEN`.
3. Apply [`backend/app/db/migrations/001_initial.sql`](backend/app/db/migrations/001_initial.sql) in the Supabase SQL editor (it enables `vector`, tables, indexes, and RLS). For local SQLite experimentation, run `python scripts/seed_database.py`.
4. Start the API: `cd backend && uvicorn app.main:app --reload`.
5. In a second terminal, start the frontend from `frontend/` with `pnpm install` and `pnpm dev`.
6. Visit `http://localhost:8000/docs` and use `/api/health` for readiness.

## Configuration

All required configuration is documented in `.env.example`. Keep `.env`, TMDB bearer tokens, and Supabase service-role keys private. `SUPABASE_SERVICE_ROLE_KEY` is backend-only; this API validates Supabase access tokens via the project's JWKS endpoint. CORS is restricted to `ALLOWED_ORIGINS`, not a wildcard.

## Data and recommendation workflows

- Ingest a small, repeatable catalog: `python scripts/ingest_movies.py --category popular --pages 2`.
- Generate changed-only embeddings: `python scripts/generate_embeddings.py`.
- The SQL migration defines `movie_embeddings.embedding vector(384)` for `all-MiniLM-L6-v2`. Local test-mode represents vectors as JSON to avoid requiring PostgreSQL.
- The recommender starts with popularity and TF-IDF content similarity, then has embedding, collaborative, and hybrid extension points. Hybrid weights are environment configuration, not claimed optimal values.

## Testing

From the repository root: `pytest backend/tests`. Tests use SQLite and mocked TMDB transport; they never call TMDB or Supabase. The test suite covers health, movie lookup/missing IDs, validation, protected interaction behavior through an auth dependency override, and TF-IDF ranking.

## API contract and production notes

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for the frontend-consumable endpoints and response shapes. FastAPI serves live OpenAPI at `/openapi.json` and Swagger at `/docs`.

Before deploying, provision Supabase Postgres/Auth, run the migration, configure a private backend database credential and valid allowed frontend origin, and retain the TMDB attribution in the product: “This product uses the TMDB API but is not endorsed or certified by TMDB.”

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the exact Render and Vercel procedure. The Render blueprint is [render.yaml](render.yaml). The frontend only needs the browser-safe `NEXT_PUBLIC_API_URL`; all database, Supabase service-role, and TMDB credentials remain on the backend.
