"""Config flow for OpenSpeedTest CLI."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CLI_HELP_TIMEOUT,
    CONF_API_KEY,
    CONF_BINARY_PATH,
    CONF_DURATION,
    CONF_INSTALL_CLI,
    CONF_SERVER_ID,
    CONF_SUBMIT_RESULTS,
    CONF_THREADS,
    DEFAULT_DURATION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_THREADS,
    DOMAIN,
    MIN_SCAN_INTERVAL,
    get_recommended_cli_path,
)
from .installer import async_install_cli

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=MIN_SCAN_INTERVAL,
        max=86400,
        step=60,
        unit_of_measurement="s",
        mode=selector.NumberSelectorMode.BOX,
    )
)

SERVER_ID_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=1,
        step=1,
        mode=selector.NumberSelectorMode.BOX,
    )
)

THREADS_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=1,
        max=32,
        step=1,
        mode=selector.NumberSelectorMode.BOX,
    )
)

DURATION_SELECTOR = selector.NumberSelector(
    selector.NumberSelectorConfig(
        min=5,
        max=60,
        step=1,
        unit_of_measurement="s",
        mode=selector.NumberSelectorMode.BOX,
    )
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BINARY_PATH): str,
        vol.Required(CONF_SCAN_INTERVAL): SCAN_INTERVAL_SELECTOR,
        vol.Optional(CONF_SERVER_ID): SERVER_ID_SELECTOR,
        vol.Required(CONF_THREADS): THREADS_SELECTOR,
        vol.Required(CONF_DURATION): DURATION_SELECTOR,
        vol.Required(CONF_SUBMIT_RESULTS): bool,
        vol.Optional(CONF_API_KEY): str,
    }
)


def _normalize_int(value: Any, default: int) -> int:
    """Cast NumberSelector values (often floats) to int."""
    if value is None:
        return default
    return int(value)


def _normalize_optional_int(value: Any) -> int | None:
    """Cast optional numeric config values to int."""
    if value in (None, ""):
        return None
    return int(value)


def _suggested_options(hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    """Build suggested values for the options form."""
    suggested = {**entry.data, **entry.options}

    suggested[CONF_SCAN_INTERVAL] = _normalize_int(
        suggested.get(CONF_SCAN_INTERVAL), DEFAULT_SCAN_INTERVAL
    )
    suggested[CONF_THREADS] = _normalize_int(
        suggested.get(CONF_THREADS), DEFAULT_THREADS
    )
    suggested[CONF_DURATION] = _normalize_int(
        suggested.get(CONF_DURATION), DEFAULT_DURATION
    )

    server_id = _normalize_optional_int(suggested.get(CONF_SERVER_ID))
    if server_id is None:
        suggested.pop(CONF_SERVER_ID, None)
    else:
        suggested[CONF_SERVER_ID] = server_id

    if not suggested.get(CONF_API_KEY):
        suggested.pop(CONF_API_KEY, None)

    suggested.setdefault(
        CONF_BINARY_PATH, get_recommended_cli_path(hass.config.config_dir)
    )
    suggested.setdefault(CONF_SUBMIT_RESULTS, False)

    return suggested


async def _validate_binary(hass: HomeAssistant, binary_path: str) -> dict[str, str]:
    """Validate that the CLI binary exists and responds."""
    errors: dict[str, str] = {}

    try:
        process = await asyncio.create_subprocess_exec(
            binary_path,
            "--help",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(),
            timeout=CLI_HELP_TIMEOUT,
        )
    except FileNotFoundError:
        errors[CONF_BINARY_PATH] = "not_found"
        return errors
    except TimeoutError:
        errors["base"] = "timeout"
        return errors

    output = (
        stdout_bytes.decode("utf-8", errors="replace")
        + stderr_bytes.decode("utf-8", errors="replace")
    ).lower()

    if process.returncode != 0 or "openspeedtest" not in output:
        errors[CONF_BINARY_PATH] = "invalid"

    return errors


class OpenSpeedTestConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenSpeedTest CLI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        recommended_path = get_recommended_cli_path(self.hass.config.config_dir)

        if user_input is not None:
            binary_path = user_input[CONF_BINARY_PATH]

            if user_input.get(CONF_INSTALL_CLI):
                try:
                    await async_install_cli(self.hass, binary_path)
                except Exception as err:
                    _LOGGER.exception("Failed to install OpenSpeedTest CLI")
                    errors["base"] = "download_failed"
                    if isinstance(err, ValueError):
                        errors["base"] = "invalid_download"

            if not errors:
                errors = await _validate_binary(self.hass, binary_path)

            if not errors:
                await self.async_set_unique_id(binary_path)
                self._abort_if_unique_id_configured()
                api_key = user_input.get(CONF_API_KEY) or None
                return self.async_create_entry(
                    title="OpenSpeedTest CLI",
                    data={
                        CONF_BINARY_PATH: binary_path,
                        CONF_SCAN_INTERVAL: _normalize_int(
                            user_input.get(CONF_SCAN_INTERVAL), DEFAULT_SCAN_INTERVAL
                        ),
                        CONF_THREADS: _normalize_int(
                            user_input.get(CONF_THREADS), DEFAULT_THREADS
                        ),
                        CONF_DURATION: _normalize_int(
                            user_input.get(CONF_DURATION), DEFAULT_DURATION
                        ),
                        CONF_SERVER_ID: _normalize_optional_int(
                            user_input.get(CONF_SERVER_ID)
                        ),
                        CONF_SUBMIT_RESULTS: user_input.get(
                            CONF_SUBMIT_RESULTS, False
                        ),
                        CONF_API_KEY: api_key,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_BINARY_PATH, default=recommended_path): str,
                vol.Optional(
                    CONF_INSTALL_CLI,
                    default=not os.path.exists(recommended_path),
                ): bool,
                vol.Optional(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): SCAN_INTERVAL_SELECTOR,
                vol.Optional(CONF_SERVER_ID): SERVER_ID_SELECTOR,
                vol.Optional(CONF_THREADS, default=DEFAULT_THREADS): THREADS_SELECTOR,
                vol.Optional(CONF_DURATION, default=DEFAULT_DURATION): DURATION_SELECTOR,
                vol.Optional(CONF_SUBMIT_RESULTS, default=False): bool,
                vol.Optional(CONF_API_KEY): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
            description_placeholders={"config_path": recommended_path},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OpenSpeedTestOptionsFlowHandler:
        """Get the options flow for this handler."""
        return OpenSpeedTestOptionsFlowHandler()


class OpenSpeedTestOptionsFlowHandler(OptionsFlow):
    """Handle options for OpenSpeedTest CLI."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            errors = await _validate_binary(self.hass, user_input[CONF_BINARY_PATH])
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=self.add_suggested_values_to_schema(
                        OPTIONS_SCHEMA,
                        _suggested_options(self.hass, self.config_entry),
                    ),
                    errors=errors,
                )

            options = {
                CONF_BINARY_PATH: user_input[CONF_BINARY_PATH],
                CONF_SCAN_INTERVAL: _normalize_int(
                    user_input.get(CONF_SCAN_INTERVAL), DEFAULT_SCAN_INTERVAL
                ),
                CONF_THREADS: _normalize_int(
                    user_input.get(CONF_THREADS), DEFAULT_THREADS
                ),
                CONF_DURATION: _normalize_int(
                    user_input.get(CONF_DURATION), DEFAULT_DURATION
                ),
                CONF_SERVER_ID: _normalize_optional_int(
                    user_input.get(CONF_SERVER_ID)
                ),
                CONF_SUBMIT_RESULTS: user_input.get(CONF_SUBMIT_RESULTS, False),
                CONF_API_KEY: user_input.get(CONF_API_KEY) or None,
            }

            if options[CONF_SERVER_ID] is None:
                options.pop(CONF_SERVER_ID)

            if options[CONF_API_KEY] is None:
                options.pop(CONF_API_KEY)

            return self.async_create_entry(title="", data=options)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                _suggested_options(self.hass, self.config_entry),
            ),
        )
