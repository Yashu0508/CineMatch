import hashlib
from app.core.config import get_settings


def movie_text(movie) -> str:
    return "\n".join([f"Title: {movie.title}", f"Genres: {', '.join(g.name for g in movie.genres)}", f"Overview: {movie.overview or ''}", f"Language: {movie.original_language or ''}"])


def source_hash(text: str) -> str: return hashlib.sha256(text.encode()).hexdigest()


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings(); self._model = None
    def embed(self, texts: list[str]) -> list[list[float]]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.settings.embedding_model)
        return self._model.encode(texts, normalize_embeddings=True).tolist()
