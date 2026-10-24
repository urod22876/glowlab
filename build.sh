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
# brand name is always written "GlowLab" (one word) in everything users see
python3 -I - site <<'PY'
import sys, os
d = sys.argv[1]
for n in sorted(os.listdir(d)):
    if not (n.endswith('.html') or n == '_worker.js'): continue
    p = os.path.join(d, n); s = open(p, encoding='utf-8').read()
    t = s.replace('Glow <span>Lab</span>', 'Glow<span>Lab</span>').replace('Glow Lab', 'GlowLab')
    if t != s: open(p, 'w', encoding='utf-8').write(t)
PY
rm -rf "$tmp"
echo "site built: $(du -sh site | cut -f1)"
