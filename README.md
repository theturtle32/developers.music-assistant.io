# developers.music-assistant.io

Developer Documentation repo for Music Assistant based on MkDocs Material

NOTE that we use a [repo for the main documentation](https://github.com/music-assistant/music-assistant.io) and a [dedicated fork/repo](https://github.com/music-assistant/beta.music-assistant.io) for the beta docs.

## Where the content lives

Two sources, and knowing which is which saves editing the wrong file.

| Section | Lives in |
|---|---|
| Provider authoring guides, the home page | This repository, under `docs/` |
| Architecture pages and package docs | The [server repository](https://github.com/music-assistant/server), pulled in at build time |

`docs/architecture/` and `docs/packages/` are **generated** and git-ignored. Editing them here has
no effect; the change belongs in the server repo, either in its `docs/architecture/` or in the
`README.md` beside the code it describes.

## Building locally

```bash
pip install -r requirements.txt

# pull the architecture and package docs out of a server checkout
scripts/pull-server-docs.sh ../music-assistant-server

mkdocs serve
```

Then open <http://127.0.0.1:8000>.

Run the pull script **before** `mkdocs serve`, or the Architecture and Package docs sections will be
missing. Re-run it whenever the server docs change; `mkdocs serve` picks the new files up on its own
once they are on disk.

With no argument the script clones the server's default branch into a temporary directory, which is
handy for a one-off but slower:

```bash
scripts/pull-server-docs.sh
```

To check the built output without serving it:

```bash
mkdocs build
```

`mkdocs build --strict` is stricter still, but the social-card plugin needs Cairo, which is not
installed everywhere; if `--strict` fails only on cairo warnings, build without it.

## Running Music Assistant locally

These docs describe a server you will probably want running alongside them. From a
[server](https://github.com/music-assistant/server) checkout:

```bash
scripts/setup.sh                              # venv, dependencies, pre-commit hooks
python -m music_assistant --log-level debug   # http://localhost:8095
```

It needs Python 3.14+ and ffmpeg 7+. See the server's `DEVELOPMENT.md` for building a provider, and
its `docs/architecture/README.md` for how the pieces fit together.

## How the site is published

The `build-docs` workflow deploys to GitHub Pages on a push to the default branch. It also runs
nightly, and accepts a `repository_dispatch` of type `server-docs-updated`, so documentation merged
in the server repo reaches the site without a commit here.

The workflow checks the server repo out at its `dev` branch and runs the same pull script used
above, so a local build and a deployed build see the same content.

---

[![A project from the Open Home Foundation](https://www.openhomefoundation.org/badges/ohf-project.png)](https://www.openhomefoundation.org/)
