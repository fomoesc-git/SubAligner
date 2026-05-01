"""
FFmpeg/FFprobe path resolution utility
Handles PyInstaller bundled binaries vs system installations
"""
import sys
from pathlib import Path


def get_ffmpeg_path() -> str:
    """Get ffmpeg path: prefer PyInstaller-bundled, fallback to system"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        for name in ["ffmpeg", "ffmpeg.exe"]:
            bundled = base_path / name
            if bundled.exists():
                return str(bundled)
    return "ffmpeg"


def get_ffprobe_path() -> str:
    """Get ffprobe path: prefer PyInstaller-bundled, fallback to system"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
        for name in ["ffprobe", "ffprobe.exe"]:
            bundled = base_path / name
            if bundled.exists():
                return str(bundled)
    return "ffprobe"
