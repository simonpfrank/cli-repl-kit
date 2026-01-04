#!/bin/bash
# Wrapper script to run hello-world demo

cd "$(dirname "$0")/../.."
PYTHONPATH=src:examples/hello-world python -m hello_world.cli "$@"
