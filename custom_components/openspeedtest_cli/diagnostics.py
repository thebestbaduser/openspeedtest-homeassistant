"""Diagnostics for the OpenSpeedTest CLI integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import OpenSpeedTestConfigEntry
from .const import CONF_API_KEY
from .parser import result_to_dict

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OpenSpeedTestConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry, with secrets redacted."""
    coordinator = entry.runtime_data
    result = result_to_dict(coordinator.data) if coordinator.data else None
    return {
        "entry": async_redact_data(
            {"data": dict(entry.data), "options": dict(entry.options)},
            TO_REDACT,
        ),
        "last_update_success": coordinator.last_update_success,
        "scan_interval_seconds": coordinator.scan_interval_seconds,
        "seconds_until_next_test": coordinator.seconds_until_next_test(),
        "result": result,
    }
