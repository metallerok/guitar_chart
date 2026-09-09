#!/usr/bin/env bash
# Regenerates the test pages and captures headless-Firefox screenshots into tmp/.
# Results: read tmp/gp-test.png (PASS/FAIL panel in the top-left corner).
set -e
cd "$(dirname "$0")/.."

python3 tests/inject_tests.py

mkdir -p tmp/ffprof-t1 tmp/ffprof-t2 tmp/ffprof-t3
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t1" \
  --window-size=1500,5200 --screenshot "$PWD/tmp/gp-test.png" \
  "file://$PWD/tmp/index-test.html" 2>/dev/null
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t2" \
  --window-size=1500,5200 --screenshot "$PWD/tmp/gp-scenario.png" \
  "file://$PWD/tmp/index-scenario.html" 2>/dev/null
firefox --no-remote --headless --profile "$PWD/tmp/ffprof-t3" \
  --window-size=1500,5200 --screenshot "$PWD/tmp/gp-default.png" \
  "file://$PWD/index.html" 2>/dev/null
rm -rf tmp/ffprof-t1 tmp/ffprof-t2 tmp/ffprof-t3

ls -la tmp/*.png
