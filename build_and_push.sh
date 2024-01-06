#!/bin/bash -e

# Directory of this script
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Step 1: Generate setup.cfg with the latest GN version
python3 gen_setup_cfg.py

# Extract version from setup.cfg
VERSION=$(sed -n 's/version = .*+\(.*\)/\1/p' setup.cfg)

# Step 2: Build the package
python3 setup.py sdist bdist_wheel

# Step 3: Test the package using tox
tox

# If the tests pass, proceed with the deployment
# Step 4: Commit the changes
git add setup.cfg
git commit -m "Update GN to version ${VERSION}"

# Step 5: Tag the commit
git tag -a "${VERSION}" -m "GN version ${VERSION}"

# Step 6: Push the changes and tag
git push origin main
git push origin "${VERSION}"
