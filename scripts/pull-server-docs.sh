#!/usr/bin/env bash
# Pull the architecture and package docs out of the server repo so the site can render them.
#
# In CI the workflow checks the server out first and passes its path. Locally, point this at your
# own checkout before running `mkdocs serve`:
#
#   scripts/pull-server-docs.sh ../music-assistant-server
#
# With no argument it clones the default branch into a temporary directory.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ $# -ge 1 ]; then
  server="$1"
else
  server="$(mktemp -d)/server"
  echo "Cloning music-assistant/server into ${server}"
  git clone --depth 1 --branch dev https://github.com/music-assistant/server.git "${server}"
fi

python scripts/pull_server_docs.py "${server}" --output docs
