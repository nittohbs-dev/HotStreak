#!/bin/sh
set -eu
cd "$(dirname "$0")"
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
exec uv run --python 3.12 --with-requirements requirements.txt python -B -m hotstreak_display.app "$@"
