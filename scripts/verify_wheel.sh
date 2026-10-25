#!/usr/bin/env bash
# Build the wheel, install it (and blux-sdk) into a clean venv outside the source tree, and use it there.
set -euo pipefail
PYTHON="${PYTHON:-python3}"
SDK="${BLUX_SDK:-blux-sdk @ git+https://github.com/Outer-Void/blux.git@0b09a46a98a29cbdb108679f3ef5252b0b6881d1#subdirectory=sdk/python}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

"$PYTHON" -m build --wheel --outdir "$WORK/dist" "$ROOT" >/dev/null
"$PYTHON" -m venv "$WORK/venv"
"$WORK/venv/bin/pip" install -q "$SDK"
"$WORK/venv/bin/pip" install -q "$WORK"/dist/*.whl
cd "$WORK"
export GOD_INDEX="$WORK/index.json"
"$WORK/venv/bin/god" version
"$WORK/venv/bin/god" project "$ROOT" --json | "$WORK/venv/bin/python" -c "import json,sys; d=json.load(sys.stdin); assert d['project']['project_id']=='god', d"
"$WORK/venv/bin/god" index "$ROOT" >/dev/null
"$WORK/venv/bin/god" capabilities -r "$ROOT" --json | "$WORK/venv/bin/python" -c "import json,sys; d=json.load(sys.stdin); assert d['index']['cache']['hits']==1, d['index']"
set +e; "$WORK/venv/bin/god" capabilities -r "$WORK/missing" 2>/dev/null; code=$?; set -e
[ "$code" -eq 3 ] || { echo "expected exit 3 for a missing root, got $code" >&2; exit 1; }
echo "verify_wheel: OK"
