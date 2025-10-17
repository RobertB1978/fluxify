param(
    [string]$Python = "python"
)

$env:PYTHONPATH = "apps/backend"
& $Python -m venv .venv
& .\.venv\Scripts\pip.exe install --upgrade pip
& .\.venv\Scripts\pip.exe install -r apps/backend/requirements.txt
