"""Data update coordinator for OpenSpeedTest CLI."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    get_recommended_cli_path,
    CONF_API_KEY,
    CONF_BINARY_PATH,
    CONF_DURATION,
    CONF_SERVER_ID,
    CONF_SUBMIT_RESULTS,
    CONF_THREADS,
    DEFAULT_DURATION,
    DEFAULT_THREADS,
    DOMAIN,
    DOWNLOAD_PATTERN,
    JITTER_PATTERN,
    PING_PATTERN,
    SERVER_PATTERN,
    UPLOAD_PATTERN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SpeedtestResult:
    """Parsed speed test result."""

    ping: float
    jitter: float
    download: float
    upload: float
    server: str
    last_run: datetime
    success: bool
    error: str | None = None


def parse_cli_output(output: str) -> SpeedtestResult:
    """Parse OpenSpeedTest CLI stdout into structured data."""
    ping_match = re.search(PING_PATTERN, output, re.IGNORECASE)
    jitter_match = re.search(JITTER_PATTERN, output, re.IGNORECASE)
    download_match = re.search(DOWNLOAD_PATTERN, output, re.IGNORECASE)
    upload_match = re.search(UPLOAD_PATTERN, output, re.IGNORECASE)
    server_match = re.search(SERVER_PATTERN, output)

    missing = [
        name
        for name, match in (
            ("ping", ping_match),
            ("jitter", jitter_match),
            ("download", download_match),
            ("upload", upload_match),
        )
        if not match
    ]
    if missing:
        raise ValueError(f"Failed to parse CLI output, missing fields: {', '.join(missing)}")

    server = server_match.group(1).strip() if server_match else "Unknown"

    return SpeedtestResult(
        ping=float(ping_match.group(1)),
        jitter=float(jitter_match.group(1)),
        download=float(download_match.group(1)),
        upload=float(upload_match.group(1)),
        server=server,
        last_run=datetime.now(),
        success=True,
    )


class OpenSpeedTestCoordinator(DataUpdateCoordinator[SpeedtestResult]):
    """Fetch speed test data by running openspeedtest-cli."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        self._lock = asyncio.Lock()
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    @property
    def scan_interval(self) -> int:
        """Return configured scan interval in seconds."""
        return self.config_entry.options.get(
            "scan_interval",
            self.config_entry.data.get("scan_interval"),
        )

    def _build_command(self) -> list[str]:
        """Build CLI command from config entry."""
        data = {**self.config_entry.data, **self.config_entry.options}
        binary = data.get(
            CONF_BINARY_PATH,
            get_recommended_cli_path(self.hass.config.config_dir),
        )
        command = [binary]

        if not data.get(CONF_SUBMIT_RESULTS, False):
            command.append("--no-submit")

        if server_id := data.get(CONF_SERVER_ID):
            command.extend(["--server", str(int(server_id))])

        threads = int(data.get(CONF_THREADS, DEFAULT_THREADS))
        duration = int(data.get(CONF_DURATION, DEFAULT_DURATION))
        command.extend(["--threads", str(threads), "--duration", str(duration)])

        if api_key := data.get(CONF_API_KEY):
            command.extend(["--api-key", api_key])

        return command

    def _calculate_timeout(self) -> int:
        """Calculate subprocess timeout based on test duration."""
        data = {**self.config_entry.data, **self.config_entry.options}
        duration = int(data.get(CONF_DURATION, DEFAULT_DURATION))
        return max(180, duration * 4 + 120)

    async def _async_update_data(self) -> SpeedtestResult:
        """Run speed test and return parsed results."""
        if self._lock.locked():
            raise UpdateFailed("Speed test is already running")

        async with self._lock:
            command = self._build_command()
            timeout = self._calculate_timeout()
            _LOGGER.debug("Running OpenSpeedTest CLI: %s", " ".join(command))

            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except FileNotFoundError as err:
                raise UpdateFailed(
                    f"OpenSpeedTest CLI not found at '{command[0]}'. "
                    "Check the binary path in integration settings."
                ) from err

            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except TimeoutError as err:
                process.kill()
                await process.wait()
                raise UpdateFailed(
                    f"Speed test timed out after {timeout} seconds"
                ) from err

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")

            if process.returncode != 0:
                detail = stderr.strip() or stdout.strip() or "Unknown error"
                raise UpdateFailed(
                    f"OpenSpeedTest CLI exited with code {process.returncode}: {detail}"
                )

            try:
                return parse_cli_output(stdout)
            except ValueError as err:
                _LOGGER.debug("CLI stdout:\n%s", stdout)
                _LOGGER.debug("CLI stderr:\n%s", stderr)
                raise UpdateFailed(str(err)) from err

    async def async_run_test(self) -> SpeedtestResult:
        """Run a speed test immediately and refresh entity states."""
        await self.async_request_refresh()
        if self.last_exception is not None:
            raise self.last_exception
        if self.data is None:
            raise UpdateFailed("Speed test finished without data")
        return self.data
