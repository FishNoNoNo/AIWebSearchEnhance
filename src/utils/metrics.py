from __future__ import annotations

from collections import Counter, deque
from dataclasses import dataclass, field
from time import time


@dataclass
class MetricsCollector:
    total_requests: int = 0
    search_required_total: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    engine_usage: Counter[str] = field(default_factory=Counter)
    errors: deque[float] = field(default_factory=lambda: deque(maxlen=10_000))
    request_timestamps: deque[float] = field(default_factory=lambda: deque(maxlen=10_000))
    latencies_ms: deque[float] = field(default_factory=lambda: deque(maxlen=10_000))

    def record_request(self, latency_ms: float | None = None) -> None:
        self.total_requests += 1
        self.request_timestamps.append(time())
        if latency_ms is not None:
            self.latencies_ms.append(latency_ms)

    def record_search_required(self) -> None:
        self.search_required_total += 1

    def record_cache_hit(self) -> None:
        self.cache_hits += 1

    def record_cache_miss(self) -> None:
        self.cache_misses += 1

    def record_engine_usage(self, engine: str) -> None:
        self.engine_usage[engine] += 1

    def record_error(self) -> None:
        self.errors.append(time())

    def snapshot(self) -> dict[str, object]:
        now = time()
        recent_requests = [item for item in self.request_timestamps if now - item <= 60]
        recent_errors = [item for item in self.errors if now - item <= 3600]
        cache_total = self.cache_hits + self.cache_misses
        engine_total = sum(self.engine_usage.values())
        return {
            "total_requests": self.total_requests,
            "requests_per_minute": len(recent_requests),
            "search_rate": round(self.search_required_total / self.total_requests, 4)
            if self.total_requests
            else 0,
            "cache_hit_rate": round(self.cache_hits / cache_total, 4) if cache_total else 0,
            "avg_latency_ms": round(sum(self.latencies_ms) / len(self.latencies_ms), 2)
            if self.latencies_ms
            else 0,
            "engine_usage": {
                key: round(value / engine_total, 4) for key, value in self.engine_usage.items()
            }
            if engine_total
            else {},
            "errors_last_hour": len(recent_errors),
        }
