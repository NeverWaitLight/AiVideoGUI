#!/bin/bash
set -e

echo "Compiling Qt resources..."
uv run pyside6-rcc resources.qrc -o resources_rc.py

echo "Starting application..."
uv run main.py
