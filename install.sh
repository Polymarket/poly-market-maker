#!/usr/bin/env bash
echo "Installing dependencies and activating virtualenv..."

set -e

rm -rf .venv/

python3.10 -m venv .venv

source .venv/bin/activate

pip install --upgrade pip
pip3 install -r requirements.txt

echo "Installation complete!"
