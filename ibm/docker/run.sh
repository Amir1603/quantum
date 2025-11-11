#!/bin/sh
set -e

# Ensure artifacts directory exists at runtime (safe if already exists)
mkdir -p /app/artifacts

# Run whatever you pass (script + args) with the venv's python
exec python "$@"
