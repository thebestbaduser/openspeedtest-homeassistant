"""Unit tests for OpenSpeedTest CLI parsing and helpers."""

from __future__ import annotations

from datetime import timezone
import os
import sys
import unittest

# Allow importing the integration without a full Home Assistant custom_components layout.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from custom_components.openspeedtest_cli.coordinator import (  # noqa: E402
    _redact_command,
    parse_cli_output,
    result_from_dict,
    result_to_dict,
)
from custom_components.openspeedtest_cli.installer import (  # noqa: E402
    _normalize_cli_content,
    _validate_destination,
)


SAMPLE_OUTPUT = """\
OpenSpeedTest CLI
Сервер: Moscow #1
Ping: 1.00 ms\rPing: 12.34 ms
Jitter: 0.10 ms\rJitter: 2.50 ms
Download: 10.00 Mbps\rDownload: 250.55 Mbps
Upload: 5.00 Mbps\rUpload: 100.12 Mbps
"""


class ParseCliOutputTests(unittest.TestCase):
    """Tests for CLI stdout parsing."""

    def test_parses_final_progress_values(self) -> None:
        """Progress lines overwritten with \\r must use the last value."""
        result = parse_cli_output(SAMPLE_OUTPUT)
        self.assertEqual(result.ping, 12.34)
        self.assertEqual(result.jitter, 2.5)
        self.assertEqual(result.download, 250.55)
        self.assertEqual(result.upload, 100.12)
        self.assertEqual(result.server, "Moscow #1")

    def test_parses_english_server_label(self) -> None:
        """English Server label is accepted."""
        output = SAMPLE_OUTPUT.replace("Сервер:", "Server:")
        result = parse_cli_output(output)
        self.assertEqual(result.server, "Moscow #1")

    def test_missing_fields_raise(self) -> None:
        """Incomplete output raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_cli_output("Ping: 1 ms\n")
        self.assertIn("missing fields", str(ctx.exception))

    def test_unknown_server_when_absent(self) -> None:
        """Missing server label falls back to unknown."""
        output = (
            "Ping: 10 ms\n"
            "Jitter: 1 ms\n"
            "Download: 100 Mbps\n"
            "Upload: 50 Mbps\n"
        )
        result = parse_cli_output(output)
        self.assertEqual(result.server, "unknown")


class ResultCacheTests(unittest.TestCase):
    """Tests for result serialization."""

    def test_roundtrip(self) -> None:
        """Serialized results restore cleanly."""
        original = parse_cli_output(SAMPLE_OUTPUT)
        restored = result_from_dict(result_to_dict(original))
        self.assertEqual(restored.ping, original.ping)
        self.assertEqual(restored.jitter, original.jitter)
        self.assertEqual(restored.download, original.download)
        self.assertEqual(restored.upload, original.upload)
        self.assertEqual(restored.server, original.server)
        self.assertEqual(restored.last_run, original.last_run)

    def test_naive_timestamp_gets_utc(self) -> None:
        """Naive timestamps from older caches are treated as UTC."""
        restored = result_from_dict(
            {
                "ping": 1.0,
                "jitter": 0.5,
                "download": 10.0,
                "upload": 5.0,
                "server": "test",
                "last_run": "2026-01-01T12:00:00",
            }
        )
        self.assertEqual(restored.last_run.tzinfo, timezone.utc)


class RedactCommandTests(unittest.TestCase):
    """Tests for log redaction."""

    def test_redacts_api_key(self) -> None:
        """API key value must not appear in log output."""
        command = [
            "/config/openspeedtest-cli",
            "--threads",
            "8",
            "--api-key",
            "secret-token",
        ]
        redacted = _redact_command(command)
        self.assertNotIn("secret-token", redacted)
        self.assertIn("--api-key ***", redacted)


class InstallerHelperTests(unittest.TestCase):
    """Tests for installer helpers."""

    def test_normalize_crlf(self) -> None:
        """CRLF scripts are normalized to LF."""
        self.assertEqual(_normalize_cli_content(b"#!/usr/bin/env python3\r\n"), b"#!/usr/bin/env python3\n")

    def test_reject_relative_destination(self) -> None:
        """Relative install paths are rejected."""
        with self.assertRaises(ValueError):
            _validate_destination("openspeedtest-cli")

    def test_reject_directory_destination(self) -> None:
        """Directory-like destinations are rejected."""
        with self.assertRaises(ValueError):
            _validate_destination("/config/")


class SubmitValidationTests(unittest.TestCase):
    """Tests for config-flow submit validation."""

    def test_api_key_required_when_submitting(self) -> None:
        """Submitting without an API key is rejected."""
        from custom_components.openspeedtest_cli.config_flow import (
            _validate_submit_settings,
        )
        from custom_components.openspeedtest_cli.const import (
            CONF_API_KEY,
            CONF_SUBMIT_RESULTS,
        )

        errors = _validate_submit_settings(
            {CONF_SUBMIT_RESULTS: True, CONF_API_KEY: ""}
        )
        self.assertEqual(errors, {CONF_API_KEY: "api_key_required"})

    def test_submit_disabled_allows_empty_key(self) -> None:
        """No API key is fine when submission is off."""
        from custom_components.openspeedtest_cli.config_flow import (
            _validate_submit_settings,
        )
        from custom_components.openspeedtest_cli.const import CONF_SUBMIT_RESULTS

        self.assertEqual(
            _validate_submit_settings({CONF_SUBMIT_RESULTS: False}),
            {},
        )


if __name__ == "__main__":
    unittest.main()
