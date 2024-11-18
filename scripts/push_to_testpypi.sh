#!/bin/bash

# Clean up any previous builds
rm -rf dist/

# Build the package
poetry build

# Upload to TestPyPI
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry publish -r testpypi 