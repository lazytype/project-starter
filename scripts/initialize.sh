#!/usr/bin/env bash

set -e

if [[ $(command -v dotslash || true) == "" ]]; then
    echo "Error: Please install DotSlash first and add it to your PATH."
    exit 1
fi

if [[ $(command -v direnv || true) == "" ]]; then
    echo "Warning: direnv is not installed. It's recommended to install direnv and add it to your PATH."
fi

bin/uv venv --clear
lefthook install
