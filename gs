#!/usr/bin/env bash
# gitSOLVE Launcher
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$DIR/.venv/bin/python" -m gitsolve.cli "$@"
