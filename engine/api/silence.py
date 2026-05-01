"""Silence detection and removal API endpoints"""
import traceback
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from core.silence_remover import SilenceRemover
from core.srt_remapper import remap_srt_timestamps

router = APIRouter()


class SilenceConfig(BaseModel):
    min_silence_duration: float = 0.3
    keep_padding: float = 0.1
    breath_mode: str = "long_only"
    breath_threshold: float = 0.5
    vad_threshold: float = 0.5
    vad_margin: float = 0.12
    vad_margin_head: float = 0.22


class SilenceDetectRequest(BaseModel):
    audio_path: str
    config: Optional[SilenceConfig] = None


class SilenceSegment(BaseModel):
    start: float
    end: float
    type: str  # "silence" or "breath"
    remove: bool


class SilenceDetectResponse(BaseModel):
    segments: List[SilenceSegment]


@router.post("/silence/detect", response_model=SilenceDetectResponse)
async def detect_silence(req: SilenceDetectRequest):
    """Detect silence and breath segments in audio"""
    try:
        config = req.config or SilenceConfig()
        print(f"[Silence/Detect] audio_path={req.audio_path}, config={config}")
        remover = SilenceRemover()
        # Run blocking VAD/torch in thread pool to avoid blocking event loop
        segments = await asyncio.to_thread(
            remover.detect,
            req.audio_path,
            min_duration=config.min_silence_duration,
            breath_mode=config.breath_mode,
            breath_threshold=config.breath_threshold,
            margin=config.vad_margin,
            margin_head=config.vad_margin_head,
        )
        print(f"[Silence/Detect] Found {len(segments)} segments")
        return SilenceDetectResponse(
            segments=[
                SilenceSegment(
                    start=s["start"],
                    end=s["end"],
                    type=s["type"],
                    remove=s.get("remove", True),
                )
                for s in segments
            ]
        )
    except Exception as e:
        print(f"[Silence/Detect] ERROR: {e}")
        traceback.print_exc()
        raise


class SilenceRemoveRequest(BaseModel):
    audio_path: str
    segments: List[SilenceSegment]
    config: Optional[dict] = None


class SilenceRemoveResponse(BaseModel):
    clean_audio_path: str
    clean_duration: float
    removed_total: float


@router.post("/silence/remove", response_model=SilenceRemoveResponse)
async def remove_silence(req: SilenceRemoveRequest):
    """Remove silence segments and export clean audio"""
    try:
        config = req.config or {}
        removable_segments = [
            {"start": s.start, "end": s.end, "type": s.type, "remove": s.remove}
            for s in req.segments
            if s.remove
        ]
        print(f"[Silence/Remove] audio_path={req.audio_path}, "
              f"removing {len(removable_segments)} segments, config={config}")

        remover = SilenceRemover()
        # Run blocking ffmpeg operations in thread pool
        result = await asyncio.to_thread(
            remover.remove,
            req.audio_path,
            removable_segments,
            keep_padding=config.get("keep_padding", 0.1),
            crossfade=config.get("crossfade", 0.01),
            export_format=config.get("export_format", "mp3"),
        )
        print(f"[Silence/Remove] Success: clean_audio={result['clean_audio_path']}, "
              f"duration={result['clean_duration']}, removed={result['removed_total']}")
        return SilenceRemoveResponse(
            clean_audio_path=result["clean_audio_path"],
            clean_duration=result["clean_duration"],
            removed_total=result["removed_total"],
        )
    except Exception as e:
        print(f"[Silence/Remove] ERROR: {e}")
        traceback.print_exc()
        raise


class RemapSrtRequest(BaseModel):
    subtitles: List[dict]
    removed_segments: List[dict]
    padding: float = 0.1


class RemapSrtResponse(BaseModel):
    subtitles_clean: List[dict]


@router.post("/silence/remap_srt", response_model=RemapSrtResponse)
async def remap_srt(req: RemapSrtRequest):
    """Remap SRT timestamps after silence removal"""
    try:
        print(f"[Silence/RemapSrt] {len(req.subtitles)} subtitles, "
              f"{len(req.removed_segments)} removed segments, padding={req.padding}")
        clean_subs = remap_srt_timestamps(
            req.subtitles,
            req.removed_segments,
            req.padding,
        )
        print(f"[Silence/RemapSrt] Result: {len(clean_subs)} clean subtitles")
        return RemapSrtResponse(subtitles_clean=clean_subs)
    except Exception as e:
        print(f"[Silence/RemapSrt] ERROR: {e}")
        traceback.print_exc()
        raise
