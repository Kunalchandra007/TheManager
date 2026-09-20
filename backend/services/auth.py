"""Cognito JWT verification for TheManager API routes."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from fastapi import Header, HTTPException, status
from jose import jwt
from jose.exceptions import JWTError
from urllib.error import URLError
from urllib.request import urlopen
import json


@lru_cache(maxsize=1)
def _jwks(region: str, user_pool_id: str) -> dict[str, Any]:
    url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
    with urlopen(url, timeout=15) as response:  # nosec B310: AWS Cognito URL is constructed from config
        return json.loads(response.read())


def require_authenticated_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if os.getenv("DEMO_MODE", "false").lower() == "true":
        return {"sub": "local-demo-user"}

    region = os.getenv("AWS_REGION")
    user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
    client_id = os.getenv("COGNITO_CLIENT_ID")
    if not region or not user_pool_id or not client_id:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Authentication is not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
    try:
        try:
            keys = _jwks(region, user_pool_id)
        except (OSError, URLError, TimeoutError) as error:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service unavailable",
            ) from error

        claims = jwt.decode(token, keys, algorithms=["RS256"], audience=client_id, issuer=issuer)
        if claims.get("token_use") not in {"id", "access"}:
            raise JWTError("Unsupported token type")
        return claims
    except JWTError as error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token") from error
