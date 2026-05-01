"""
FFmpeg/FFprobe path resolution utility
Handles PyInstaller bundled binaries vs system installations
"""
import os
import sys
import stat
from pathlib import Path


def _ensure_executable(path: Path) -> None:
    """Ensure a binary file has execute permission (macOS/Linux)"""
    if not path.exists():
        return
    try:
        current = path.stat().st_mode
        if not (current & stat.S_IXUSR):
            path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    except OSError:
        pass


def get_ffmpeg_path() -> str:
    """Get ffmpeg path: prefer PyInstaller-bundled, fallback to system"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        for name in ["ffmpeg", "ffmpeg.exe"]:
            bundled = base_path / name
            if bundled.exists():
                _ensure_executable(bundled)
                return str(bundled)
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Get ffprobe path: prefer PyInstaller-bundled, fallback to system"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        for name in ["ffprobe", "ffprobe.exe"]:
            bundled = base_path / name
            if bundled.exists():
                _ensure_executable(bundled)
                return str(bundled)
    return "ffprobe"
