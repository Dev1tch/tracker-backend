import logging

from fastapi import Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.service_provider import ServiceProvider
from app.core.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """Best-effort originating client IP behind Vercel's proxy.

    Vercel sets ``x-real-ip`` to the originating client; ``x-forwarded-for`` can
    carry a client-supplied prefix, so we prefer ``x-real-ip``. This is not a
    hard security boundary (IPs can be spoofed/rotated) — per-email limiting on
    login compensates for that on the endpoint that matters most.
    """
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _check(db: SupabaseClient, key: str, limit: int, window_seconds: int) -> None:
    """Raise 429 if ``key`` has exceeded ``limit`` within ``window_seconds``.

    Fails OPEN on backend errors: a rate limiter must never take the API down,
    so a transient DB failure is logged and the request is allowed through
    rather than turning the limiter itself into a denial-of-service vector.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    try:
        response = db.rpc(
            "check_rate_limit",
            {"p_key": key, "p_limit": limit, "p_window_seconds": window_seconds},
        )
        row = (response.data or [{}])[0]
    except Exception:
        logger.warning("rate-limit check failed for key=%s; allowing request", key, exc_info=True)
        return

    if not row.get("allowed", True):
        retry_after = int(row.get("retry_after") or window_seconds)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please slow down and try again later.",
            headers={"Retry-After": str(retry_after)},
        )


class RateLimiter:
    """FastAPI dependency enforcing a per-client-IP fixed-window limit.

    Usage: ``dependencies=[Depends(RateLimiter("login", 5))]`` on a route, or as
    a router-wide default. ``scope`` namespaces the counter so different limits
    don't collide on the same IP.
    """

    def __init__(self, scope: str, limit: int, window_seconds: int = 60):
        self.scope = scope
        self.limit = limit
        self.window_seconds = window_seconds

    def __call__(
        self,
        request: Request,
        db: SupabaseClient = Depends(ServiceProvider.get_supabase_client),
    ) -> None:
        _check(db, f"{self.scope}:ip:{client_ip(request)}", self.limit, self.window_seconds)


def enforce_login_email_limit(db: SupabaseClient, identifier: str) -> None:
    """Per-account login throttle, keyed by the submitted identifier (lowercased).

    Complements the per-IP login limit: caps attempts against a single account
    even when an attacker rotates source IPs (credential stuffing).
    """
    _check(
        db,
        f"login:email:{identifier.strip().lower()}",
        settings.RATE_LIMIT_LOGIN_PER_MIN,
        60,
    )


# Pre-built limiters wired into routes. Limits are configurable via settings.
global_rate_limit = RateLimiter("global", settings.RATE_LIMIT_GLOBAL_PER_MIN, 60)
login_rate_limit = RateLimiter("login", settings.RATE_LIMIT_LOGIN_PER_MIN, 60)
signup_rate_limit = RateLimiter("signup", settings.RATE_LIMIT_SIGNUP_PER_MIN, 60)
