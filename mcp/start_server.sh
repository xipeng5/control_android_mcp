#!/bin/bash

# Get the script directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Explicitly use the Homebrew python3.11
PYTHON="/opt/homebrew/bin/python3.11"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

# Print status to stderr so we don't break JSON-RPC on stdout
echo "[INFO] Starting Android Control MCP Server..." >&2
echo "[INFO] Script Dir: $DIR" >&2
echo "[INFO] Python Intepreter: $PYTHON" >&2

# Check/Install packages
if ! $PYTHON -c "import mcp" &> /dev/null; then
    echo "[INFO] Installing required packages (mcp, pillow)..." >&2
    $PYTHON -m pip install -r "$DIR/requirements.txt" --break-system-packages --user >&2
fi

echo "[INFO] Server launching..." >&2
echo "[INFO] Ready for JSON-RPC connections. (Press Ctrl+C to stop)" >&2

# Run the server
exec $PYTHON "$DIR/server.py"
