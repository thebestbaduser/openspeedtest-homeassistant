# Submitting to the HACS default catalog

This document is for the maintainer (`@thebestbaduser`) and tracks the
steps required to add this repository to
[`hacs/default`](https://github.com/hacs/default).

## 1. GitHub repository settings

Open <https://github.com/thebestbaduser/openspeedtest-homeassistant/settings>
and make sure the following is done. **HACS validation will fail without
all three.**

### 1.1. Description

Set a one-line description for the repository, for example:

> Кастомная интеграция для Home Assistant, которая запускает OpenSpeedTest CLI и публикует результаты замеров скорости.

### 1.2. Topics

Add at least these topics (repository home page → ⚙ next to **About** →
**Topics**). As of the last check, `internet-speed`, `custom-component`
and `python` still need to be added manually:

```
home-assistant
hacs
hacs-integration
integration
openspeedtest
speedtest
internet-speed
custom-component
python
```

### 1.3. Issues

Issues must be enabled (default on new repos). Verify on the **Issues**
tab.

## 2. CI must be green

The repository ships two GitHub Actions:

- `.github/workflows/validate.yml` — runs **HACS Action** and **Hassfest**
- `.github/workflows/release.yml` — auto-creates a GitHub release when
  pushing a tag of the form `v*`

Before submitting, open the **Actions** tab and confirm the latest
`Validate` run on `main` is green for **both** `HACS validation` and
`Hassfest validation`.

**Latest green run (2026-06-26):**

- Workflow run: <https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28213833282>
- HACS validation: <https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28213833282/job/83580566478>
- Hassfest validation: <https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28213833282/job/83580566517>

## 3. Create the first GitHub release

A tag alone is not enough — HACS requires a **release**.

After pushing a `v*` tag, the `Release` workflow creates a draft release
with auto-generated notes. To do it manually:

1. <https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/new>
2. Choose the tag (e.g. `v1.3.2`)
3. Set the title to `v1.3.2`
4. Use the contents of `CHANGELOG.md` for the body
5. Click **Publish release**

**Current release:** <https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/tag/v1.3.2>

## 4. Submit the PR to `hacs/default`

1. Fork <https://github.com/hacs/default> from a **personal** account
   (organisations are rejected).
2. Create a new branch from `master` (do not commit to `master` directly).
3. Open `integration` and add this line **alphabetically**:

   ```
   thebestbaduser/openspeedtest-homeassistant
   ```

4. Open a PR. Fill in the template:

   - **Link to current release:**
     `https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/tag/v1.3.2`
   - **Link to successful HACS action run:**
     <https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28213833282/job/83580566478>
   - **Link to successful Hassfest run:**
     <https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28213833282/job/83580566517>

5. Tick every checkbox in the checklist section.
6. Mark the PR as **Ready for review**.

## 5. Wait for review

Reviews are not fast — see the [backlog](https://github.com/hacs/default/pulls).
When merged, the repository will appear in HACS at the next scheduled
scan.

## Notes

- Brand assets live in
  `custom_components/openspeedtest_cli/brand/` (icon.png, icon@2x.png,
  logo.png, logo@2x.png) and follow the
  [home-assistant/brands](https://github.com/home-assistant/brands)
  size rules. **No PR to `home-assistant/brands` is required** because
  this is a custom integration on Home Assistant 2026.3+.
- The repository is country-tagged `RU` in `hacs.json`. HACS will hide
  it from non-Russian filters when that option is set in the UI, but it
  is still installable for everyone.
