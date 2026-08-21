"""Install OpenSpeedTest CLI into the persistent config directory."""

from __future__ import annotations

import logging
import os
import tempfile

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .cli_file import (
    CLI_MAX_DOWNLOAD_BYTES,
    assert_allowed_download_url,
    validate_cli_content,
    validate_destination,
)
from .const import CLI_DOWNLOAD_TIMEOUT, CLI_DOWNLOAD_URL

_LOGGER = logging.getLogger(__name__)


async def _read_limited(response: aiohttp.ClientResponse, max_bytes: int) -> bytes:
    """Read a response body, aborting if it exceeds max_bytes."""
    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared = int(content_length)
        except ValueError:
            declared = 0
        else:
            if declared > max_bytes:
                raise ValueError("Downloaded file is too large to be openspeedtest-cli")

    chunks: list[bytes] = []
    total = 0
    async for chunk in response.content.iter_chunked(64 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise ValueError("Downloaded file is too large to be openspeedtest-cli")
        chunks.append(chunk)
    return b"".join(chunks)


async def async_install_cli(hass: HomeAssistant, destination: str) -> None:
    """Download openspeedtest-cli to a persistent path."""
    validate_destination(destination)
    assert_allowed_download_url(CLI_DOWNLOAD_URL)

    session = aiohttp_client.async_get_clientsession(hass)
    timeout = aiohttp.ClientTimeout(total=CLI_DOWNLOAD_TIMEOUT)
    async with session.get(CLI_DOWNLOAD_URL, timeout=timeout) as response:
        response.raise_for_status()
        assert_allowed_download_url(str(response.url))
        raw = await _read_limited(response, CLI_MAX_DOWNLOAD_BYTES)
        if b"\r" in raw:
            _LOGGER.debug("Normalizing CRLF line endings in openspeedtest-cli")
        content = validate_cli_content(raw)

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
