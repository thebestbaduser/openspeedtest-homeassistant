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


def _normalize_int(value: Any, default: int) -> int:
    """Cast NumberSelector values (often floats) to int."""
    if value is None:
        return default
    return int(value)


def _normalize_optional_int(value: Any) -> int | None:
    """Cast optional numeric config values to int."""
    if value is None:
        return None
    return int(value)


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
            timeout=30,
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


def _options_schema(hass: HomeAssistant, data: dict[str, Any]) -> vol.Schema:
    """Build the options schema from merged config data."""
    recommended_path = get_recommended_cli_path(hass.config.config_dir)
    return vol.Schema(
        {
            vol.Required(
                CONF_BINARY_PATH,
                default=data.get(CONF_BINARY_PATH, recommended_path),
            ): str,
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=MIN_SCAN_INTERVAL,
                    max=86400,
                    step=60,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_SERVER_ID,
                default=data.get(CONF_SERVER_ID),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_THREADS,
                default=data.get(CONF_THREADS, DEFAULT_THREADS),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=32,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_DURATION,
                default=data.get(CONF_DURATION, DEFAULT_DURATION),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=60,
                    step=1,
                    unit_of_measurement="s",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SUBMIT_RESULTS,
                default=data.get(CONF_SUBMIT_RESULTS, False),
            ): bool,
            vol.Optional(
                CONF_API_KEY,
                default=data.get(CONF_API_KEY, ""),
            ): str,
        }
    )


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
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=86400,
                        step=60,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_SERVER_ID): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_THREADS, default=DEFAULT_THREADS): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=32,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(CONF_DURATION, default=DEFAULT_DURATION): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=5,
                        max=60,
                        step=1,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.BOX,
                    )
                ),
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
        return OpenSpeedTestOptionsFlowHandler(config_entry)


class OpenSpeedTestOptionsFlowHandler(OptionsFlow):
    """Handle options for OpenSpeedTest CLI."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        data = {**self.config_entry.data, **self.config_entry.options}
        schema = _options_schema(self.hass, data)

        if user_input is not None:
            errors = await _validate_binary(self.hass, user_input[CONF_BINARY_PATH])
            if errors:
                return self.async_show_form(
                    step_id="init",
                    data_schema=schema,
                    errors=errors,
                )

            if not user_input.get(CONF_API_KEY):
                user_input[CONF_API_KEY] = None

            user_input[CONF_SCAN_INTERVAL] = _normalize_int(
                user_input.get(CONF_SCAN_INTERVAL), DEFAULT_SCAN_INTERVAL
            )
            user_input[CONF_THREADS] = _normalize_int(
                user_input.get(CONF_THREADS), DEFAULT_THREADS
            )
            user_input[CONF_DURATION] = _normalize_int(
                user_input.get(CONF_DURATION), DEFAULT_DURATION
            )
            user_input[CONF_SERVER_ID] = _normalize_optional_int(
                user_input.get(CONF_SERVER_ID)
            )

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=schema)
