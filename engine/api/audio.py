"""Audio processing API endpoints"""
import os
import subprocess
import asyncio
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AudioInfoRequest(BaseModel):
    audio_path: str


class AudioInfoResponse(BaseModel):
    path: str
    duration: float
    format: str
    size: int
    sample_rate: int


@router.post("/audio/info", response_model=AudioInfoResponse)
async def get_audio_info(req: AudioInfoRequest):
    """Get audio file information using ffprobe"""
    audio_path = Path(req.audio_path)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    file_size = audio_path.stat().st_size
    file_format = audio_path.suffix.lstrip(".")

    # Get duration and sample rate using ffprobe (blocking - run in thread)
    def _probe():
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                str(audio_path),
            ],
            capture_output=True, text=True, check=True,
        )
        import json
        info = json.loads(result.stdout)
        duration = float(info.get("format", {}).get("duration", 0))
        sample_rate = 44100
        for stream in info.get("streams", []):
            if stream.get("codec_type") == "audio":
                sample_rate = int(stream.get("sample_rate", 44100))
                break
        return duration, sample_rate

    try:
        duration, sample_rate = await asyncio.to_thread(_probe)
    except Exception:
        duration = 0
        sample_rate = 44100

    return AudioInfoResponse(
        path=str(audio_path),
        duration=duration,
        format=file_format,
        size=file_size,
        sample_rate=sample_rate,
    )


class WaveformRequest(BaseModel):
    audio_path: str
    samples_per_second: int = 20


@router.post("/audio/waveform")
async def get_waveform(req: WaveformRequest):
    """Get waveform data for visualization"""
    from core.audio_processor import AudioProcessor
    processor = AudioProcessor()
    data = await asyncio.to_thread(processor.get_waveform, req.audio_path, req.samples_per_second)
    return {"waveform": data}
