# Stage 1 Audit Report

| Element | Status (before) | Status (after) | Akcja | Plik(i) |
| --- | --- | --- | --- | --- |
| FastAPI backend skeleton | ❌ | ✅ | Utworzyć strukturę aplikacji FastAPI z routerami i konfiguracją | apps/backend/app/main.py |
| SQLite + SQLAlchemy modele | ❌ | ✅ | Zaimplementować modele ORM i konfigurację bazy | apps/backend/app/models/* |
| Migracje Alembic | ❌ | ✅ | Dodać konfigurację Alembic i migrację początkową | apps/backend/alembic/* |
| Endpoints Stage 1 | ❌ | ✅ | Zaimplementować wymagane endpointy API | apps/backend/app/api/routes/* |
| TTS provider Piper | ❌ | ⚠️ | Dodać interfejs providera i implementację Piper (wymaga dostarczenia modeli) | apps/backend/app/tts/* |
| Audio pipeline | ❌ | ✅ | Dostarczyć funkcje normalizacji/konwersji audio | apps/backend/app/audio/pipeline.py |
| Zadania BackgroundTasks | ❌ | ✅ | Obsłużyć kolejkę zadań TTS i eksportu | apps/backend/app/services/jobs.py |
| Modele danych i statusy | ❌ | ✅ | Zaimplementować Project/Scene/Render/Job/Asset | apps/backend/app/models/entities.py |
| Health-checki audio/TTS | ❌ | ⚠️ | Zapewnić endpointy /health/audio i /health/tts (zależne od FFmpeg/Piper) | apps/backend/app/api/routes/health.py |
| Eksport MP3 i streaming ZIP | ❌ | ✅ | Dodać pipeline eksportu i streaming pliku | apps/backend/app/api/routes/exports.py |
| Konfiguracja .env example | ❌ | ✅ | Przygotować przykład zmiennych środowiskowych | apps/backend/.env.example |
| Requirements backend | ❌ | ✅ | Pinować zależności w requirements.txt | apps/backend/requirements.txt |
| Makefile / skrypty | ❌ | ✅ | Przygotować komendy make i skrypty PowerShell | Makefile, scripts/* |
| README Stage 1 | ❌ | ✅ | Zaktualizować instrukcje uruchomienia Stage 1 | README.md |
| Logowanie z rotacją | ❌ | ✅ | Skonfigurować logging z rotacją dzienną i request_id | apps/backend/app/logging.py, services |
| Rate limiting | ❌ | ✅ | Dodać ograniczanie zapytań na endpointach | apps/backend/app/api/deps/db.py |
| Checksum Piper | ❌ | ✅ | Weryfikować SHA256 modeli Piper | apps/backend/app/tts/piper_provider.py |
| TODO manual required | ❌ | ✅ | Utworzyć listę manualnych kroków | TODO.md |
