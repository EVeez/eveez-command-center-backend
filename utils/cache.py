import os
import json
import hashlib
from typing import Callable, Any, Dict

try:
    from redis import Redis
except Exception:  # pragma: no cover
    Redis = None  # type: ignore


class NoOpCache:
    def get(self, *_args, **_kwargs):
        return None

    def setex(self, *_args, **_kwargs):
        return None


def get_cache_client():
    """Return Redis client if enabled, otherwise a no-op cache.

    Controlled by ENABLE_REDIS_CACHE env flag (default OFF).
    """
    enabled = os.getenv("ENABLE_REDIS_CACHE", "0") in ("1", "true", "True")
    if not enabled or Redis is None:
        return NoOpCache()
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    return Redis(host=host, port=port, db=db)


def cache_response(ttl_seconds: int = 60):
    """Simple caching decorator for idempotent GET endpoints.

    Cache key includes path and sorted query params.
    If Redis not enabled/present, acts as no-op.
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            from fastapi import Request

            cache = get_cache_client()
            request: Request = kwargs.get("request") if "request" in kwargs else None
            if request is None and args:
                # FastAPI injects request as first arg for dependencies when requested
                for a in args:
                    if getattr(a, "scope", None):  # crude Request detection
                        request = a  # type: ignore
                        break

            if request is None:
                return func(*args, **kwargs)

            query_pairs = sorted(request.query_params.multi_items())
            raw_key = json.dumps([request.url.path, query_pairs], separators=(",", ":"))
            key = "cache:" + hashlib.sha256(raw_key.encode()).hexdigest()

            cached = cache.get(key)
            if cached:
                try:
                    return json.loads(cached)
                except Exception:
                    pass

            result = func(*args, **kwargs)
            try:
                cache.setex(key, ttl_seconds, json.dumps(result))
            except Exception:
                pass
            return result

        return wrapper

    return decorator


