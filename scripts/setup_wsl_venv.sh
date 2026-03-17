#!/bin/bash
# Setup WSL development venv (without pynput — it can't work in WSL anyway)
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Creating WSL development venv..."
python3 -m venv .venv

echo "Installing dev dependencies (no pynput)..."
.venv/bin/pip install -r requirements-dev.txt

echo ""
echo "✅ WSL venv ready!"
echo ""
echo "Activate with:"
echo "  source .venv/bin/activate.fish   # fish"
echo "  source .venv/bin/activate        # bash/zsh"
echo ""
echo "Run tests with:"
echo "  pytest tests/"
echo ""
echo "⚠️  To run the actual server (with key simulation),"
echo "    use PowerShell on Windows: scripts\\start_server.bat"
