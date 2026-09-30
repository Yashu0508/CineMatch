def score(popularity: float | None, vote_average: float | None, vote_count: int | None) -> float:
    return (popularity or 0) + (vote_average or 0) * 10 + min(vote_count or 0, 10000) / 1000
