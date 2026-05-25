"""The OpenSpeedTest CLI integration."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later, async_track_time_interval

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, MIN_SCAN_INTERVAL, PLATFORMS
from .coordinator import OpenSpeedTestCoordinator

_LOGGER = logging.getLogger(__name__)

FIRST_TEST_DELAY = 30


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenSpeedTest CLI from a config entry."""
    coordinator = OpenSpeedTestCoordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _deferred_first_refresh(_now) -> None:
        _LOGGER.debug("Starting deferred OpenSpeedTest CLI refresh")
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_call_later(hass, FIRST_TEST_DELAY, _deferred_first_refresh)
    )

    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    scan_interval = max(int(scan_interval), MIN_SCAN_INTERVAL)

    async def _scheduled_update(_now) -> None:
        await coordinator.async_request_refresh()

    entry.async_on_unload(
        async_track_time_interval(
            hass,
            _scheduled_update,
            timedelta(seconds=scan_interval),
            name=f"{DOMAIN}_{entry.entry_id}",
        )
    )
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
