from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from ..audio.pipeline import compute_checksum
from ..config import settings
from ..logging import get_logger
from .provider import TTSModelUnavailableError, TTSProvider, TTSProviderError

logger = get_logger(__name__)


@dataclass
class PiperArtifacts:
    binary: Path
    model: Path
    model_checksum: Optional[str]
    config: Path
    config_checksum: Optional[str]


class PiperTTSProvider(TTSProvider):
    def __init__(
        self,
        binary: Path | None = None,
        model: Path | None = None,
        model_checksum: str | None = None,
        config: Path | None = None,
        config_checksum: str | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
        enable_fallback: bool | None = None,
    ) -> None:
        self.artifacts = PiperArtifacts(
            binary=binary or settings.piper_binary or Path("piper"),
            model=model or settings.piper_model_path or Path("model.onnx"),
            model_checksum=model_checksum or settings.piper_model_checksum,
            config=config or settings.piper_config_path or Path("model.json"),
            config_checksum=config_checksum or settings.piper_config_checksum,
        )
        self.max_retries = max_retries or settings.piper_max_retries
        self.retry_backoff_seconds = retry_backoff_seconds or settings.piper_retry_backoff_seconds
        self.enable_fallback = enable_fallback if enable_fallback is not None else settings.piper_enable_fallback
        self._use_fallback = False

    def _validate_artifacts(self, *, strict: bool = False) -> None:
        missing: list[str] = []
        if not self.artifacts.binary or not Path(self.artifacts.binary).exists():
            missing.append("binary")
        if not self.artifacts.model or not Path(self.artifacts.model).exists():
            missing.append("model")
        if not self.artifacts.config or not Path(self.artifacts.config).exists():
            missing.append("config")

        if missing:
            if self.enable_fallback and not strict:
                self._use_fallback = True
                logger.warning(
                    "Piper artifacts missing; using synthetic fallback", extra={"missing": missing}
                )
                return
            logger.error("Piper artifacts missing: %s", ", ".join(missing))
            raise TTSModelUnavailableError(f"Missing Piper artifact(s): {', '.join(missing)}")

        if self.artifacts.model_checksum:
            checksum = compute_checksum(Path(self.artifacts.model))
            if checksum.lower() != self.artifacts.model_checksum.lower():
                if self.enable_fallback and not strict:
                    self._use_fallback = True
                    logger.warning("Model checksum mismatch; using fallback")
                    return
                raise TTSModelUnavailableError("Model checksum mismatch")

        if self.artifacts.config_checksum:
            checksum = compute_checksum(Path(self.artifacts.config))
            if checksum.lower() != self.artifacts.config_checksum.lower():
                if self.enable_fallback and not strict:
                    self._use_fallback = True
                    logger.warning("Config checksum mismatch; using fallback")
                    return
                raise TTSModelUnavailableError("Config checksum mismatch")

        self._use_fallback = False

    def _generate_fallback_audio(self, destination: Path, text: str) -> Path:
        from pydub import AudioSegment
        from pydub.generators import Sine

        duration_ms = max(1500, min(10000, len(text) * 40))
        base_tone = Sine(440).to_audio_segment(duration=duration_ms)
        overlay_tone = Sine(660).to_audio_segment(duration=duration_ms).apply_gain(-6)
        combined = base_tone.overlay(overlay_tone).fade_in(100).fade_out(200)
        destination.parent.mkdir(parents=True, exist_ok=True)
        combined.export(destination, format="wav")
        return destination

    def synthesize(self, text: str, destination: Path, voice: str | None = None) -> Path:
        self._validate_artifacts()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if self._use_fallback:
            logger.warning("Using synthetic audio fallback for Piper", extra={"destination": str(destination)})
            return self._generate_fallback_audio(destination, text)
        command = [
            str(self.artifacts.binary),
            "--model",
            str(self.artifacts.model),
            "--config",
            str(self.artifacts.config),
            "--output_file",
            str(destination),
        ]
        if voice:
            command.extend(["--speaker", voice])

        attempt = 0
        while True:
            try:
                subprocess.run(
                    command,
                    input=text.encode("utf-8"),
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                logger.info("Synthesized audio", extra={"destination": str(destination)})
                return destination
            except FileNotFoundError as exc:
                raise TTSModelUnavailableError("Piper binary not found") from exc
            except subprocess.CalledProcessError as exc:
                attempt += 1
                if attempt >= self.max_retries:
                    stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
                    raise TTSProviderError(f"Piper synthesis failed: {stderr}") from exc
                logger.warning(
                    "Piper synthesis transient failure (attempt %s/%s)",
                    attempt,
                    self.max_retries,
                )
                time.sleep(self.retry_backoff_seconds * attempt)

    def healthcheck(self) -> dict[str, str]:
        try:
            self._validate_artifacts(strict=True)
        except TTSModelUnavailableError as exc:
            return {"status": "unhealthy", "reason": str(exc)}
        return {"status": "healthy"}
