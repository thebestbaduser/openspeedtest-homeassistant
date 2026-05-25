"""Install OpenSpeedTest CLI into the persistent config directory."""

from __future__ import annotations

import logging
import os

from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from .const import CLI_DOWNLOAD_URL

_LOGGER = logging.getLogger(__name__)


async def async_install_cli(hass: HomeAssistant, destination: str) -> None:
    """Download openspeedtest-cli to a persistent path."""
    session = aiohttp_client.async_get_clientsession(hass)
    async with session.get(CLI_DOWNLOAD_URL, timeout=60) as response:
        response.raise_for_status()
        content = await response.read()

    if not content.startswith(b"#!"):
        raise ValueError("Downloaded file does not look like openspeedtest-cli")

    def _write() -> None:
        directory = os.path.dirname(destination)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(destination, "wb") as file:
            file.write(content)
        os.chmod(destination, 0o755)

    await hass.async_add_executor_job(_write)
    _LOGGER.info("Installed OpenSpeedTest CLI to %s", destination)
