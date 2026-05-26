"""Button platform for OpenSpeedTest CLI."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONFIGURATION_URL,
    DEVICE_MANUFACTURER,
    DEVICE_MODEL,
    DEVICE_NAME,
    DOMAIN,
)
from .coordinator import OpenSpeedTestCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenSpeedTest CLI button."""
    coordinator: OpenSpeedTestCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([OpenSpeedTestRunButton(coordinator, entry)])


class OpenSpeedTestRunButton(CoordinatorEntity[OpenSpeedTestCoordinator], ButtonEntity):
    """Button to run a speed test on demand."""

    _attr_has_entity_name = True
    _attr_translation_key = "run_test"
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: OpenSpeedTestCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_run_test"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=DEVICE_NAME,
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
            configuration_url=CONFIGURATION_URL,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_refresh()
