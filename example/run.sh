#!/bin/bash
# Wrapper script to run hello-world demo

cd "$(dirname "$0")/../.."
PYTHONPATH=.:example python -m example.cli "$@"
