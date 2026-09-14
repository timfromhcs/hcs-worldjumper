#!/usr/bin/env bash
# HCS WorldJumper Linux Desktop Launcher
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$DIR"

echo "Launching HCS WorldJumper on Linux..."

# Check Python3
if command -v python3 &>/dev/null; then
    python3 desktop/app.py
elif command -v python &>/dev/null; then
    python desktop/app.py
else
    echo "Error: Python 3 runtime is required to launch HCS WorldJumper."
    exit 1
fi
