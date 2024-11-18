#!/bin/bash

# Clean up any previous builds
rm -rf dist/

# Build the package
poetry build

# Upload to PyPI
poetry publish 