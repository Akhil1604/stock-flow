from fastapi import Header, HTTPException, Request, status

from app.config import get_settings
from app.infrastructure.cache import ResilientCache

cache = ResilientCache()


def require_admin_key(x_admin_api_key: str | None = Header(default=None)) -> None:
    if x_admin_api_key != get_settings().admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin API key required"
        )


def enforce_rate_limit(request: Request) -> None:
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate:{client_ip}"
    count = cache.increment(key, 60)
    if count > get_settings().rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="Rate limit exceeded; retry in one minute")
