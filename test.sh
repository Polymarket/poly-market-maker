#!/usr/bin/env bash
echo "Installing dependencies and activating virtualenv..."

set -e

echo $SKIP_VIRTUAL_ENV
if [[ -n "$SKIP_VIRTUAL_ENV" ]]; then
    echo "Set"
fi

if [[ "$SKIP_VIRTUAL_ENV" -gt 0 ]]; then
    echo "true"
fi

echo "here"
