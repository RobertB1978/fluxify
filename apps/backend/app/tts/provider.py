from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TTSProviderError(Exception):
    """Base exception for TTS provider errors."""


class TTSModelUnavailableError(TTSProviderError):
    """Raised when required Piper model artifacts are missing."""


class TTSTransientError(TTSProviderError):
    """Raised when a transient error occurs and the operation can be retried."""


class TTSProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, destination: Path, voice: str | None = None) -> Path:
        """Generate audio for the provided text and return the destination path."""

    @abstractmethod
    def healthcheck(self) -> dict[str, str]:
        """Return health information about the provider."""
