"""The OpenSpeedTest CLI integration."""

from __future__ import annotations

import os
import shutil

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.storage import Store

from .const import (
    CONFIGURATION_URL,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
    PLATFORMS,
    STORAGE_VERSION,
)
from .coordinator import OpenSpeedTestCoordinator

type OpenSpeedTestConfigEntry = ConfigEntry[OpenSpeedTestCoordinator]


def build_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return shared device metadata for all entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEVICE_NAME,
        manufacturer=DEVICE_MANUFACTURER,
        model=DEVICE_MODEL,
        configuration_url=CONFIGURATION_URL,
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: OpenSpeedTestConfigEntry
) -> bool:
    """Set up OpenSpeedTest CLI from a config entry."""
    coordinator = OpenSpeedTestCoordinator(hass, entry)
    await coordinator.async_load_cached()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    coordinator.async_start_scheduler()
    entry.async_on_unload(coordinator.async_stop_scheduler)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: OpenSpeedTestConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove isolated CLI HOME and cached results when the entry is deleted."""
    runtime_home = os.path.join(hass.config.config_dir, f".{DOMAIN}", entry.entry_id)

    def _cleanup() -> None:
        shutil.rmtree(runtime_home, ignore_errors=True)
        parent = os.path.dirname(runtime_home)
        try:
            os.rmdir(parent)
        except OSError:
            pass

    await hass.async_add_executor_job(_cleanup)
    store = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")
    await store.async_remove()


async def _async_reload_entry(
    hass: HomeAssistant, entry: OpenSpeedTestConfigEntry
) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
