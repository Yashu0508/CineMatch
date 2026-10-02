# CineMatch Backend

Production-structured FastAPI backend for the CineMatch movie recommendation platform. This repository deliberately implements backend phase 1 only; no frontend is included.

## Quick start

1. Create a virtual environment and install dependencies: `python -m venv .venv`, activate it, then `pip install -r requirements.txt`.
2. Copy `.env.example` to `.env` and set `DATABASE_URL`, Supabase values, and the backend-only `OMDB_API_KEY`.
3. Apply [`backend/app/db/migrations/001_initial.sql`](backend/app/db/migrations/001_initial.sql) in the Supabase SQL editor (it enables `vector`, tables, indexes, and RLS). For local SQLite experimentation, run `python scripts/seed_database.py`.
4. Start the API: `cd backend && uvicorn app.main:app --reload`.
5. Visit `http://localhost:8000/docs` and use `/api/health` for readiness.

## Configuration

All required configuration is documented in `.env.example`. Keep `.env`, the OMDb API key, and Supabase service-role keys private. `SUPABASE_SERVICE_ROLE_KEY` and `OMDB_API_KEY` are backend-only; this API validates Supabase access tokens via the project's JWKS endpoint. CORS is restricted to `ALLOWED_ORIGINS`, not a wildcard.

## Data and recommendation workflows

- Enrich existing catalog records explicitly with OMDb: `python scripts/ingest_movies.py --title "The Matrix"` (OMDb does not provide broad discovery pagination).
- Generate changed-only embeddings: `python scripts/generate_embeddings.py`.
- The SQL migration defines `movie_embeddings.embedding vector(384)` for `all-MiniLM-L6-v2`. Local test-mode represents vectors as JSON to avoid requiring PostgreSQL.
- The recommender starts with popularity and TF-IDF content similarity, then has embedding, collaborative, and hybrid extension points. Hybrid weights are environment configuration, not claimed optimal values.

## Testing

From the repository root: `pytest backend/tests`. Tests use SQLite and mocked external-provider transports; they never call OMDb or Supabase. The test suite covers health, movie lookup/missing IDs, validation, protected interaction behavior through an auth dependency override, recommendation ranking, and OMDb behavior.

## API contract and production notes

See [docs/API_CONTRACT.md](docs/API_CONTRACT.md) for the frontend-consumable endpoints and response shapes. FastAPI serves live OpenAPI at `/openapi.json` and Swagger at `/docs`.

Before deploying, provision Supabase Postgres/Auth, run the migration, configure a private backend database credential, `OMDB_API_KEY`, and a valid allowed frontend origin. OMDb is used for title search/metadata; discovery and recommendations remain local because OMDb has no equivalent feeds.

For local development, put the real key only in `C:\Users\Yatharth Mehta\OneDrive\Desktop\Movie recommendation\.env` as `OMDB_API_KEY=your_real_key`. For production, configure `OMDB_API_KEY` in the backend service environment (for example Render), never in Vercel or any `NEXT_PUBLIC_*` variable.
