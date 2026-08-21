"""Unit tests that do not require Home Assistant."""

from __future__ import annotations

from datetime import timezone
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from types import ModuleType

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPONENT = os.path.join(ROOT, "custom_components", "openspeedtest_cli")


def _load(mod_name: str, filename: str) -> ModuleType:
    """Load a component module by file path, skipping Home Assistant package init."""
    path = os.path.join(COMPONENT, filename)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = module
    spec.loader.exec_module(module)
    return module


api_key = _load("ost_api_key", "api_key.py")
cli_file = _load("ost_cli_file", "cli_file.py")
parser = _load("ost_parser", "parser.py")

CONF_API_KEY = api_key.CONF_API_KEY
CONF_SUBMIT_RESULTS = api_key.CONF_SUBMIT_RESULTS
CONF_CLEAR_API_KEY = api_key.CONF_CLEAR_API_KEY

SAMPLE_OUTPUT = """\
OpenSpeedTest CLI
Сервер: Moscow #1
Ping: 1.00 ms\rPing: 12.34 ms
Jitter: 0.10 ms\rJitter: 2.50 ms
Download: 10.00 Mbps\rDownload: 250.55 Mbps
Upload: 5.00 Mbps\rUpload: 100.12 Mbps
"""

VALID_CLI = (
    b"#!/usr/bin/env python3\n"
    b"parser = argparse.ArgumentParser(\n"
    b' description="OpenSpeedTest.ru CLI - speed test."\n'
    b")\n"
    b'API_BASE_URL = "https://openspeedtest.ru"\n'
    b"parser.add_argument('--no-submit')\n"
)

VALID_API_KEY = "a" * 64


class ParseCliOutputTests(unittest.TestCase):
    """Tests for CLI stdout parsing."""

    def test_parses_final_progress_values(self) -> None:
        """Progress lines overwritten with \\r must use the last value."""
        result = parser.parse_cli_output(SAMPLE_OUTPUT)
        self.assertEqual(result.ping, 12.34)
        self.assertEqual(result.jitter, 2.5)
        self.assertEqual(result.download, 250.55)
        self.assertEqual(result.upload, 100.12)
        self.assertEqual(result.server, "Moscow #1")

    def test_parses_english_server_label(self) -> None:
        """English Server label is accepted."""
        output = SAMPLE_OUTPUT.replace("Сервер:", "Server:")
        result = parser.parse_cli_output(output)
        self.assertEqual(result.server, "Moscow #1")

    def test_missing_fields_raise(self) -> None:
        """Incomplete output raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parser.parse_cli_output("Ping: 1 ms\n")
        self.assertIn("missing fields", str(ctx.exception))

    def test_unknown_server_when_absent(self) -> None:
        """Missing server label falls back to unknown."""
        output = (
            "Ping: 10 ms\n"
            "Jitter: 1 ms\n"
            "Download: 100 Mbps\n"
            "Upload: 50 Mbps\n"
        )
        result = parser.parse_cli_output(output)
        self.assertEqual(result.server, "unknown")


class ResultCacheTests(unittest.TestCase):
    """Tests for result serialization."""

    def test_roundtrip(self) -> None:
        """Serialized results restore cleanly."""
        original = parser.parse_cli_output(SAMPLE_OUTPUT)
        restored = parser.result_from_dict(parser.result_to_dict(original))
        self.assertEqual(restored.ping, original.ping)
        self.assertEqual(restored.jitter, original.jitter)
        self.assertEqual(restored.download, original.download)
        self.assertEqual(restored.upload, original.upload)
        self.assertEqual(restored.server, original.server)
        self.assertEqual(restored.last_run, original.last_run)

    def test_naive_timestamp_gets_utc(self) -> None:
        """Naive timestamps from older caches are treated as UTC."""
        restored = parser.result_from_dict(
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
        redacted = parser.redact_command(command)
        self.assertNotIn("secret-token", redacted)
        self.assertIn("--api-key ***", redacted)


class InstallerHelperTests(unittest.TestCase):
    """Tests for installer helpers."""

    def test_normalize_crlf(self) -> None:
        """CRLF scripts are normalized to LF."""
        self.assertEqual(
            cli_file.normalize_cli_content(b"#!/usr/bin/env python3\r\n"),
            b"#!/usr/bin/env python3\n",
        )

    def test_reject_relative_destination(self) -> None:
        """Relative install paths are rejected."""
        with self.assertRaises(ValueError):
            cli_file.validate_destination("openspeedtest-cli")

    def test_reject_directory_destination(self) -> None:
        """Directory-like destinations are rejected."""
        with self.assertRaises(ValueError):
            cli_file.validate_destination("/config/")

    def test_reject_http_and_foreign_hosts(self) -> None:
        """Only HTTPS openspeedtest.ru is allowed."""
        with self.assertRaises(ValueError):
            cli_file.assert_allowed_download_url(
                "http://openspeedtest.ru/cli/openspeedtest-cli"
            )
        with self.assertRaises(ValueError):
            cli_file.assert_allowed_download_url(
                "https://evil.example/openspeedtest-cli"
            )
        cli_file.assert_allowed_download_url(
            "https://openspeedtest.ru/cli/openspeedtest-cli"
        )

    def test_validate_cli_content_accepts_real_markers(self) -> None:
        """A script with CLI markers is accepted."""
        self.assertTrue(cli_file.validate_cli_content(VALID_CLI).startswith(b"#!"))

    def test_reject_shebang_only(self) -> None:
        """A random shebang script is not accepted."""
        with self.assertRaises(ValueError):
            cli_file.validate_cli_content(b"#!/usr/bin/env python3\nprint('hi')\n")

    def test_reject_agent_script(self) -> None:
        """Enterprise agent must not be installed as CLI."""
        agent = VALID_CLI + b"\nimport psutil\nopenspeedtest-agent\n"
        with self.assertRaises(ValueError):
            cli_file.validate_cli_content(agent)

    def test_reject_oversized_payload(self) -> None:
        """Huge downloads are rejected before install."""
        with self.assertRaises(ValueError):
            cli_file.validate_cli_content(VALID_CLI, max_bytes=16)


class SubmitValidationTests(unittest.TestCase):
    """Tests for config-flow submit validation."""

    def test_api_key_required_when_submitting(self) -> None:
        """Submitting without an API key is rejected."""
        errors = api_key.validate_submit_settings(
            {CONF_SUBMIT_RESULTS: True, CONF_API_KEY: ""}
        )
        self.assertEqual(errors, {CONF_API_KEY: "api_key_required"})

    def test_submit_disabled_allows_empty_key(self) -> None:
        """No API key is fine when submission is off."""
        self.assertEqual(
            api_key.validate_submit_settings({CONF_SUBMIT_RESULTS: False}),
            {},
        )

    def test_existing_key_satisfies_submit(self) -> None:
        """Empty password field keeps the previously stored key."""
        errors = api_key.validate_submit_settings(
            {CONF_SUBMIT_RESULTS: True, CONF_API_KEY: ""},
            existing_api_key=VALID_API_KEY,
        )
        self.assertEqual(errors, {})

    def test_uppercase_key_is_normalized(self) -> None:
        """CLI accepts only lowercase hex; we lowercase user input."""
        self.assertEqual(api_key.normalize_api_key("A" * 64), VALID_API_KEY)
        self.assertTrue(api_key.is_valid_api_key("AB" * 32))

    def test_invalid_key_format(self) -> None:
        """Non-hex and wrong-length keys are rejected."""
        errors = api_key.validate_submit_settings(
            {CONF_SUBMIT_RESULTS: True, CONF_API_KEY: "not-a-key"}
        )
        self.assertEqual(errors, {CONF_API_KEY: "api_key_invalid"})

    def test_clear_flag_drops_existing_key(self) -> None:
        """Clearing the stored key is rejected when submission stays on."""
        errors = api_key.validate_submit_settings(
            {
                CONF_SUBMIT_RESULTS: True,
                CONF_API_KEY: "",
                CONF_CLEAR_API_KEY: True,
            },
            existing_api_key=VALID_API_KEY,
        )
        self.assertEqual(errors, {CONF_API_KEY: "api_key_required"})

    def test_clear_allowed_when_submit_disabled(self) -> None:
        """The stored key can be removed when results are not submitted."""
        errors = api_key.validate_submit_settings(
            {
                CONF_SUBMIT_RESULTS: False,
                CONF_API_KEY: "",
                CONF_CLEAR_API_KEY: True,
            },
            existing_api_key=VALID_API_KEY,
        )
        self.assertEqual(errors, {})


class CliRuntimeConfigTests(unittest.TestCase):
    """Tests for isolated CLI HOME config.json."""

    def test_writes_restricted_config(self) -> None:
        """API key is stored in config.json, not on the command line."""
        with tempfile.TemporaryDirectory() as home:
            api_key.write_cli_runtime_config(home, VALID_API_KEY)
            path = os.path.join(home, ".config", "openspeedtest-cli", "config.json")
            with open(path, encoding="utf-8") as file:
                payload = json.load(file)
            self.assertEqual(payload, {"api_key": VALID_API_KEY})
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)

    def test_removes_config_when_key_missing(self) -> None:
        """Clearing the key deletes the CLI config file."""
        with tempfile.TemporaryDirectory() as home:
            api_key.write_cli_runtime_config(home, VALID_API_KEY)
            api_key.write_cli_runtime_config(home, None)
            path = os.path.join(home, ".config", "openspeedtest-cli", "config.json")
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
