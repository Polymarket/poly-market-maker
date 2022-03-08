#!/usr/bin/env bash
echo "Installing dependencies and activating virtualenv..."

rm -rf .venv/

python3.9 -m venv .venv

source .venv/bin/activate

pip3 install -r requirements.txt

echo "Installation complete!"