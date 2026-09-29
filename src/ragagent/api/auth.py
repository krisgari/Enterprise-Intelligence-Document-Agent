"""
API-key authentication for the RagAgent API.

Enterprise deployments virtually never expose an agent endpoint without
some form of auth in front of it. This is the simplest real version of
that: a shared-secret key, checked on every request via a FastAPI
dependency, compared against a value that lives in config/.env — never
hardcoded, never logged.

This is intentionally simple (a single shared key, not per-user OAuth or
JWT) so it's easy to reason about and swap out. In a real client
engagement you'd more likely sit this behind the client's own identity
provider (OAuth2/OIDC) or an API gateway that handles auth upstream —
this dependency is the seam where that would plug in instead.
"""
from fastapi import Header, HTTPException, status

from ragagent.config import settings
from ragagent.observability.logger import logger

_warned_auth_disabled = False


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """
    FastAPI dependency: validates the `X-API-Key` header against
    `settings.api_key` (from the `RAGAGENT_API_KEY` env var).

    If `RAGAGENT_API_KEY` is unset, auth is disabled — convenient for
    local development, but this logs a warning (once) rather than
    failing silently, so it's obvious in the logs if auth was meant to
    be on but the env var was never set in a real deployment.
    """
    global _warned_auth_disabled
    if not settings.api_key:
        if not _warned_auth_disabled:
            logger.warning(
                "RAGAGENT_API_KEY is not set — API auth is DISABLED. "
                "Set RAGAGENT_API_KEY in .env before deploying this anywhere "
                "other than local development."
            )
            _warned_auth_disabled = True
        return "auth-disabled"

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Pass it as the X-API-Key header.",
        )
    return x_api_key
