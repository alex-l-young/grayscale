#!/bin/bash
# Build a standalone "Value Study.app" and a distributable zip. Run on a Mac.
set -e
cd "$(dirname "$0")"
python3 -m venv .buildenv
source .buildenv/bin/activate
pip install --upgrade pip pillow numpy pyinstaller
python make_icon.py
pyinstaller --noconfirm --clean value_study.spec
# Ad-hoc sign so Apple Silicon Macs will launch it
codesign --force --deep --sign - "dist/Value Study.app"
(cd dist && ditto -c -k --keepParent "Value Study.app" ValueStudy-mac.zip)
echo "Built dist/Value Study.app and dist/ValueStudy-mac.zip"
