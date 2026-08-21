"""Sensor platform for OpenSpeedTest CLI."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import OpenSpeedTestConfigEntry, build_device_info
from .const import (
    ATTR_SERVER,
    SENSOR_DOWNLOAD,
    SENSOR_JITTER,
    SENSOR_LAST_TEST,
    SENSOR_PING,
    SENSOR_UPLOAD,
)
from .coordinator import OpenSpeedTestCoordinator, SpeedtestResult

PARALLEL_UPDATES = 0

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_DOWNLOAD,
        translation_key=SENSOR_DOWNLOAD,
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_UPLOAD,
        translation_key=SENSOR_UPLOAD,
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_PING,
        translation_key=SENSOR_PING,
        icon="mdi:lan-pending",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_JITTER,
        translation_key=SENSOR_JITTER,
        icon="mdi:chart-timeline-variant",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    SensorEntityDescription(
        key=SENSOR_LAST_TEST,
        translation_key=SENSOR_LAST_TEST,
        icon="mdi:clock-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenSpeedTestConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenSpeedTest CLI sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        OpenSpeedTestSensor(coordinator, entry, description)
        for description in SENSOR_TYPES
    )


class OpenSpeedTestSensor(CoordinatorEntity[OpenSpeedTestCoordinator], SensorEntity):
    """Representation of an OpenSpeedTest CLI sensor."""

    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: OpenSpeedTestCoordinator,
        entry: OpenSpeedTestConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry)

    @property
    def available(self) -> bool:
        """Return whether the last update succeeded and data is present."""
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self) -> float | datetime | None:
        """Return the state of the sensor."""
        data: SpeedtestResult | None = self.coordinator.data
        if data is None:
            return None

        if self.entity_description.key == SENSOR_LAST_TEST:
            return data.last_run

        return getattr(data, self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return None

        if self.entity_description.key == SENSOR_LAST_TEST:
            return None

        return {ATTR_SERVER: self.coordinator.data.server}
