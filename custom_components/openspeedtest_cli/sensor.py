"""Sensor platform for OpenSpeedTest CLI."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_ERROR,
    ATTR_LAST_RUN,
    ATTR_SERVER,
    DOMAIN,
    SENSOR_DOWNLOAD,
    SENSOR_JITTER,
    SENSOR_PING,
    SENSOR_UPLOAD,
)
from .coordinator import OpenSpeedTestCoordinator, SpeedtestResult

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=SENSOR_DOWNLOAD,
        translation_key=SENSOR_DOWNLOAD,
        icon="mdi:download-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_UPLOAD,
        translation_key=SENSOR_UPLOAD,
        icon="mdi:upload-network",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_PING,
        translation_key=SENSOR_PING,
        icon="mdi:lan-pending",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=SENSOR_JITTER,
        translation_key=SENSOR_JITTER,
        icon="mdi:chart-timeline-variant",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up OpenSpeedTest CLI sensors."""
    coordinator: OpenSpeedTestCoordinator = hass.data[DOMAIN][entry.entry_id]
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
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="OpenSpeedTest CLI",
            manufacturer="OpenSpeedTest.ru",
            model="CLI Speed Test",
            configuration_url="https://openspeedtest.ru/cli/",
        )

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if not self.coordinator.data or not self.coordinator.data.success:
            return None

        data: SpeedtestResult = self.coordinator.data
        return getattr(data, self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, str | None]:
        """Return extra state attributes."""
        if not self.coordinator.data:
            return {}

        data = self.coordinator.data
        return {
            ATTR_SERVER: data.server,
            ATTR_LAST_RUN: data.last_run.isoformat(),
            ATTR_ERROR: data.error,
        }
