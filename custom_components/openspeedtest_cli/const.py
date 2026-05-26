"""Constants for the OpenSpeedTest CLI integration."""

from __future__ import annotations

import os

DOMAIN = "openspeedtest_cli"

CONF_BINARY_PATH = "binary_path"
CONF_INSTALL_CLI = "install_cli"
CONF_SERVER_ID = "server_id"
CONF_THREADS = "threads"
CONF_DURATION = "duration"
CONF_SUBMIT_RESULTS = "submit_results"
CONF_API_KEY = "api_key"

CLI_BINARY_NAME = "openspeedtest-cli"
CLI_DOWNLOAD_URL = "https://openspeedtest.ru/cli/openspeedtest-cli"
CLI_DOWNLOAD_TIMEOUT = 60
CLI_HELP_TIMEOUT = 30

DEFAULT_SCAN_INTERVAL = 6 * 60 * 60
DEFAULT_THREADS = 8
DEFAULT_DURATION = 10
MIN_SCAN_INTERVAL = 15 * 60
MIN_SCHEDULE_DELAY = 60
STARTUP_TEST_DELAY = 30

ATTR_SERVER = "server"
ATTR_LAST_RUN = "last_run"

SENSOR_DOWNLOAD = "download"
SENSOR_UPLOAD = "upload"
SENSOR_PING = "ping"
SENSOR_JITTER = "jitter"
SENSOR_LAST_TEST = "last_test"

PLATFORMS = ["sensor", "button"]

STORAGE_VERSION = 1

PING_PATTERN = r"Ping:\s+([\d.]+)\s*ms"
JITTER_PATTERN = r"Jitter:\s+([\d.]+)\s*ms"
DOWNLOAD_PATTERN = r"Download:\s+([\d.]+)\s*Mbps"
UPLOAD_PATTERN = r"Upload:\s+([\d.]+)\s*Mbps"
SERVER_PATTERN = r"(?:Сервер|Server):\s+([^\r\n]+)"

DEVICE_MANUFACTURER = "OpenSpeedTest.ru"
DEVICE_MODEL = "CLI Speed Test"
DEVICE_NAME = "OpenSpeedTest CLI"
CONFIGURATION_URL = "https://openspeedtest.ru/cli/"


def get_recommended_cli_path(config_dir: str) -> str:
    """Return the persistent CLI path inside the Home Assistant config directory."""
    return os.path.join(config_dir, CLI_BINARY_NAME)
