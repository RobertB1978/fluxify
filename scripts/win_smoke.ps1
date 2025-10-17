$env:PYTHONPATH = "apps/backend"
$env:PIPER_ENABLE_FALLBACK = "true"
& .\.venv\Scripts\python.exe apps/backend/scripts/smoke_test.py
