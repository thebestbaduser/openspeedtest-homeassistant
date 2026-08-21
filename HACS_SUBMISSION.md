# Submitting to the HACS default catalog

This is the **official** HACS listing: a PR against
[`hacs/default`](https://github.com/hacs/default) so the integration
appears in the HACS store without adding a custom repository.

Docs: [publish/start](https://hacs.xyz/docs/publish/start) and
[publish/include](https://hacs.xyz/docs/publish/include).

Only the GitHub owner (`@thebestbaduser`) or a major contributor can
open that PR, and it **must** come from a **personal** fork — PRs from
organisation accounts are closed because they are not editable by HACS
maintainers.

## Status in this repository

Already in place:

- Public GitHub repo, README, MIT license
- Root `hacs.json` with `name`, `country: RU`, `homeassistant: 2024.12.0`
- Integration layout: one domain under `custom_components/openspeedtest_cli/`
- `manifest.json` keys required by HACS (`domain`, `name`, `documentation`,
  `issue_tracker`, `codeowners`, `version`)
- Brand assets: `custom_components/openspeedtest_cli/brand/icon.png` (and
  `@2x` / `logo` variants). No PR to `home-assistant/brands` is required
  for a custom integration on Home Assistant 2026.3+.
- GitHub Actions: HACS Action (no `ignore`) and Hassfest in
  `.github/workflows/validate.yml`
- GitHub **releases** (not tags alone) via `.github/workflows/release.yml`

Must be true **on GitHub** before opening the `hacs/default` PR (these
are repository settings, not files):

- Description filled in
- Issues enabled
- Topics set (at least): `home-assistant`, `hacs`, `hacs-integration`,
  `integration`, `openspeedtest`, `speedtest`, `internet-speed`,
  `custom-component`, `python`

## Blockers that closed the previous attempt

1. **Hassfest must be green on the commit you release.** The `v1.3.4`
   Validate run failed because `strings.json` / `en.json` contained a
   raw URL. That is fixed in **1.3.5** (`{cli_url}` placeholder).
2. **Do not point the HACS PR at a red or stale Actions run.** The
   checklist asks for links to successful HACS and Hassfest jobs
   **without** `ignore`.
3. **Create the GitHub release after those jobs succeed.** A release
   cut from a failing commit (as `v1.3.4` was) will fail the
   `hacs/default` automated checks.

## Sequence

### 1. Land 1.3.5 and wait for Validate

Merge this branch to `main`. Open
<https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/workflows/validate.yml>
and wait until the latest run on `main` is green for:

- HACS validation
- Hassfest validation
- Unit tests

Copy the job URLs. Do **not** proceed on a failing or ignored run.

### 2. Publish GitHub release `v1.3.5`

After Validate is green on `main`:

```bash
git tag v1.3.5
git push origin v1.3.5
```

The `Release` workflow publishes the GitHub release. Confirm:

<https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/tag/v1.3.5>

A tag without a published **release** is not enough.

### 3. Open the PR on `hacs/default` (manual, personal account)

Copy-paste body: [`HACS_DEFAULT_PR.md`](HACS_DEFAULT_PR.md).

1. Fork <https://github.com/hacs/default> from a **personal** account.
2. New branch from `master` (never commit on `master`).
3. In `./integration`, add this line **alphabetically**
   (after `TheByteStuff/RemoteSyslog_Service`, before
   `thecem/octopus_germany`):

   ```json
     "thebestbaduser/openspeedtest-homeassistant",
   ```

4. Open the PR, fill the template (release + two green job links),
   tick every checkbox, mark **Ready for review**.
5. Do not submit if you are not the owner / a major contributor.

### 4. Wait

Reviews take **months**. Backlog:
<https://github.com/hacs/default/pulls>.

When the PR is up for review, HACS re-runs: brands, manifest,
hacs-validation, hacs.json, archived, releases, owner, repository
description / issues / topics, jq, alphabetical sort. All must pass.

After merge, the integration appears in HACS on the next scheduled
scan.

## Notes

- `country: RU` in `hacs.json` is a filter in the HACS UI. The
  integration is still installable for everyone.
- This wraps `openspeedtest-cli`, **not** `openspeedtest-agent.py`.
- Custom integrations that override a core component are rejected.
  This one does not.
- HACS Action must pass **without** the `ignore` input.
- Optional: a [My Home Assistant](https://my.home-assistant.io/create-link/?redirect=hacs_repository)
  link in the README after the repo is in the default catalog.
