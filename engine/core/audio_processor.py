"""
Audio preprocessing utilities
"""
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List
from core.ffmpeg_utils import get_ffmpeg_path


class AudioProcessor:
    """Audio file preprocessing and waveform extraction"""

    def preprocess(self, audio_path: str) -> str:
        """
        Convert any audio to 16kHz mono WAV for model input

        Args:
            audio_path: Path to original audio file

        Returns:
            Path to preprocessed WAV file
        """
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Output to temp directory
        output_dir = Path(tempfile.gettempdir()) / "subaligner"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{audio_path.stem}_16k.wav"

        # Skip if already preprocessed and source hasn't changed
        if output_path.exists():
            src_mtime = audio_path.stat().st_mtime
            out_mtime = output_path.stat().st_mtime
            if out_mtime > src_mtime:
                return str(output_path)

        # Convert using ffmpeg
        cmd = [
            get_ffmpeg_path(), "-y", "-i", str(audio_path),
            "-ar", "16000",       # 16kHz sample rate
            "-ac", "1",           # mono
            "-f", "wav",
            str(output_path),
        ]

        try:
            subprocess.run(
                cmd, capture_output=True, text=True, check=True,
            )
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Please install ffmpeg first, or use the bundled version.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Audio preprocessing failed: {e.stderr}")

        return str(output_path)

    def get_waveform(self, audio_path: str, samples_per_second: int = 20) -> List[float]:
        """
        Get waveform amplitude data for visualization

        Args:
            audio_path: Path to audio file
            samples_per_second: Number of amplitude samples per second

        Returns:
            List of amplitude values normalized to [-1, 1]
        """
        import numpy as np

        wav_path = self.preprocess(audio_path)

        # Use ffmpeg to get raw PCM data
        cmd = [
            get_ffmpeg_path(), "-i", wav_path,
            "-f", "s16le",       # 16-bit PCM
            "-ac", "1",           # mono
            "-ar", "8000",        # Downsample for visualization
            "pipe:1",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            raw_data = np.frombuffer(result.stdout, dtype=np.int16)
            # Normalize to [-1, 1]
            waveform = raw_data.astype(np.float32) / 32768.0

            # Downsample to target rate
            if samples_per_second > 0:
                target_len = int(len(waveform) * samples_per_second / 8000)
                if target_len > 0 and target_len < len(waveform):
                    indices = np.linspace(0, len(waveform) - 1, target_len, dtype=int)
                    waveform = waveform[indices]

            return waveform.tolist()
        except Exception as e:
            return []
