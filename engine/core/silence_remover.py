"""
Silence removal and audio concatenation
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict


def _run_ffmpeg(cmd: list, label: str = "ffmpeg") -> subprocess.CompletedProcess:
    """Run ffmpeg with better error reporting"""
    print(f"[{label}] Running: {' '.join(cmd[:8])}{'...' if len(cmd) > 8 else ''}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(f"[{label}] FAILED (exit {result.returncode}): {stderr[:500]}")
        raise RuntimeError(f"{label} failed (exit {result.returncode}): {stderr[:300]}")
    return result


class SilenceRemover:
    """Detect and remove silence/breath from audio"""

    def detect(
        self,
        audio_path: str,
        min_duration: float = 0.3,
        breath_mode: str = "long_only",
        breath_threshold: float = 0.5,
        margin: float = 0.12,
        margin_head: float = 0.22,
    ) -> List[Dict]:
        """
        Detect silence and breath segments

        Args:
            audio_path: Path to audio file
            min_duration: Minimum silence duration
            breath_mode: "keep" | "remove" | "long_only"
            breath_threshold: Threshold for "long_only" mode
            margin: Shrink silence boundary after previous speech tail
            margin_head: Shrink silence boundary before next speech attack (larger)

        Returns:
            List of segments with start, end, type, remove flag
        """
        from core.vad import SileroVAD
        vad = SileroVAD()

        raw_segments = vad.detect_silence(
            audio_path,
            min_duration=min_duration,
            margin=margin,
            margin_head=margin_head,
        )

        # Apply breath mode
        for seg in raw_segments:
            if seg["type"] == "breath":
                duration = seg["end"] - seg["start"]
                if breath_mode == "keep":
                    seg["remove"] = False
                elif breath_mode == "remove":
                    seg["remove"] = True
                elif breath_mode == "long_only":
                    seg["remove"] = duration >= breath_threshold
            else:
                seg["remove"] = True

        return raw_segments

    def remove(
        self,
        audio_path: str,
        segments: List[Dict],
        keep_padding: float = 0.1,
        crossfade: float = 0.01,
        export_format: str = "mp3",
    ) -> Dict:
        """
        Remove silence segments and concatenate clean audio

        Args:
            audio_path: Path to original audio
            segments: List of silence segments to remove
            keep_padding: Seconds to keep before/after speech
            crossfade: Crossfade duration for smooth joins
            export_format: Output format (mp3/flac/same)

        Returns:
            {"clean_audio_path", "clean_duration", "removed_total"}
        """
        import json

        # Resolve export format
        if export_format == "same":
            ext = Path(audio_path).suffix.lstrip(".").lower()
            if ext in ("flac", "wav"):
                export_format = "flac"
            else:
                export_format = "mp3"

        from core.audio_processor import AudioProcessor
        processor = AudioProcessor()
        wav_path = processor.preprocess(audio_path)
        print(f"[Silence/Remove] wav_path={wav_path}, export_format={export_format}")

        # Get total duration
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", str(wav_path),
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        total_duration = float(info["format"]["duration"])
        print(f"[Silence/Remove] total_duration={total_duration}")

        # Build list of segments to KEEP (inverse of removed segments)
        removable = sorted(
            [s for s in segments if s.get("remove", True)],
            key=lambda s: s["start"],
        )

        keep_segments = []
        current_pos = 0.0

        for seg in removable:
            seg_start = seg["start"]
            seg_end = seg["end"]

            # Keep audio before this silence
            keep_start = current_pos
            keep_end = max(current_pos, seg_start - keep_padding)

            if keep_end > keep_start:
                keep_segments.append({"start": keep_start, "end": keep_end})

            current_pos = min(seg_end + keep_padding, total_duration)

        # Add remaining audio after last silence
        if current_pos < total_duration:
            keep_segments.append({"start": current_pos, "end": total_duration})

        print(f"[Silence/Remove] {len(removable)} removable → {len(keep_segments)} keep segments")
        for i, ks in enumerate(keep_segments):
            print(f"  keep[{i}]: {ks['start']:.2f} - {ks['end']:.2f}")

        if not keep_segments:
            # Nothing to remove, just copy
            output_dir = Path(tempfile.gettempdir()) / "subaligner"
            output_dir.mkdir(exist_ok=True)
            stem = Path(audio_path).stem
            clean_path = str(output_dir / f"{stem}_clean.{export_format}")
            codec = "libmp3lame" if export_format == "mp3" else "flac"
            _run_ffmpeg(
                ["ffmpeg", "-y", "-i", audio_path, "-c:a", codec, "-q:a", "2", clean_path],
                label="Silence/CopyAll",
            )
            return {
                "clean_audio_path": clean_path,
                "clean_duration": total_duration,
                "removed_total": 0,
            }

        # Use ffmpeg filter_complex to concatenate segments in one pass
        output_dir = Path(tempfile.gettempdir()) / "subaligner"
        output_dir.mkdir(exist_ok=True)
        stem = Path(audio_path).stem
        clean_path = str(output_dir / f"{stem}_clean.{export_format}")

        # Build filter_complex for trimming and concatenating
        # Use multiple inputs (same file) — each input feeds one atrim
        inputs = []
        filter_parts = []
        for i, seg in enumerate(keep_segments):
            inputs.extend(["-i", wav_path])
            filter_parts.append(
                f"[{i}:a]atrim=start={seg['start']}:end={seg['end']},asetpts=PTS-STARTPTS[s{i}]"
            )

        # Concat filter — reference the named streams [s0], [s1], ...
        concat_inputs = "".join(f"[s{i}]" for i in range(len(keep_segments)))
        concat_filter = f"{concat_inputs}concat=n={len(keep_segments)}:v=0:a=1[out]"
        filter_complex = ";".join(filter_parts + [concat_filter])

        print(f"[Silence/Remove] filter_complex: {filter_complex[:200]}{'...' if len(filter_complex) > 200 else ''}")

        codec = "libmp3lame" if export_format == "mp3" else "flac"
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", filter_complex,
            "-map", "[out]",
            "-c:a", codec,
            "-q:a", "2",
            clean_path,
        ]
        _run_ffmpeg(cmd, label="Silence/Concat")

        # Get clean duration
        probe_cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_format", clean_path,
        ]
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        clean_duration = float(info["format"]["duration"])

        removed_total = total_duration - clean_duration
        print(f"[Silence/Remove] Done: clean_duration={clean_duration:.2f}, removed={removed_total:.2f}")

        return {
            "clean_audio_path": clean_path,
            "clean_duration": clean_duration,
            "removed_total": round(removed_total, 2),
        }
