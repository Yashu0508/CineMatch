from app.core.config import get_settings


def combine(content: float = 0, collaborative: float = 0, popularity: float = 0, preference: float = 0) -> float:
    s = get_settings()
    return s.content_weight * content + s.collab_weight * collaborative + s.popularity_weight * popularity + s.preference_weight * preference
