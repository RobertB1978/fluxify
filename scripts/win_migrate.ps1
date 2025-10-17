$env:PYTHONPATH = "apps/backend"
& .\.venv\Scripts\alembic.exe -c apps/backend/alembic.ini upgrade head
