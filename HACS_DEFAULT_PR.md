# HACS default PR — copy-paste after Validate is green

Open the PR from a **personal** fork of `hacs/default`, not from an
organisation. Fill in the `<>` links from the **green** Validate run on
`main` for tag `v1.3.5` — do not reuse the old `v1.3.4` / run
`28257954430` links.

## 1. Fork and branch

```bash
git clone https://github.com/thebestbaduser/default.git
cd default
git checkout master
git pull origin master
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

## 4. PR body

Replace every `<>` with a real URL before submitting. Tick the boxes
only after the linked jobs are green and `v1.3.5` is a published
GitHub **release**.

```markdown
## Checklist

- [x] I've read the [publishing documentation](https://hacs.xyz/docs/publish/start).
- [x] I've added the [HACS action](https://hacs.xyz/docs/publish/action) to my repository.
- [x] (For integrations only) I've added the [hassfest action](https://developers.home-assistant.io/blog/2020/04/16/hassfest/) to my repository.
- [x] The actions are passing without any disabled checks in my repository.
- [x] I've added a link to the action run on my repository below in the links section.
- [x] I've created a new release of the repository after the validation actions were run successfully.

## Links

Link to current release: https://github.com/thebestbaduser/openspeedtest-homeassistant/releases/tag/v1.3.5

Link to successful HACS action (without the `ignore` key): <>

Link to successful hassfest action (if integration): <>
```

5. Mark the PR **Ready for review**.

## 5. GitHub About (if still missing)

On the repo homepage: description, Issues enabled, topics:

`home-assistant`, `hacs`, `hacs-integration`, `integration`,
`openspeedtest`, `speedtest`, `internet-speed`, `custom-component`,
`python`
