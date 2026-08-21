"""Helpers for validating and writing the OpenSpeedTest CLI script."""

from __future__ import annotations

import os
from urllib.parse import urlparse

CLI_MAX_DOWNLOAD_BYTES = 512 * 1024
CLI_ALLOWED_DOWNLOAD_HOSTS = frozenset({"openspeedtest.ru", "www.openspeedtest.ru"})
CLI_REQUIRED_MARKERS = (
    b"OpenSpeedTest.ru CLI",
    b"openspeedtest.ru",
    b"--no-submit",
)
CLI_REJECT_MARKERS = (
    b"openspeedtest-agent",
    b"import psutil",
    b"import requests",
)


def normalize_cli_content(content: bytes) -> bytes:
    """Convert Windows CRLF line endings to Unix LF."""
    if b"\r" not in content:
        return content
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def validate_destination(destination: str) -> None:
    """Reject empty or relative install destinations."""
    if not destination or not os.path.isabs(destination):
        raise ValueError("CLI install path must be an absolute path")
    if destination.endswith(os.sep) or os.path.basename(destination) in ("", ".", ".."):
        raise ValueError("CLI install path must point to a file")


def path_is_inside(path: str, root: str) -> bool:
    """Return True if path is the root or a file/dir inside root."""
    real_path = os.path.realpath(path)
    real_root = os.path.realpath(root)
    try:
        common = os.path.commonpath([real_path, real_root])
    except ValueError:
        return False
    return common == real_root


def assert_install_destination(destination: str, config_dir: str) -> None:
    """Require an absolute file path inside the Home Assistant config directory."""
    validate_destination(destination)
    if not path_is_inside(destination, config_dir):
        raise ValueError(
            "CLI install path must be inside the Home Assistant config directory"
        )


def assert_allowed_download_url(url: str) -> None:
    """Reject downloads that are not HTTPS from openspeedtest.ru."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in CLI_ALLOWED_DOWNLOAD_HOSTS:
        raise ValueError("CLI download URL is not an allowed OpenSpeedTest host")


def validate_cli_content(content: bytes, max_bytes: int = CLI_MAX_DOWNLOAD_BYTES) -> bytes:
    """Return normalized CLI contents or raise ValueError."""
    if len(content) > max_bytes:
        raise ValueError("Downloaded file is too large to be openspeedtest-cli")

    content = normalize_cli_content(content)
    if not content.startswith(b"#!"):
        raise ValueError("Downloaded file does not look like openspeedtest-cli")

    for marker in CLI_REQUIRED_MARKERS:
        if marker not in content:
            raise ValueError("Downloaded file is not a valid openspeedtest-cli script")

    for marker in CLI_REJECT_MARKERS:
        if marker in content:
            raise ValueError("Downloaded file looks like openspeedtest-agent, not CLI")

    return content
