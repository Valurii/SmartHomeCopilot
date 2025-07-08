#!/bin/bash
# Install dependencies for running the test suite

set -e

python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install homeassistant pytest-homeassistant-custom-component
