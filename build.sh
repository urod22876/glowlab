#!/usr/bin/env bash
# Builds the site into ./site from the sources in ./build:
#   build/base     - the original light site (input)
#   build_dark.py  - dark monochrome theme, hero, guides, scoring, result window, legal pages
#   build_pro.py   - Glow Lab Pro: payments check, plan, faces, progress, settings, assistant, _worker.js
set -euo pipefail
cd "$(dirname "$0")"
tmp="$(mktemp -d)"
python3 -I build/build_dark.py build/base "$tmp/site"
python3 -I build/build_pro.py "$tmp/site"
rm -rf site && mkdir site && cp -r "$tmp/site/." site/
rm -rf "$tmp"
echo "site built: $(du -sh site | cut -f1)"
