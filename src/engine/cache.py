"""
Thread-safe prediction cache with TTL expiry.

Uses double-checked locking to prevent duplicate computation
under concurrent requests while avoiding lock contention on hits.
"""
import threading
import time
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: Any
    created_at: float
    ttl_seconds: float

    def is_valid(self) -> bool:
        return (time.monotonic() - self.created_at) < self.ttl_seconds


class ThreadSafeCache:
    """
    Thread-safe prediction cache with TTL expiry.
    
    Uses double-checked locking to prevent duplicate computation
    under concurrent requests while avoiding lock contention on hits.
    """
    
    def __init__(self):
        self._store: Dict[str, CacheEntry] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry and entry.is_valid():
            return entry.value
        return None

    def _get_key_lock(self, key: str) -> threading.Lock:
        with self._meta_lock:
            if key not in self._locks:
                self._locks[key] = threading.Lock()
            return self._locks[key]

    def get_or_compute(self, key: str, compute_fn: Callable, ttl_seconds: float = 300) -> Any:
        # Fast path — no lock needed on cache hit
        result = self.get(key)
        if result is not None:
            return result

        # Slow path — per-key lock prevents duplicate computation
        lock = self._get_key_lock(key)
        with lock:
            # Re-check after acquiring lock (double-checked locking)
            result = self.get(key)
            if result is not None:
                return result
            
            value = compute_fn()
            self._store[key] = CacheEntry(
                value=value,
                created_at=time.monotonic(),
                ttl_seconds=ttl_seconds,
            )
            return value

    def invalidate(self, key: str) -> None:
        self._store.pop(key, None)

    def clear(self) -> None:
        with self._meta_lock:
            self._store.clear()
            self._locks.clear()
