#!/usr/bin/env bash
echo "Installing dependencies and activating virtualenv..."

set -e

if [[ "$SKIP_VIRTUAL_ENV" -eq 0 ]]; then
    echo "(re)setting virtual environment"
    rm -rf .venv/
    python3.10 -m venv .venv
    source .venv/bin/activate
fi

pip install --upgrade pip
pip3 install -r requirements.txt

echo "Installation complete!"
