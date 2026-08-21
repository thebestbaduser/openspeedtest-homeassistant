"""Button platform for OpenSpeedTest CLI."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import OpenSpeedTestConfigEntry, build_device_info
from .coordinator import OpenSpeedTestCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenSpeedTestConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenSpeedTest CLI button."""
    coordinator = entry.runtime_data
    async_add_entities([OpenSpeedTestRunButton(coordinator, entry)])


class OpenSpeedTestRunButton(CoordinatorEntity[OpenSpeedTestCoordinator], ButtonEntity):
    """Button to run a speed test on demand."""

    _attr_has_entity_name = True
    _attr_translation_key = "run_test"
    _attr_icon = "mdi:speedometer"

    def __init__(
        self,
        coordinator: OpenSpeedTestCoordinator,
        entry: OpenSpeedTestConfigEntry,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_run_test"
        self._attr_device_info = build_device_info(entry)

    @property
    def available(self) -> bool:
        """Keep the button usable after a failed speed test."""
        return True

    async def async_press(self) -> None:
        """Handle the button press without blocking the UI on a long test."""
        self.hass.async_create_task(self.coordinator.async_request_refresh())
