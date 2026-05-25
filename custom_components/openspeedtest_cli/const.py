"""Constants for the OpenSpeedTest CLI integration."""

DOMAIN = "openspeedtest_cli"

CONF_BINARY_PATH = "binary_path"
CONF_SERVER_ID = "server_id"
CONF_THREADS = "threads"
CONF_DURATION = "duration"
CONF_SUBMIT_RESULTS = "submit_results"
CONF_API_KEY = "api_key"

DEFAULT_BINARY_PATH = "openspeedtest-cli"
DEFAULT_SCAN_INTERVAL = 6 * 60 * 60
DEFAULT_THREADS = 8
DEFAULT_DURATION = 10
MIN_SCAN_INTERVAL = 15 * 60

ATTR_SERVER = "server"
ATTR_LAST_RUN = "last_run"
ATTR_ERROR = "error"

SENSOR_DOWNLOAD = "download"
SENSOR_UPLOAD = "upload"
SENSOR_PING = "ping"
SENSOR_JITTER = "jitter"

PLATFORMS = ["sensor", "button"]

PING_PATTERN = r"Ping:\s+([\d.]+)\s*ms"
JITTER_PATTERN = r"Jitter:\s+([\d.]+)\s*ms"
DOWNLOAD_PATTERN = r"Download:\s+([\d.]+)\s*Mbps"
UPLOAD_PATTERN = r"Upload:\s+([\d.]+)\s*Mbps"
SERVER_PATTERN = r"Сервер:\s+(.+)"
