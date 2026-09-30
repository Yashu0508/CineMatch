"""Idempotently ingest a manageable TMDB catalog. Run from repository root."""
import argparse, asyncio, logging, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.database import Base, SessionLocal, engine
from app.services.movie_service import upsert_movie
from app.services.tmdb import TMDBService

async def run(pages: int, category: str) -> None:
    Base.metadata.create_all(engine); service = TMDBService(); db = SessionLocal()
    try:
        for page in range(1, pages + 1):
            payload = await service.listing(category, page)
            for movie in payload.get("results", []): upsert_movie(db, movie)
            db.commit(); logging.info("ingested category=%s page=%s movies=%s", category, page, len(payload.get("results", [])))
    finally:
        db.close(); await service.aclose()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--pages", type=int, default=2); parser.add_argument("--category", choices=["trending", "popular", "top-rated", "upcoming"], default="popular")
    args = parser.parse_args(); logging.basicConfig(level=logging.INFO); asyncio.run(run(args.pages, args.category))
