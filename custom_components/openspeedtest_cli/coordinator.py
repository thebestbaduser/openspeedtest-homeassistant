"""Data update coordinator for OpenSpeedTest CLI."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
import os
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api_key import normalize_api_key, write_cli_runtime_config
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
    MIN_SCAN_INTERVAL,
    MIN_SCHEDULE_DELAY,
    STARTUP_TEST_DELAY,
    STORAGE_VERSION,
    get_cli_runtime_home,
    get_recommended_cli_path,
)
from .parser import (
    SpeedtestResult,
    parse_cli_output,
    redact_command,
    result_from_dict,
    result_to_dict,
)

_LOGGER = logging.getLogger(__name__)

__all__ = [
    "OpenSpeedTestCoordinator",
    "SpeedtestResult",
    "parse_cli_output",
    "result_from_dict",
    "result_to_dict",
    "redact_command",
]


class OpenSpeedTestCoordinator(DataUpdateCoordinator[SpeedtestResult]):
    """Fetch speed test data by running openspeedtest-cli."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        self._store: Store[dict[str, Any]] = Store(
            hass,
            STORAGE_VERSION,
            f"{DOMAIN}.{entry.entry_id}",
        )
        self._unsub_timer: CALLBACK_TYPE | None = None
        self._test_lock = asyncio.Lock()
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,
            config_entry=entry,
        )

    def _merged_config(self) -> dict[str, Any]:
        """Return config entry data overlaid with options."""
        return {**self.config_entry.data, **self.config_entry.options}

    def _cli_runtime_home(self) -> str:
        """Return an isolated HOME directory for CLI config.json."""
        return get_cli_runtime_home(
            self.hass.config.config_dir, self.config_entry.entry_id
        )

    @property
    def scan_interval_seconds(self) -> int:
        """Return configured scan interval in seconds."""
        interval = self._merged_config().get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        return max(int(interval), MIN_SCAN_INTERVAL)

    def needs_refresh(self) -> bool:
        """Return True when a new speed test should be run."""
        if self.data is None:
            return True
        age = (datetime.now(timezone.utc) - self.data.last_run).total_seconds()
        return age >= self.scan_interval_seconds

    def seconds_until_next_test(self) -> int:
        """Return seconds until the next scheduled speed test."""
        if self.data is None:
            return 0
        remaining = self.scan_interval_seconds - (
            datetime.now(timezone.utc) - self.data.last_run
        ).total_seconds()
        return max(0, int(remaining))

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
            "Restored cached speed test from %s (next test in %d s)",
            result.last_run.isoformat(),
            self.seconds_until_next_test(),
        )

    @callback
    def async_start_scheduler(self) -> None:
        """Schedule the next speed test based on cache age."""
        self.async_stop_scheduler()
        delay = (
            STARTUP_TEST_DELAY
            if self.needs_refresh()
            else max(MIN_SCHEDULE_DELAY, self.seconds_until_next_test())
        )
        _LOGGER.debug("Next OpenSpeedTest CLI run in %d s", delay)
        self._unsub_timer = async_call_later(
            self.hass, delay, self._async_run_scheduled
        )

    @callback
    def async_stop_scheduler(self) -> None:
        """Cancel any pending speed test schedule."""
        if self._unsub_timer is not None:
            self._unsub_timer()
            self._unsub_timer = None

    async def _async_run_scheduled(self, _now: datetime) -> None:
        """Run a speed test when the interval elapsed and reschedule."""
        self._unsub_timer = None
        try:
            if self.needs_refresh():
                await self.async_request_refresh()
        finally:
            self.async_start_scheduler()

    def _build_command(self) -> list[str]:
        """Build CLI command from config entry.

        The API key is never passed on the command line. It is written to
        config.json under an isolated HOME instead.
        """
        data = self._merged_config()
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
        return command

    def _calculate_timeout(self) -> int:
        """Calculate subprocess timeout based on test duration."""
        duration = int(self._merged_config().get(CONF_DURATION, DEFAULT_DURATION))
        return max(180, duration * 4 + 120)

    async def _async_update_data(self) -> SpeedtestResult:
        """Run speed test and return parsed results."""
        async with self._test_lock:
            return await self._async_run_speedtest()

    async def _async_run_speedtest(self) -> SpeedtestResult:
        """Execute openspeedtest-cli and parse its output."""
        data = self._merged_config()
        command = self._build_command()
        timeout = self._calculate_timeout()
        runtime_home = self._cli_runtime_home()
        api_key = (
            normalize_api_key(data.get(CONF_API_KEY))
            if data.get(CONF_SUBMIT_RESULTS, False)
            else None
        )
        env = os.environ.copy()
        env["HOME"] = runtime_home

        await self.hass.async_add_executor_job(
            write_cli_runtime_config, runtime_home, api_key
        )

        _LOGGER.debug("Running OpenSpeedTest CLI: %s", redact_command(command))

        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.DEVNULL,
                env=env,
            )
        except FileNotFoundError as err:
            raise UpdateFailed(
                f"OpenSpeedTest CLI not found at '{command[0]}'. "
                "Check the binary path in integration settings."
            ) from err
        except OSError as err:
            raise UpdateFailed(
                f"Failed to start OpenSpeedTest CLI at '{command[0]}': {err}"
            ) from err

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
        except TimeoutError as err:
            await self._async_kill_process(process)
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

        if result.download == 0 and result.upload == 0:
            _LOGGER.warning(
                "OpenSpeedTest CLI (%s): download and upload are both 0 Mbps. "
                "Check network access from Home Assistant to the test server",
                result.server,
            )
            _LOGGER.debug(
                "CLI stdout for zero-speed result on server %s:\n%s",
                result.server,
                stdout,
            )

        await self._store.async_save(result_to_dict(result))
        return result

    async def _async_kill_process(self, process: asyncio.subprocess.Process) -> None:
        """Terminate a hung CLI process, escalating to kill if needed."""
        if process.returncode is not None:
            return

        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            process.kill()
            await process.wait()
