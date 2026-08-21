"""Hassfest translation rules that do not require Home Assistant."""

from __future__ import annotations

import json
import os
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
COMPONENT = os.path.join(ROOT, "custom_components", "openspeedtest_cli")


def _walk_strings(value: object) -> list[str]:
    """Collect every string leaf from a JSON document."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        collected: list[str] = []
        for item in value.values():
            collected.extend(_walk_strings(item))
        return collected
    if isinstance(value, list):
        collected = []
        for item in value:
            collected.extend(_walk_strings(item))
        return collected
    return []


class TranslationPlaceholderTests(unittest.TestCase):
    """Hassfest rejects raw URLs in translation strings."""

    def test_translation_files_have_no_raw_urls(self) -> None:
        """strings.json and locale files must use description placeholders."""
        files = [
            os.path.join(COMPONENT, "strings.json"),
            os.path.join(COMPONENT, "translations", "en.json"),
            os.path.join(COMPONENT, "translations", "ru.json"),
        ]
        for path in files:
            with self.subTest(path=os.path.relpath(path, ROOT)):
                with open(path, encoding="utf-8") as handle:
                    payload = json.load(handle)
                for text in _walk_strings(payload):
                    lowered = text.lower()
                    self.assertNotIn(
                        "http://",
                        lowered,
                        f"raw URL in {path}: {text!r}",
                    )
                    self.assertNotIn(
                        "https://",
                        lowered,
                        f"raw URL in {path}: {text!r}",
                    )

    def test_install_cli_uses_cli_url_placeholder(self) -> None:
        """The download helper text is filled from description_placeholders."""
        with open(os.path.join(COMPONENT, "strings.json"), encoding="utf-8") as handle:
            strings = json.load(handle)
        description = strings["config"]["step"]["user"]["data_description"][
            "install_cli"
        ]
        self.assertIn("{cli_url}", description)


if __name__ == "__main__":
    unittest.main()
