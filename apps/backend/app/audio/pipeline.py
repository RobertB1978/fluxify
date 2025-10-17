from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable, Optional

import pyloudnorm as pyln
import soundfile as sf
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3NoHeaderError
from pydub import AudioSegment


def normalize_wav(source: Path, destination: Path, target_lufs: float = -23.0) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    audio_data, sample_rate = sf.read(source)
    meter = pyln.Meter(sample_rate)
    loudness = meter.integrated_loudness(audio_data)
    normalized_audio = pyln.normalize.loudness(audio_data, loudness, target_lufs)
    sf.write(destination, normalized_audio, sample_rate)
    return destination


def concatenate_scenes(wav_files: Iterable[Path], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    combined = AudioSegment.silent(duration=0)
    for wav_file in wav_files:
        combined += AudioSegment.from_wav(wav_file)
    combined.export(destination, format="wav")
    return destination


def convert_to_mp3(source_wav: Path, destination_mp3: Path, bitrate: str = "192k") -> Path:
    destination_mp3.parent.mkdir(parents=True, exist_ok=True)
    audio = AudioSegment.from_wav(source_wav)
    audio.export(destination_mp3, format="mp3", bitrate=bitrate)
    return destination_mp3


def add_id3_tags(
    mp3_file: Path,
    title: str,
    artist: Optional[str] = None,
    album: Optional[str] = None,
    track_number: Optional[int] = None,
) -> None:
    try:
        tags = EasyID3(mp3_file)
    except ID3NoHeaderError:
        EasyID3().save(mp3_file)
        tags = EasyID3(mp3_file)

    tags["title"] = title
    if artist:
        tags["artist"] = artist
    if album:
        tags["album"] = album
    if track_number is not None:
        tags["tracknumber"] = str(track_number)
    tags.save()


def compute_checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()
