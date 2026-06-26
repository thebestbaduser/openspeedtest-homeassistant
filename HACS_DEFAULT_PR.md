# HACS default PR — copy-paste template

Use this when opening a PR at <https://github.com/hacs/default/compare>.

## 1. Fork and branch

1. Open <https://github.com/hacs/default> → **Fork** (personal account only).
2. Clone your fork, create a branch from `master`:

```bash
git clone https://github.com/thebestbaduser/default.git
cd default
git checkout -b add-openspeedtest-homeassistant
```

## 2. Edit `integration`

Add this line **alphabetically** after `TheByteStuff/RemoteSyslog_Service`:

```json
  "thebestbaduser/openspeedtest-homeassistant",
```

Result:

```json
  "TheByteStuff/RemoteSyslog_Service",
  "thebestbaduser/openspeedtest-homeassistant",
  "thecem/octopus_germany",
```

## 3. Commit and push

```bash
git add integration
git commit -m "Adds new integration [thebestbaduser/openspeedtest-homeassistant]"
git push -u origin add-openspeedtest-homeassistant
```

## 4. Open PR — body text

```markdown
## Checklist

- [x] I've read the [publishing documentation](https://hacs.xyz/docs/publish/start).
- [x] I've added the [HACS action](https://hacs.xyz/docs/publish/action) to my repository.
- [x] (For integrations only) I've added the [hassfest action](https://developers.home-assistant.io/blog/2020/04/16/hassfest/) to my repository.
- [x] The actions are passing without any disabled checks in my repository.
- [x] I've added a link to the action run on my repository below in the links section.
- [x] I've created a new release of the repository after the validation actions were run successfully.

## Links

Link to current release: https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/tag/v1.3.2

Link to successful HACS action (without the `ignore` key): https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28257954430/job/83725742456

Link to successful hassfest action (if integration): https://github.com/thebestbaduser/openspeedtest-homeassistant/actions/runs/28257954430/job/83725742402
```

5. Mark PR **Ready for review**.

## 5. Before submitting — GitHub About (manual)

On <https://github.com/thebestbaduser/openspeedtest-homeassistant> add topics if missing:

`internet-speed`, `custom-component`, `python`
