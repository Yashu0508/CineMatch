from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_similarity(source_text: str, candidates: list[str]) -> list[float]:
    if not candidates: return []
    matrix = TfidfVectorizer(stop_words="english").fit_transform([source_text, *candidates])
    return cosine_similarity(matrix[0:1], matrix[1:]).flatten().tolist()
