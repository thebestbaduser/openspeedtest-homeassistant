# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.2] — 2026-06-10

### Changed

- Replaced brand icons and logos with transparent PNG assets (proper
  alpha channel) for correct display on light and dark Home Assistant
  themes.

## [1.3.1] — 2026-06-07

### Changed

- Restored SI units (`Mbit/s`, `ms`) and `device_class` on measurement
  sensors. Home Assistant localises unit symbols in the UI; hardcoded
  Cyrillic abbreviations broke multilingual setups and disabled automatic
  unit conversion.

### Fixed

- Zero-speed warning log now includes the selected server name.

## [1.3.0] — 2026-05-28

### Added

- Brand assets in the format required by `home-assistant/brands`:
  - `brand/icon.png` (256×256)
  - `brand/icon@2x.png` (512×512)
  - `brand/logo.png` (256×128)
  - `brand/logo@2x.png` (512×256)
- GitHub Actions: HACS validation and Hassfest on every push, PR and daily.
- Automatic GitHub release when pushing a `v*` tag.
- `CHANGELOG.md`.

### Changed

- Minimum Home Assistant version is now declared as **2024.12.0** in
  `hacs.json` (matches the modern `OptionsFlow` API).
- `hacs.json` cleaned up to the documented key set.

## [1.2.2] — 2026-05-26

### Changed

- Ping and Jitter sensors now display **`мс`** instead of `ms`.
- Download and Upload sensors now display **`Мбит/с`** instead of `Mbit/s`.
- `device_class` removed from these sensors (HA does not localise SI unit
  symbols); `state_class=MEASUREMENT` is kept so they still appear in
  long-term statistics.

## [1.2.0] — 2026-05-25

### Changed

- Refactored scheduler into the coordinator with proper cancel on unload.
- Removed redundant lock and dead `success`/`error` fields.
- Run-test button now awaits `async_refresh` so errors propagate.
- Centralised device metadata and CLI timeout constants.
- Use `aiohttp.ClientTimeout` in the installer.

### Added

- `sensor.<...>_last_test` timestamp sensor.
- `suggested_display_precision=2` for measurement sensors.
- `loggers` and `integration_type` in `manifest.json`.

## [1.1.0] — 2026-05-25

### Added

- Persistent cache for the latest speed test results. Cached values are
  shown immediately after Home Assistant restart; a new test is only run
  when the configured interval has elapsed.

## [1.0.7] — 2026-05-25

### Fixed

- Options flow crashed with `AttributeError: ConfigEntry has no
  attribute 'config_dir'`. Use `hass.config.config_dir` instead.

## [1.0.5] — 2026-05-25

### Fixed

- Options flow returned `500 Internal Server Error` because of
  `NumberSelector` with `default=None` and an outdated `OptionsFlow`
  constructor signature.

## [1.0.4] — 2026-05-25

### Fixed

- Speed test no longer blocks Home Assistant start-up. The first refresh
  runs 30 seconds after startup.
- Parser now reads the **last** `Download:` / `Upload:` line from CLI
  stdout. The CLI overwrites progress lines with `\r`, and the previous
  parser captured the initial `0.00 Mbps` value.

## [1.0.3] — 2026-05-25

### Fixed

- `NumberSelector` returned floats (`8.0`) which the CLI rejected.
  Cast `--threads`, `--duration` and `--server` to `int` before
  invocation.

## [1.0.2] — 2026-05-25

### Added

- CRLF normalisation when downloading `openspeedtest-cli` so the
  shebang line works on Linux even if the upstream serves the script
  with Windows line endings.

## [1.0.1] — 2026-05-25

### Changed

- Default binary path is now `<config>/openspeedtest-cli` so it survives
  Home Assistant container upgrades.
- Optional download step inside the config flow installs the CLI to
  the persistent config directory.

## [1.0.0] — 2026-05-25

### Added

- Initial release. Sensors for download, upload, ping and jitter, plus a
  button to run a speed test on demand.
- Config flow with options flow for scan interval, threads, duration,
  server selection and optional result submission to OpenSpeedTest.ru.
- English and Russian translations.
