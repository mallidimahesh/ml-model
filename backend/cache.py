"""Thread-safe caching system with TTL and file persistence for EcoSim.
"""

from __future__ import annotations

import time
import json
import threading
from pathlib import Path
from typing import Any

CACHE_DIR = Path(__file__).resolve().parent / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


class SimpleCache:
    """Thread-safe in-memory cache with optional disk persistence and TTL."""

    def __init__(self, default_ttl: int = 3600):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()
        self.default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key in self._cache:
                expiry, val = self._cache[key]
                if time.time() < expiry:
                    return val
                else:
                    del self._cache[key]

        # Check disk cache
        disk_file = CACHE_DIR / f"{key}.json"
        if disk_file.exists():
            try:
                data = json.loads(disk_file.read_text(encoding="utf-8"))
                expiry = data.get("_expiry", 0)
                if time.time() < expiry:
                    with self._lock:
                        self._cache[key] = (expiry, data.get("payload"))
                    return data.get("payload")
            except Exception:
                pass
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expiry = time.time() + (ttl if ttl is not None else self.default_ttl)
        with self._lock:
            self._cache[key] = (expiry, value)

        # Persist to disk in background/try-catch
        try:
            disk_file = CACHE_DIR / f"{key}.json"
            disk_file.write_text(
                json.dumps({"_expiry": expiry, "payload": value}, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()


cache = SimpleCache(default_ttl=7200)  # 2 hours default
