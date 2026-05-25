"""The OpenSpeedTest CLI integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN, PLATFORMS
from .coordinator import OpenSpeedTestCoordinator

_LOGGER = logging.getLogger(__name__)

STARTUP_TEST_DELAY = 30
MIN_SCHEDULE_DELAY = 60


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenSpeedTest CLI from a config entry."""
    coordinator = OpenSpeedTestCoordinator(hass, entry)
    await coordinator.async_load_cached()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    @callback
    def _schedule_next_test(_now) -> None:
        """Run a test when due and schedule the next check."""
        entry.async_create_task(
            hass,
            _async_run_scheduled_test(coordinator, entry),
            f"{DOMAIN}_scheduled_{entry.entry_id}",
        )

    if coordinator.needs_refresh():
        if coordinator.data is None:
            _LOGGER.debug("No cached speed test results, scheduling first test")
        else:
            _LOGGER.debug("Cached speed test results expired, scheduling refresh")
        initial_delay = STARTUP_TEST_DELAY
    else:
        initial_delay = max(
            MIN_SCHEDULE_DELAY,
            int(coordinator.seconds_until_next_test()),
        )
        _LOGGER.info(
            "Restored last speed test from %s, next test in %s seconds",
            coordinator.data.last_run.isoformat(),
            int(coordinator.seconds_until_next_test()),
        )

    entry.async_on_unload(
        async_call_later(hass, initial_delay, _schedule_next_test)
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def _async_run_scheduled_test(
    coordinator: OpenSpeedTestCoordinator,
    entry: ConfigEntry,
) -> None:
    """Run a speed test if the interval elapsed and reschedule."""
    if coordinator.needs_refresh():
        await coordinator.async_request_refresh()

    delay = max(
        MIN_SCHEDULE_DELAY,
        int(coordinator.seconds_until_next_test()),
    )

    @callback
    def _schedule_next(_now) -> None:
        entry.async_create_task(
            coordinator.hass,
            _async_run_scheduled_test(coordinator, entry),
            f"{DOMAIN}_scheduled_{entry.entry_id}",
        )

    async_call_later(coordinator.hass, delay, _schedule_next)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
