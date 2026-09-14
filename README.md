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

Install into an environment of its own rather than system-wide. The dependencies need **Python
3.10 or newer**; a `python3 -m venv` on a machine whose system Python is older fails with a
confusing `No matching distribution found for mkdocs-awesome-nav`.

With [uv](https://docs.astral.sh/uv/), which picks a suitable interpreter for you and needs no
environment at all:

```bash
# pull the architecture and package docs out of a server checkout
scripts/pull-server-docs.sh ../music-assistant-server

uv run --with-requirements requirements.txt mkdocs serve
```

Or with a virtualenv, if you would rather have one to activate:

```bash
uv venv --python 3.12          # or: python3.12 -m venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt   # or: pip install -r requirements.txt

scripts/pull-server-docs.sh ../music-assistant-server
mkdocs serve
```

Either way, open <http://127.0.0.1:8000>. `.venv/` is git-ignored.

Run the pull script **before** serving, or the Architecture and Package docs sections will be
missing. Re-run it whenever the server docs change; `mkdocs serve` picks the new files up on its own
once they are on disk.

With no argument the script clones the server's default branch into a temporary directory, which is
handy for a one-off but slower:

```bash
scripts/pull-server-docs.sh
```

To check the built output without serving it, substitute `mkdocs build` for `mkdocs serve`, or
`mkdocs build --strict` to have warnings fail the build the way a broken link should.

### Social cards

Social cards are generated in CI only, because the plugin needs Cairo and would otherwise print a
screenful of `cairosvg` warnings **per page** for anyone without it. Nothing else is affected;
cards are the preview image a link unfurls into, not part of the site.

To render them locally, install Cairo and opt in:

```bash
brew install cairo                       # macOS; apt install libcairo2 on Debian/Ubuntu
export DYLD_FALLBACK_LIBRARY_PATH="$(brew --prefix)/lib"   # macOS only, see below
CI=true mkdocs serve
```

The library path is needed because the plugin looks Cairo up through `ctypes`, which does not
search Homebrew's prefix, so an installed Cairo still reports as missing without it.

## Running Music Assistant locally

These docs describe a server you will probably want running alongside them. From a
[server](https://github.com/music-assistant/server) checkout:

```bash
scripts/setup.sh              # creates .venv, installs dependencies and pre-commit hooks
source .venv/bin/activate
python -m music_assistant --log-level debug   # http://localhost:8095
```

That setup script uses uv and builds its own virtualenv, which is separate from the one this
repository uses. Activate it before running the server, or `python -m music_assistant` will not find
the package.

The server needs Python 3.14+ and ffmpeg 7+. See the server's `DEVELOPMENT.md` for building a
provider, and its `docs/architecture/README.md` for how the pieces fit together.

## How the site is published

The `build-docs` workflow deploys to GitHub Pages on a push to the default branch. It also runs
nightly, and accepts a `repository_dispatch` of type `server-docs-updated`, so documentation merged
in the server repo reaches the site without a commit here.

The workflow checks the server repo out at its `dev` branch and runs the same pull script used
above, so a local build and a deployed build see the same content.

---

[![A project from the Open Home Foundation](https://www.openhomefoundation.org/badges/ohf-project.png)](https://www.openhomefoundation.org/)
