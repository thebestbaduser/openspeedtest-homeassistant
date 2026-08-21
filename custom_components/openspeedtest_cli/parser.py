"""Parse and serialize OpenSpeedTest CLI results without Home Assistant imports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any

PING_PATTERN = r"Ping:\s+([\d.]+)\s*ms"
JITTER_PATTERN = r"Jitter:\s+([\d.]+)\s*ms"
DOWNLOAD_PATTERN = r"Download:\s+([\d.]+)\s*Mbps"
UPLOAD_PATTERN = r"Upload:\s+([\d.]+)\s*Mbps"
SERVER_PATTERN = r"(?:Сервер|Server):\s+([^\r\n]+)"


@dataclass(slots=True)
class SpeedtestResult:
    """Parsed speed test result."""

    ping: float
    jitter: float
    download: float
    upload: float
    server: str
    last_run: datetime


def _last_numeric_match(pattern: str, output: str) -> float | None:
    """Return the last numeric capture from output.

    The CLI overwrites progress lines with \\r, so stdout may contain several
    intermediate values before the final measurement.
    """
    matches = re.findall(pattern, output, flags=re.IGNORECASE)
    if not matches:
        return None
    return float(matches[-1])


def parse_cli_output(output: str) -> SpeedtestResult:
    """Parse OpenSpeedTest CLI stdout into structured data."""
    ping = _last_numeric_match(PING_PATTERN, output)
    jitter = _last_numeric_match(JITTER_PATTERN, output)
    download = _last_numeric_match(DOWNLOAD_PATTERN, output)
    upload = _last_numeric_match(UPLOAD_PATTERN, output)
    server_match = re.search(SERVER_PATTERN, output)

    missing = [
        name
        for name, value in (
            ("ping", ping),
            ("jitter", jitter),
            ("download", download),
            ("upload", upload),
        )
        if value is None
    ]
    if missing or ping is None or jitter is None or download is None or upload is None:
        raise ValueError(
            f"Failed to parse CLI output, missing fields: {', '.join(missing)}"
        )

    server = server_match.group(1).strip() if server_match else "unknown"

    return SpeedtestResult(
        ping=ping,
        jitter=jitter,
        download=download,
        upload=upload,
        server=server,
        last_run=datetime.now(timezone.utc),
    )


def result_to_dict(result: SpeedtestResult) -> dict[str, Any]:
    """Serialize a speed test result for persistent storage."""
    return {
        "ping": result.ping,
        "jitter": result.jitter,
        "download": result.download,
        "upload": result.upload,
        "server": result.server,
        "last_run": result.last_run.isoformat(),
    }


def result_from_dict(data: dict[str, Any]) -> SpeedtestResult:
    """Restore a speed test result from persistent storage."""
    last_run = datetime.fromisoformat(data["last_run"])
    if last_run.tzinfo is None:
        last_run = last_run.replace(tzinfo=timezone.utc)

    return SpeedtestResult(
        ping=float(data["ping"]),
        jitter=float(data["jitter"]),
        download=float(data["download"]),
        upload=float(data["upload"]),
        server=str(data["server"]),
        last_run=last_run,
    )


def redact_command(command: list[str]) -> str:
    """Return a log-safe representation of the CLI command."""
    redacted: list[str] = []
    skip_next = False
    for part in command:
        if skip_next:
            redacted.append("***")
            skip_next = False
            continue
        if part == "--api-key":
            redacted.append(part)
            skip_next = True
            continue
        redacted.append(part)
    return " ".join(redacted)
