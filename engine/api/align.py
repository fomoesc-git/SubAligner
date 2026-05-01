"""Alignment API endpoints"""
import traceback
import asyncio
from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from core.aligner import AlignmentEngine
from core.text_processor import TextProcessor

router = APIRouter()
engine = AlignmentEngine()
text_processor = TextProcessor()


class AlignRequest(BaseModel):
    audio_path: str
    script_text: str
    max_chars_per_line: int = 14


class WordTimestamp(BaseModel):
    text: str
    start: float
    end: float


class SubtitleEntry(BaseModel):
    index: int
    start_time: float
    end_time: float
    text: str
    words: Optional[List[WordTimestamp]] = None


class AlignResponse(BaseModel):
    subtitles: List[SubtitleEntry]


class DebugSplitRequest(BaseModel):
    text: str


class DebugSplitResponse(BaseModel):
    original_repr: str
    char_count: int
    newline_count: int
    cr_count: int
    sentences: List[str]
    sentence_count: int


@router.post("/debug/split", response_model=DebugSplitResponse)
async def debug_split(req: DebugSplitRequest):
    """Debug endpoint: show exactly how text is split (no audio needed)"""
    sentences = text_processor.split_into_sentences(req.text)
    return DebugSplitResponse(
        original_repr=repr(req.text),
        char_count=len(req.text),
        newline_count=req.text.count('\n'),
        cr_count=req.text.count('\r'),
        sentences=sentences,
        sentence_count=len(sentences),
    )


@router.post("/align", response_model=AlignResponse)
async def align_audio(req: AlignRequest):
    """Align audio with known text to generate subtitles"""
    try:
        # Debug: log received text to verify line breaks are preserved
        has_newlines = '\n' in req.script_text or '\r' in req.script_text
        sentences = text_processor.split_into_sentences(req.script_text)
        print(f"[Align API] Received text: {len(req.script_text)} chars, "
              f"has_newlines={has_newlines}, "
              f"newlines_count={req.script_text.count(chr(10))}, "
              f"sentences={len(sentences)}")
        print(f"[Align API] Audio: {req.audio_path}, max_chars={req.max_chars_per_line}")

        # Run blocking alignment (torch + ffmpeg) in thread pool
        result = await asyncio.to_thread(
            engine.align, req.audio_path, req.script_text, req.max_chars_per_line,
        )
        print(f"[Align API] Success: {len(result)} subtitles")
        return AlignResponse(subtitles=result)
    except Exception as e:
        print(f"[Align API] ERROR: {e}")
        traceback.print_exc()
        raise
