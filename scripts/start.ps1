$ErrorActionPreference = "Stop"
$env:PYTHONPATH = (Get-Location).Path
.\.venv\Scripts\python.exe -m uvicorn src.main:app --host 0.0.0.0 --port 18080
