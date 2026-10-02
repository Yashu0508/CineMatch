"""Enrich existing local movies with OMDb metadata by explicit title.

OMDb does not provide a broad discovery feed, so this script intentionally
does not invent category pagination or create records with incompatible IMDb
string identifiers. Use --title for movies already present in the catalog.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.db.database import SessionLocal
from app.db.models import Movie
from app.services.omdb import OMDbService


async def run(titles: list[str]) -> None:
    db = SessionLocal()
    service = OMDbService()
    try:
        for title in titles:
            movie = db.scalar(select(Movie).where(Movie.title.ilike(title)))
            if movie is None:
                logging.warning("skipped title not present in local catalog: %s", title)
                continue
            payload = await service.details(title)
            if payload.get("Response") != "True":
                logging.warning("OMDb did not find title: %s", title)
                continue
            movie.overview = payload.get("Plot") if payload.get("Plot") not in (None, "N/A") else movie.overview
            db.commit()
            logging.info("enriched title=%s", title)
    finally:
        db.close()
        await service.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", action="append", required=True, help="Existing catalog title; repeat for multiple movies")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run(args.title))
