#!/bin/bash
set -e
python3 -m pip install --user buildozer
buildozer android debug
echo "APK files are in: bin/"
