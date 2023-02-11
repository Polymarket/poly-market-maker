#!/usr/bin/env bash

cd "$(dirname "$0")"

set -e

rm -rf .venv
virtualenv .venv
source .venv/bin/activate

# The advantage of using this method, in contrary to just calling `pip install -r requirements.txt` several times,
# is that it can detect different versions of the same dependency and fail with a "Double requirement given"
# error message.
pip install requirements.text

# install development requirements
pip install -r requirements-dev.txt
