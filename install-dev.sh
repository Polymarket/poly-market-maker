#!/usr/bin/env bash
echo "Installing dev dependencies and activating virtualenv..."

set -e

rm -rf .venv

python3.10 -m venv .venv

source .venv/bin/activate

pip install --upgrade pip
pip install requirements.text
pip install -r requirements-dev.txt
