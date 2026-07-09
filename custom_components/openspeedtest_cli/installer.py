"""Install OpenSpeedTest CLI into the persistent config directory."""

from __future__ import annotations

import logging
import os
import tempfile

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import CLI_DOWNLOAD_TIMEOUT, CLI_DOWNLOAD_URL

_LOGGER = logging.getLogger(__name__)


def _normalize_cli_content(content: bytes) -> bytes:
    """Convert Windows CRLF line endings to Unix LF."""
    if b"\r" not in content:
        return content
    _LOGGER.debug("Normalizing CRLF line endings in openspeedtest-cli")
    return content.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _validate_destination(destination: str) -> None:
    """Reject empty or relative install destinations."""
    if not destination or not os.path.isabs(destination):
        raise ValueError("CLI install path must be an absolute path")
    if destination.endswith(os.sep) or os.path.basename(destination) in ("", ".", ".."):
        raise ValueError("CLI install path must point to a file")


async def async_install_cli(hass: HomeAssistant, destination: str) -> None:
    """Download openspeedtest-cli to a persistent path."""
    _validate_destination(destination)

    session = aiohttp_client.async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=CLI_DOWNLOAD_TIMEOUT)
    async with session.get(CLI_DOWNLOAD_URL, timeout=timeout) as response:
        response.raise_for_status()
        content = _normalize_cli_content(await response.read())

    if not content.startswith(b"#!"):
        raise ValueError("Downloaded file does not look like openspeedtest-cli")

    def _write() -> None:
        directory = os.path.dirname(destination)
        if directory:
            os.makedirs(directory, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(
            dir=directory or None,
            prefix=".openspeedtest-cli-",
            suffix=".tmp",
        )
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(content)
            os.chmod(temp_path, 0o755)
            os.replace(temp_path, destination)
        except Exception:
            try:
                os.unlink(temp_path)
            except OSError:
                pass
            raise

    await hass.async_add_executor_job(_write)
    _LOGGER.info("Installed OpenSpeedTest CLI to %s", destination)
