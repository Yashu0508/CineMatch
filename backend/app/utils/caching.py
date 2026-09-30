from time import monotonic
from typing import Any


class TTLCache:
    """Small process-local cache; replaceable with Redis without changing callers."""
    def __init__(self) -> None:
        self._values: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._values.get(key)
        if item and item[0] > monotonic():
            return item[1]
        self._values.pop(key, None)
        return None

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._values[key] = (monotonic() + ttl_seconds, value)
