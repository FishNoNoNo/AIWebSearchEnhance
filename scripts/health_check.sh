#!/usr/bin/env sh
set -eu
python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:18080/health", timeout=5) as response:
    print(json.dumps(json.load(response), ensure_ascii=False, indent=2))
PY
