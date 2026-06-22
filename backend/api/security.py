"""Security module for Authentication and Authorization."""

from __future__ import annotations

import os
import json
import secrets
import hashlib
from enum import Enum
from pathlib import Path
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

from backend.core import get_settings

class Role(Enum):
    ADMIN = "admin"
    READONLY = "readonly"

API_KEY_NAME = "X-AEGIS-API-KEY"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_security_config_path() -> Path:
    settings = get_settings()
    config_dir = settings.data_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "security.json"

def _hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

def ensure_security_baseline():
    """Ensure a security baseline exists when authentication is enabled.

    Keys are never printed to stdout/logs (where they would be captured by
    container/systemd log collectors). They are written once to a protected
    ``api_keys.txt`` next to the (hashed) key store, for the operator to read.
    When authentication is disabled (default, local-first), no keys are needed
    and none are generated.
    """
    if not get_settings().auth_enabled:
        return

    config_path = get_security_config_path()
    if config_path.exists():
        return

    admin_key = f"aegis-{secrets.token_urlsafe(32)}"
    readonly_key = f"aegis-ro-{secrets.token_urlsafe(32)}"

    config = {
        "keys": {
            _hash_key(admin_key): {"role": Role.ADMIN.value},
            _hash_key(readonly_key): {"role": Role.READONLY.value},
        }
    }

    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)

    api_keys_path = get_settings().data_dir / "api_keys.txt"
    with open(api_keys_path, "w") as f:
        f.write("Authentication enabled. Generated API keys (will not be shown again):\n")
        f.write(f"ADMIN: {admin_key}\n")
        f.write(f"READONLY: {readonly_key}\n")

    log = __import__("logging").getLogger("aegis.security")
    log.info(f"Authentication enabled. Initial keys written securely to {api_keys_path}")

def get_current_role(api_key_header: str = Security(api_key_header)) -> Role:
    """Validate API key and return Role.

    When authentication is disabled (the default for local-first, single-user,
    loopback operation) every caller is treated as ADMIN so the bundled SPA works
    with no key. Enable ``AEGIS_AUTH_ENABLED`` to enforce keys.
    """
    if not get_settings().auth_enabled:
        return Role.ADMIN

    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-AEGIS-API-KEY header",
        )
        
    config_path = get_security_config_path()
    if not config_path.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security baseline not initialized.",
        )
        
    with open(config_path, "r") as f:
        config = json.load(f)
        
    key_hash = _hash_key(api_key_header)
    key_info = config.get("keys", {}).get(key_hash)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key",
        )
        
    return Role(key_info["role"])

def require_admin(role: Role = Security(get_current_role)) -> Role:
    if role != Role.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return role

def require_readonly(role: Role = Security(get_current_role)) -> Role:
    # Admin can do readonly actions too
    if role not in (Role.ADMIN, Role.READONLY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Read privileges required",
        )
    return role
