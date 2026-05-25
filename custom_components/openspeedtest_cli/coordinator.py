"""Data update coordinator for OpenSpeedTest CLI."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_API_KEY,
    CONF_BINARY_PATH,
    CONF_DURATION,
    CONF_SERVER_ID,
    CONF_SUBMIT_RESULTS,
    CONF_THREADS,
    DEFAULT_DURATION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_THREADS,
    DOMAIN,
    DOWNLOAD_PATTERN,
    JITTER_PATTERN,
    MIN_SCAN_INTERVAL,
    PING_PATTERN,
    SERVER_PATTERN,
    UPLOAD_PATTERN,
    get_recommended_cli_path,
    STORAGE_VERSION,
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


def _last_numeric_match(pattern: str, output: str) -> float | None:
    """Return the last numeric capture from output.

    The CLI overwrites progress lines with \\r, so stdout may contain several
    intermediate values before the final measurement.
    """
    matches = [
        float(value)
        for value in re.findall(pattern, output, flags=re.IGNORECASE)
    ]
    if not matches:
        return None
    return matches[-1]


def parse_cli_output(output: str) -> SpeedtestResult:
    """Parse OpenSpeedTest CLI stdout into structured data."""
    ping = _last_numeric_match(PING_PATTERN, output)
    jitter = _last_numeric_match(JITTER_PATTERN, output)
    download = _last_numeric_match(DOWNLOAD_PATTERN, output)
    upload = _last_numeric_match(UPLOAD_PATTERN, output)
    server_match = re.search(SERVER_PATTERN, output)

    missing = [
        name
        for name, value in (
            ("ping", ping),
            ("jitter", jitter),
            ("download", download),
            ("upload", upload),
        )
        if value is None
    ]
    if missing:
        raise ValueError(f"Failed to parse CLI output, missing fields: {', '.join(missing)}")

    server = server_match.group(1).strip() if server_match else "Unknown"

    result = SpeedtestResult(
        ping=ping,
        jitter=jitter,
        download=download,
        upload=upload,
        server=server,
        last_run=dt_util.utcnow(),
        success=True,
    )

    if result.download == 0 and result.upload == 0:
        _LOGGER.warning(
            "OpenSpeedTest CLI reported 0 Mbps for both download and upload. "
            "Check network access from Home Assistant to the selected server."
        )
        _LOGGER.debug("CLI stdout for zero-speed result:\n%s", output)

    return result


def result_to_dict(result: SpeedtestResult) -> dict:
    """Serialize a speed test result for persistent storage."""
    return {
        "ping": result.ping,
        "jitter": result.jitter,
        "download": result.download,
        "upload": result.upload,
        "server": result.server,
        "last_run": result.last_run.isoformat(),
        "success": result.success,
        "error": result.error,
    }


def result_from_dict(data: dict) -> SpeedtestResult:
    """Restore a speed test result from persistent storage."""
    last_run = dt_util.parse_datetime(data["last_run"])
    if last_run is None:
        raise ValueError("Invalid last_run timestamp in cache")

    return SpeedtestResult(
        ping=float(data["ping"]),
        jitter=float(data["jitter"]),
        download=float(data["download"]),
        upload=float(data["upload"]),
        server=str(data["server"]),
        last_run=last_run,
        success=bool(data.get("success", True)),
        error=data.get("error"),
    )


class OpenSpeedTestCoordinator(DataUpdateCoordinator[SpeedtestResult]):
    """Fetch speed test data by running openspeedtest-cli."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        self._lock = asyncio.Lock()
        self._store = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.{entry.entry_id}",
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
        )

    @property
    def scan_interval_seconds(self) -> int:
        """Return configured scan interval in seconds."""
        data = {**self.config_entry.data, **self.config_entry.options}
        interval = data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return max(int(interval), MIN_SCAN_INTERVAL)

    def needs_refresh(self) -> bool:
        """Return True when a new speed test should be run."""
        if self.data is None:
            return True
        age = (dt_util.utcnow() - self.data.last_run).total_seconds()
        return age >= self.scan_interval_seconds

    def seconds_until_next_test(self) -> float:
        """Return seconds until the next scheduled speed test."""
        if self.data is None:
            return 0
        remaining = self.scan_interval_seconds - (
            dt_util.utcnow() - self.data.last_run
        ).total_seconds()
        return max(0.0, remaining)

    async def async_load_cached(self) -> None:
        """Restore the last speed test result from storage."""
        stored = await self._store.async_load()
        if not stored:
            return

        try:
            result = result_from_dict(stored)
        except (KeyError, TypeError, ValueError):
            _LOGGER.warning("Could not restore cached OpenSpeedTest CLI results")
            return

        self.async_set_updated_data(result)
        _LOGGER.debug(
            "Restored cached speed test from %s (next test in %.0f s)",
            result.last_run.isoformat(),
            self.seconds_until_next_test(),
        )

    async def _async_save_result(self, result: SpeedtestResult) -> None:
        """Persist the latest speed test result."""
        await self._store.async_save(result_to_dict(result))

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
                result = parse_cli_output(stdout)
            except ValueError as err:
                _LOGGER.debug("CLI stdout:\n%s", stdout)
                _LOGGER.debug("CLI stderr:\n%s", stderr)
                raise UpdateFailed(str(err)) from err

            await self._async_save_result(result)
            return result

    async def async_run_test(self) -> SpeedtestResult:
        """Run a speed test immediately and refresh entity states."""
        await self.async_request_refresh()
        if self.last_exception is not None:
            raise self.last_exception
        if self.data is None:
            raise UpdateFailed("Speed test finished without data")
        return self.data
