"""Export API endpoints"""
import os
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from core.srt_generator import generate_srt_file

router = APIRouter()


class ExportSrtRequest(BaseModel):
    subtitles: List[dict]
    output_path: str


class ExportSrtResponse(BaseModel):
    file_path: str


@router.post("/export/srt", response_model=ExportSrtResponse)
async def export_srt(req: ExportSrtRequest):
    """Export subtitles as SRT file"""
    output_path = generate_srt_file(req.subtitles, req.output_path)
    return ExportSrtResponse(file_path=output_path)


class ExportAllRequest(BaseModel):
    subtitles: List[dict]
    subtitles_clean: Optional[List[dict]] = None
    clean_audio_path: Optional[str] = None
    output_dir: str


class ExportAllResponse(BaseModel):
    files: List[str]


@router.post("/export/all", response_model=ExportAllResponse)
async def export_all(req: ExportAllRequest):
    """Export SRT + clean audio"""
    output_dir = Path(req.output_dir)
    files = []

    # Export original SRT
    base_name = "subtitle"
    if req.clean_audio_path:
        audio_path = Path(req.clean_audio_path)
        base_name = audio_path.stem.replace("_clean", "")

    srt_path = str(output_dir / f"{base_name}.srt")
    generate_srt_file(req.subtitles_clean or req.subtitles, srt_path)
    files.append(srt_path)

    # Copy clean audio to output dir
    if req.clean_audio_path and Path(req.clean_audio_path).exists():
        import shutil
        clean_name = Path(req.clean_audio_path).name
        dest = str(output_dir / clean_name)
        if dest != req.clean_audio_path:
            shutil.copy2(req.clean_audio_path, dest)
        files.append(dest)

    return ExportAllResponse(files=files)


class ExportAudioRequest(BaseModel):
    clean_audio_path: str
    output_path: str


class ExportAudioResponse(BaseModel):
    file_path: str


@router.post("/export/audio", response_model=ExportAudioResponse)
async def export_clean_audio(req: ExportAudioRequest):
    """Export clean audio to user-specified path"""
    import shutil
    src = Path(req.clean_audio_path)
    if not src.exists():
        raise FileNotFoundError(f"Clean audio not found: {src}")
    dest = Path(req.output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dest))
    return ExportAudioResponse(file_path=str(dest))
