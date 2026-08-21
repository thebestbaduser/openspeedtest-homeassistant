"""API key normalization and CLI runtime config helpers."""

from __future__ import annotations

import json
import os
import re
import tempfile
from typing import Any

CONF_API_KEY = "api_key"
CONF_SUBMIT_RESULTS = "submit_results"

API_KEY_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def normalize_api_key(value: Any) -> str | None:
    """Strip and lowercase an API key. Empty values become None."""
    if value is None:
        return None
    key = str(value).strip().lower()
    return key or None


def is_valid_api_key(value: Any) -> bool:
    """Return True when value is a 64-character lowercase hex API key."""
    key = normalize_api_key(value)
    return bool(key and API_KEY_PATTERN.fullmatch(key))


def validate_submit_settings(
    user_input: dict[str, Any],
    *,
    existing_api_key: str | None = None,
) -> dict[str, str]:
    """Validate API key format and require it when submission is enabled."""
    raw = user_input.get(CONF_API_KEY)
    if raw not in (None, "") and not is_valid_api_key(raw):
        return {CONF_API_KEY: "api_key_invalid"}

    effective = normalize_api_key(raw) or normalize_api_key(existing_api_key)
    if user_input.get(CONF_SUBMIT_RESULTS) and not effective:
        return {CONF_API_KEY: "api_key_required"}
    return {}


def write_cli_runtime_config(home: str, api_key: str | None) -> None:
    """Write or remove the CLI config.json under an isolated HOME directory."""
    config_dir = os.path.join(home, ".config", "openspeedtest-cli")
    config_path = os.path.join(config_dir, "config.json")

    if not api_key:
        try:
            os.unlink(config_path)
        except FileNotFoundError:
            pass
        return

    os.makedirs(config_dir, mode=0o700, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(
        dir=config_dir,
        prefix=".config-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump({"api_key": api_key}, file)
        os.chmod(temp_path, 0o600)
        os.replace(temp_path, config_path)
    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise
