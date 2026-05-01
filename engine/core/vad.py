"""
Silero VAD - Voice Activity Detection
Segments audio into speech segments (no duration limit)
"""
import torch
import torchaudio
from pathlib import Path
from typing import List, Dict
import threading


# Global lock for thread-safe VAD/torch operations
_vad_lock = threading.Lock()


class SileroVAD:
    """Silero VAD for speech segmentation"""

    def __init__(self):
        self._model = None
        self._get_speech_timestamps = None
        self._read_audio = None

    def _load(self):
        if self._model is not None:
            return

        # Use silero-vad pip package (no GitHub/torch.hub needed)
        from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
        self._model = load_silero_vad()
        self._read_audio = read_audio
        self._get_speech_timestamps = get_speech_timestamps

    def segment(self, audio_path: str) -> List[Dict]:
        """
        Segment audio into speech segments

        Args:
            audio_path: Path to audio file (any format, will be converted)

        Returns:
            List of {"start": float, "end": float} in seconds
        """
        with _vad_lock:
            self._load()

            # Read audio (silero-vad handles resampling internally)
            wav = self._read_audio(audio_path, sampling_rate=16000)

            # Get speech timestamps
            speech_timestamps = self._get_speech_timestamps(
                wav,
                self._model,
                sampling_rate=16000,
                return_seconds=True,
            )

            # Convert to our format
            segments = []
            for ts in speech_timestamps:
                segments.append({
                    "start": ts["start"],
                    "end": ts["end"],
                })

            return segments

    def detect_silence(
        self,
        audio_path: str,
        min_duration: float = 0.3,
        threshold: float = 0.5,
        margin: float = 0.12,
        margin_head: float = 0.22,
    ) -> List[Dict]:
        """
        Detect silence/breath segments (inverse of speech)

        Args:
            audio_path: Path to audio file
            min_duration: Minimum silence duration to detect
            threshold: VAD threshold
            margin: Shrink silence boundary after previous speech tail (smaller)
            margin_head: Shrink silence boundary before next speech attack/start (larger)
                       This protects the attack transient of the next sentence
                       from being cut off, preventing abrupt onsets.

        Returns:
            List of {"start": float, "end": float, "type": str, "remove": bool}
        """
        with _vad_lock:
            self._load()

            wav = self._read_audio(audio_path, sampling_rate=16000)

            # Get speech timestamps
            speech_timestamps = self._get_speech_timestamps(
                wav,
                self._model,
                sampling_rate=16000,
                return_seconds=True,
                threshold=threshold,
            )

            # Calculate silence segments (gaps between speech)
            total_duration = len(wav) / 16000
            silence_segments = []

            # Before first speech — shrink end inward (use larger head margin)
            if speech_timestamps and speech_timestamps[0]["start"] > min_duration:
                silence_segments.append({
                    "start": 0,
                    "end": max(0, speech_timestamps[0]["start"] - margin_head),
                    "type": "silence",
                    "remove": True,
                })

            # Between speech segments — ASYMMETRIC margins
            # margin_tail (smaller): after previous speech ends
            # margin_head (larger): before next speech starts — protects attack/onset
            for i in range(len(speech_timestamps) - 1):
                gap_start = speech_timestamps[i]["end"] + margin
                gap_end = speech_timestamps[i + 1]["start"] - margin_head
                gap_duration = gap_end - gap_start

                if gap_duration >= min_duration:
                    # Classify: short gaps are likely breaths, longer ones are silence
                    seg_type = "breath" if gap_duration < 1.0 else "silence"
                    silence_segments.append({
                        "start": gap_start,
                        "end": gap_end,
                        "type": seg_type,
                        "remove": True,
                    })

            # After last speech — shrink start inward (tail margin only)
            if speech_timestamps:
                last_end = speech_timestamps[-1]["end"] + margin
                if total_duration - last_end > min_duration:
                    silence_segments.append({
                        "start": last_end,
                        "end": total_duration,
                        "type": "silence",
                        "remove": True,
                    })

            return silence_segments
