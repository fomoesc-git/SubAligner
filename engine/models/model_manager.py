"""
Model download and management
Supports ModelScope (China) as primary source, HuggingFace as fallback
"""
import os
import shutil
from pathlib import Path
from typing import Optional


class ModelManager:
    """Manage AI model downloads and loading"""

    # ModelScope mirror (fast in China)
    MODELSCOPE_WAV2VEC2 = "AI-ModelScope/wav2vec2-base-960h"

    def __init__(self):
        self.model_dir = self._get_model_dir()

    def _get_model_dir(self) -> Path:
        """Get model storage directory"""
        home = Path.home()
        model_dir = home / ".subaligner" / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        return model_dir

    def _is_china_network(self) -> bool:
        """Detect if we're in China (can't reach HuggingFace directly)"""
        import urllib.request
        try:
            req = urllib.request.Request("https://huggingface.co", method="HEAD")
            urllib.request.urlopen(req, timeout=5)
            return False
        except Exception:
            return True

    def is_model_ready(self) -> bool:
        """Check if alignment model is available"""
        model_path = self.get_model_path()
        return model_path is not None

    def get_model_path(self) -> Optional[Path]:
        """Get path to downloaded model, or None"""
        # Check our custom model directory
        wav2vec2_dir = self.model_dir / "wav2vec2_base_960h"
        if wav2vec2_dir.exists() and (wav2vec2_dir / ".downloaded").exists():
            # Verify it has actual model files
            if (wav2vec2_dir / "config.json").exists():
                return wav2vec2_dir

        # Check HuggingFace cache
        hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
        if hf_cache.exists():
            for d in hf_cache.iterdir():
                if d.is_dir() and "wav2vec2-base-960h" in d.name:
                    snap = d / "snapshots"
                    if snap.exists():
                        for s in snap.iterdir():
                            if (s / "config.json").exists():
                                return s

        # Check torch hub cache (torchaudio pipeline download)
        hub_dir = Path.home() / ".cache" / "torch" / "hub"
        if hub_dir.exists():
            for d in hub_dir.iterdir():
                if d.is_dir() and "wav2vec2" in d.name.lower():
                    return d

        return None

    def download_model(self):
        """
        Download the alignment model (wav2vec2) and Silero VAD

        Auto-detects network and uses ModelScope (China) or HuggingFace
        Silero VAD is loaded from pip package (no separate download needed)
        """
        # Step 1: Download wav2vec2 model
        print("Downloading wav2vec2 model...")
        self._download_wav2vec2()
        print("wav2vec2 model downloaded successfully")

        # Step 2: Verify Silero VAD is available (loaded via pip package)
        print("Verifying Silero VAD...")
        self._verify_silero_vad()
        print("Silero VAD ready")

        # Mark as downloaded
        marker = self.model_dir / "wav2vec2_base_960h"
        marker.mkdir(exist_ok=True)
        (marker / ".downloaded").write_text("1")

    def _download_wav2vec2(self):
        """Download wav2vec2 model, using ModelScope for China"""
        if self._is_china_network():
            print("[Network] Detected China network, using ModelScope mirror...")
            self._download_wav2vec2_modelscope()
        else:
            print("[Network] Using HuggingFace directly...")
            self._download_wav2vec2_hf()

    def _download_wav2vec2_modelscope(self):
        """Download wav2vec2 from ModelScope (fast in China)"""
        try:
            from modelscope import snapshot_download
        except ImportError:
            try:
                from modelscope.hub.snapshot_download import snapshot_download
            except ImportError:
                raise RuntimeError(
                    "modelscope 未安装，请运行: pip install modelscope"
                )

        cache_dir = str(self.model_dir / "modelscope_cache")
        model_dir = snapshot_download(
            self.MODELSCOPE_WAV2VEC2,
            cache_dir=cache_dir,
        )
        # Copy model files to our expected location
        target = self.model_dir / "wav2vec2_base_960h"
        target.mkdir(exist_ok=True)
        src = Path(model_dir)
        for f in src.iterdir():
            if f.is_file():
                dest = target / f.name
                if not dest.exists():
                    shutil.copy2(str(f), str(dest))

    def _download_wav2vec2_hf(self):
        """Download wav2vec2 from HuggingFace directly"""
        import torchaudio
        bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        model = bundle.get_model()
        del model  # Just download, don't keep in memory

    def _verify_silero_vad(self):
        """Verify Silero VAD is available via pip package"""
        try:
            from silero_vad import load_silero_vad
            model = load_silero_vad()
            del model
        except ImportError:
            raise RuntimeError(
                "silero-vad package not installed. "
                "Please run: pip install silero-vad"
            )

    def delete_model(self):
        """Delete downloaded model files"""
        # Remove our marker
        marker = self.model_dir / "wav2vec2_base_960h"
        if marker.exists():
            shutil.rmtree(marker)

        # Remove ModelScope cache
        ms_cache = self.model_dir / "modelscope_cache"
        if ms_cache.exists():
            shutil.rmtree(ms_cache)

        # Note: torch hub / HF cache not removed (may be used by other apps)
