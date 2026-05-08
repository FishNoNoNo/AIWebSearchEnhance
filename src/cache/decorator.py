from __future__ import annotations

import hashlib


class CacheKeyGenerator:
    @staticmethod
    def search(engine: str, query: str, max_results: int) -> str:
        raw = f"{engine}:{query}:{max_results}".encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        return f"search:{engine}:{digest}"
