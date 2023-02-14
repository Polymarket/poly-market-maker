#!/usr/bin/env bash
echo "Installing dev dependencies and activating virtualenv..."

set -e

rm -rf .venv

python3.10 -m venv .venv

source .venv/bin/activate

pip3 install --upgrade pip
pip3 install -r requirements.txt
pip3 install -r requirements-dev.txt
