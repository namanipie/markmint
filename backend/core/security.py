"""
Security and administrative authentication infrastructure for MarkMint.
Implements fail-closed authentication for moderation endpoints.
"""

import logging
import secrets
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPBearer, HTTPAuthorizationCredentials

from backend.core.config import settings

logger = logging.getLogger("markmint.security")

# Support both X-Admin-Key header and Bearer token for API/tooling flexibility
_admin_key_header = APIKeyHeader(name="X-Admin-Key", auto_error=False)
_bearer_auth = HTTPBearer(auto_error=False)


def verify_admin_key(candidate_key: Optional[str]) -> bool:
    """Constant-time comparison against configured ADMIN_API_KEY."""
    configured_key = settings.ADMIN_API_KEY
    if not configured_key or not isinstance(configured_key, str) or not configured_key.strip():
        # Fail closed: No administrative key configured
        return False
    if not candidate_key or not isinstance(candidate_key, str):
        return False
    return secrets.compare_digest(candidate_key.strip(), configured_key.strip())


def require_admin_auth(
    header_key: Optional[str] = Security(_admin_key_header),
    bearer_creds: Optional[HTTPAuthorizationCredentials] = Security(_bearer_auth),
) -> str:
    """
    FastAPI dependency ensuring administrative authorization.
    Fails closed if ADMIN_API_KEY is not configured in settings/environment.
    Does not log or expose the secret key.
    """
    configured_key = settings.ADMIN_API_KEY
    if not configured_key or not isinstance(configured_key, str) or not configured_key.strip():
        logger.warning("Administrative action blocked: ADMIN_API_KEY is not configured on the server.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Administrative authentication is not configured on this server.",
        )

    # Check X-Admin-Key header first
    candidate = header_key.strip() if header_key and isinstance(header_key, str) else None
    
    # Fallback to Bearer token
    if not candidate and bearer_creds and bearer_creds.credentials:
        candidate = bearer_creds.credentials.strip()

    if not candidate or not verify_admin_key(candidate):
        logger.warning("Unauthorized administrative access attempt blocked.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Invalid or missing administrative credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return "admin"
