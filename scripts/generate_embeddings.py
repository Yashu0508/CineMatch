"""Create/update sentence-transformer embeddings only when movie text changes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import select
from app.core.config import get_settings
from app.db.database import SessionLocal
from app.db.models import Movie, MovieEmbedding
from app.services.embedding_service import EmbeddingService, movie_text, source_hash

def run() -> None:
    settings, db, service = get_settings(), SessionLocal(), EmbeddingService()
    try:
        for movie in db.scalars(select(Movie)):
            text, digest = movie_text(movie), source_hash(movie_text(movie))
            existing = db.get(MovieEmbedding, movie.id)
            if existing and existing.source_hash == digest and existing.model_name == settings.embedding_model: continue
            vector = service.embed([text])[0]
            if existing: existing.embedding, existing.model_name, existing.embedding_version, existing.source_hash = vector, settings.embedding_model, settings.embedding_version, digest
            else: db.add(MovieEmbedding(movie_id=movie.id, embedding=vector, model_name=settings.embedding_model, embedding_version=settings.embedding_version, source_hash=digest))
            movie.metadata_text = text
        db.commit()
    finally: db.close()
if __name__ == "__main__": run()
