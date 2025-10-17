# AI Fairytale Audio Generator

Stage 1 dostarcza backend FastAPI odpowiedzialny za generowanie scen audio, ich normalizację oraz eksport gotowych bajek do plików MP3.

## Wymagania

- Python 3.11
- [FFmpeg](https://ffmpeg.org/) z włączonym kodekiem `libmp3lame`
- [Piper TTS](https://github.com/rhasspy/piper) wraz z modelem językowym (instrukcja poniżej)
- Opcjonalnie: `make` lub PowerShell dla gotowych skryptów

## Instalacja

```bash
make setup
```

Na Windows uruchom:

```powershell
scripts\win_setup.ps1
```

## Migracje bazy danych

```bash
make migrate
```

```powershell
scripts\win_setup.ps1
scripts\win_migrate.ps1
```

## Uruchomienie serwera

```bash
make run
```

Domyślnie aplikacja nasłuchuje na porcie `8000`. Dokumentację OpenAPI znajdziesz pod `http://localhost:8000/docs`.

## Zdrowie usług

```bash
make health
```

Polecenie wysyła zapytania do `/v1/health/audio` i `/v1/health/tts`. Jeśli Piper lub model są niedostępne, endpoint TTS zwróci `503` i należy pobrać wymagane artefakty.

## Test dymny

```bash
make smoke
```

Smoke test uruchamia kompletną ścieżkę Stage 1 (generowanie scen → TTS → eksport MP3) z włączonym trybem fallback dla środowiska developerskiego. Skrypt weryfikuje również metadane ID3 w wyeksportowanym pliku.

## Piper – pobieranie i weryfikacja

1. Pobierz binarkę Piper oraz polski model głosowy (plik `*.onnx` i `*.onnx.json`).
2. Oblicz sumy SHA256:
   ```bash
   sha256sum pl_PL-voice.onnx
   sha256sum pl_PL-voice.onnx.json
   ```
3. Zaktualizuj `.env` lub zmienne środowiskowe:
   ```env
   PIPER_BINARY=/ścieżka/do/piper
   PIPER_MODEL_PATH=/ścieżka/do/pl_PL-voice.onnx
   PIPER_MODEL_CHECKSUM=<wynik sha256>
   PIPER_CONFIG_PATH=/ścieżka/do/pl_PL-voice.onnx.json
   PIPER_CONFIG_CHECKSUM=<wynik sha256>
   ```
4. Uruchom ponownie `make health`. Endpoint `/v1/health/tts` musi zwracać `{ "status": "healthy" }`.

> **Uwaga:** W środowisku developerskim można ustawić `PIPER_ENABLE_FALLBACK=true`, aby generować syntetyczne próbki audio bez zewnętrznych modeli. Health-check nadal pozostaje `unhealthy`, dzięki czemu brak zależności jest widoczny.

## Makefile

| Komenda | Opis |
| --- | --- |
| `make setup` | Tworzy środowisko wirtualne i instaluje zależności backendu |
| `make migrate` | Uruchamia migracje Alembic |
| `make health` | Odpala lokalny test health-checków |
| `make smoke` | Wykonuje scenariusz generacja → TTS → eksport |
| `make test` | Uruchamia testy jednostkowe (pytest + coverage) |
| `make lint` | Szybka weryfikacja składniowa modułów Pythona |
| `make clean` | Czyści środowisko wirtualne i artefakty |
| `make run` | Startuje serwer deweloperski (uvicorn) |

Odpowiedniki PowerShell znajdziesz w katalogu `scripts/` (`win_setup.ps1`, `win_health.ps1`, `win_smoke.ps1`).

## Zmienne środowiskowe

Pełny zestaw znajduje się w pliku [`apps/backend/.env.example`](apps/backend/.env.example).

## Co dalej? Stage 2 (stub)

Stage 2 będzie rozszerzał backend o orkiestrację kolejek (np. Redis/Celery), zaawansowane miksowanie efektów oraz eksport do formatów audiobookowych. W tym repozytorium sekcja pozostaje celowo pusta do czasu kolejnego etapu.
