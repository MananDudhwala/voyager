"""
shared/cache.py — Redis caching layer for Voyager backend.

Provides a lazily-initialised async Redis singleton with simple
cache_get / cache_set helpers and a deterministic key builder.

All public functions silently swallow Redis errors so the app
continues to work even when Redis is down (graceful degradation).

Usage:
    from shared.cache import cache_get, cache_set, make_cache_key

    key = make_cache_key("search_flights", origin="BOM", destination="GOI", date="2026-08-01")
    cached = await cache_get(key)
    if cached is None:
        result = await call_external_api(...)
        await cache_set(key, result, ttl=1800)
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

# Module-level singleton — set lazily on first call
_redis: Any | None = None  # redis.asyncio.Redis | None


def _cache_enabled() -> bool:
    return os.getenv("REDIS_CACHE_ENABLED", "true").lower() in ("1", "true", "yes")


async def get_redis():
    """
    Return the cached Redis client, creating it on first call.

    Returns None if REDIS_CACHE_ENABLED=false or if the import/connection fails.
    """
    global _redis
    if not _cache_enabled():
        return None
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis  # noqa: PLC0415

        url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _redis = aioredis.from_url(
            url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=0.5,  # fail fast — don't stall health checks or startup
            socket_timeout=1,
            retry_on_timeout=False,
        )
        # Verify connectivity eagerly so we log a warning now rather than
        # silently never caching anything.
        await _redis.ping()
        logger.info("[cache] Connected to Redis at %s", url)
        return _redis
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cache] Redis unavailable — caching disabled: %s", exc)
        _redis = None
        return None


async def close_redis() -> None:
    """Close the Redis connection pool. Call from FastAPI lifespan shutdown."""
    global _redis
    if _redis is not None:
        try:
            await _redis.aclose()
            logger.info("[cache] Redis connection closed")
        except Exception:  # noqa: BLE001
            pass
        finally:
            _redis = None


# ---------------------------------------------------------------------------
# Key helpers
# ---------------------------------------------------------------------------


def make_cache_key(prefix: str, **kwargs: Any) -> str:
    """
    Build a deterministic, collision-resistant cache key.

    Args:
        prefix: A human-readable prefix, e.g. ``"search_flights"``.
        **kwargs: Arbitrary key-value pairs that identify the resource.

    Returns:
        A string of the form ``"voyager:{prefix}:{sha256[:16]}"``.

    Example:
        >>> make_cache_key("search_flights", origin="BOM", destination="GOI")
        'voyager:search_flights:3f2a1b0c8e7d4c5a'
    """
    # Sort kwargs so that key order doesn't affect the hash
    payload = json.dumps(kwargs, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode()).hexdigest()[:16]
    return f"voyager:{prefix}:{digest}"


# ---------------------------------------------------------------------------
# Get / Set
# ---------------------------------------------------------------------------


async def cache_get(key: str) -> Any | None:
    """
    Retrieve a value from Redis.

    Returns:
        The deserialized Python object on a hit, or ``None`` on a miss or error.
    """
    r = await get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(key)
        if raw is None:
            return None
        value = json.loads(raw)
        logger.debug("[cache] HIT  %s", key)
        return value
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cache] GET error for %s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: int) -> None:
    """
    Store a value in Redis with a TTL (seconds).

    Args:
        key:   Cache key (from ``make_cache_key``).
        value: JSON-serializable Python object.
        ttl:   Expiry in seconds.
    """
    r = await get_redis()
    if r is None:
        return
    try:
        serialized = json.dumps(value, default=str)
        await r.set(key, serialized, ex=ttl)
        logger.debug("[cache] SET  %s (ttl=%ds)", key, ttl)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cache] SET error for %s: %s", key, exc)


async def cache_delete(key: str) -> None:
    """Delete a single cache key (useful for invalidation)."""
    r = await get_redis()
    if r is None:
        return
    try:
        await r.delete(key)
        logger.debug("[cache] DEL  %s", key)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[cache] DEL error for %s: %s", key, exc)


async def redis_ping() -> bool:
    """Return True if Redis is reachable, False otherwise."""
    r = await get_redis()
    if r is None:
        return False
    try:
        return await r.ping()
    except Exception:  # noqa: BLE001
        return False
