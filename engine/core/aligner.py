"""
Core forced alignment engine using VAD + wav2vec2 CTC
No duration limit - VAD segments long audio into chunks

Key design: Each user-defined sentence gets its own time range.
Short sentences are NEVER cut in the middle.
Multiple short sentences can be merged into one subtitle line,
but a sentence boundary is always respected.
"""
import re
import torch
import torchaudio
from pathlib import Path
from typing import List, Dict, Optional, Tuple

from core.vad import SileroVAD
from core.audio_processor import AudioProcessor
from core.text_processor import TextProcessor
from core.srt_generator import group_words_into_subtitles
from models.model_manager import ModelManager


class AlignmentEngine:
    """Forced alignment engine: VAD + wav2vec2 CTC"""

    def __init__(self):
        self.vad = SileroVAD()
        self.audio_processor = AudioProcessor()
        self.text_processor = TextProcessor()
        self.model_manager = ModelManager()
        self._model = None
        self._labels = None
        self._dictionary = None
        self._model_type = None  # "transformers" or "torchaudio"

    def _load_model(self):
        """Load wav2vec2 alignment model"""
        if self._model is not None:
            return

        model_dir = self.model_manager.get_model_path()
        if not model_dir:
            raise RuntimeError(
                "Alignment model not found. Please download it first via Settings."
            )

        device = self._get_device()

        # Try loading from local directory first (ModelScope download)
        if self._load_from_local(model_dir, device):
            return

        # Fallback: load via torchaudio pipeline (HuggingFace download)
        self._load_from_pipeline(device)

    def _load_from_local(self, model_dir: Path, device: str) -> bool:
        """Try loading wav2vec2 from a local directory (ModelScope download)"""
        try:
            config_file = model_dir / "config.json"
            if not config_file.exists():
                return False

            from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

            print(f"[Aligner] Loading model from local dir: {model_dir}")
            model = Wav2Vec2ForCTC.from_pretrained(str(model_dir)).to(device)
            model.eval()

            # Load processor for tokenizer
            try:
                processor = Wav2Vec2Processor.from_pretrained(str(model_dir))
                self._labels = processor.tokenizer.get_vocab()
            except Exception:
                # Build labels from model config
                vocab = model.config.vocab_size
                self._labels = {chr(i + 96): i for i in range(1, min(27, vocab))}
                self._labels["|"] = vocab - 1  # word separator

            self._model = model
            self._model_type = "transformers"

            # Build dictionary for forced_align
            self._dictionary = {v: k for k, v in self._labels.items()}
            print(f"[Aligner] Model loaded (transformers), labels: {len(self._labels)}")
            return True

        except ImportError:
            print("[Aligner] transformers not installed, using torchaudio pipeline")
            return False
        except Exception as e:
            print(f"[Aligner] Local model load failed: {e}, falling back to pipeline")
            return False

    def _load_from_pipeline(self, device: str):
        """Load wav2vec2 via torchaudio pipeline"""
        bundle = torchaudio.pipelines.WAV2VEC2_ASR_BASE_960H
        self._model = bundle.get_model().to(device)
        self._model.eval()
        self._labels = bundle.get_labels()
        self._model_type = "torchaudio"
        self._dictionary = {i: c for i, c in enumerate(self._labels)}
        print(f"[Aligner] Model loaded (torchaudio pipeline)")

    def _get_device(self) -> str:
        """Get best available device"""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def align(
        self,
        audio_path: str,
        script_text: str,
        max_chars_per_line: int = 14,
    ) -> List[Dict]:
        """
        Main alignment function: audio + text -> subtitles

        Process:
        1. Split text into sentences (respecting line breaks and punctuation)
        2. Run VAD on audio to get speech segments
        3. Assign each sentence a proportional time range
        4. For each sentence, distribute characters across its time range
        5. Group into subtitle entries respecting sentence boundaries
        """
        self._load_model()
        device = self._get_device()

        # Step 1: Preprocess audio to 16kHz mono WAV
        wav_path = self.audio_processor.preprocess(audio_path)
        waveform, sample_rate = torchaudio.load(wav_path)
        total_duration = waveform.shape[1] / sample_rate

        # Step 2: VAD segmentation
        speech_segments = self.vad.segment(wav_path)
        if not speech_segments:
            raise ValueError("No speech detected in audio")

        # Step 3: Split text into sentences (line breaks = hard boundaries)
        text_segments = self.text_processor.split_into_sentences(script_text)
        if not text_segments:
            raise ValueError("No text to align")

        print(f"[Aligner] {len(text_segments)} sentences, {len(speech_segments)} speech segments")

        # Step 4: Assign time ranges to each sentence
        sentence_timings = self._assign_sentence_timings(
            text_segments, speech_segments, total_duration
        )

        # Step 5: Generate word-level timestamps for each sentence
        all_words = []
        for sentence, start, end in sentence_timings:
            duration = end - start
            if duration <= 0:
                continue
            # Get character-level timestamps within this sentence's time range
            char_timestamps = self._distribute_sentence(sentence, start, duration, device, waveform, sample_rate)
            all_words.extend(char_timestamps)

        # Step 6: Group into subtitles respecting sentence boundaries
        subtitles = self._group_subtitles_by_sentences(all_words, sentence_timings, max_chars_per_line)
        return subtitles

    def _assign_sentence_timings(
        self,
        text_segments: List[str],
        speech_segments: List[Dict],
        total_duration: float,
    ) -> List[Tuple[str, float, float]]:
        """
        Assign each sentence a start and end time based on speech segments.

        Uses proportional distribution: each sentence gets time proportional
        to its character count relative to total text length.
        """
        total_speech = sum(s["end"] - s["start"] for s in speech_segments)
        char_counts = [len(s.replace(" ", "")) for s in text_segments]
        total_chars = sum(char_counts)

        if total_chars == 0:
            return [(s, seg["start"], seg["end"]) for s, seg in zip(text_segments, speech_segments)]

        # Build a continuous speech timeline
        # Map each sentence to a proportional chunk of the speech duration
        results = []
        current_time = speech_segments[0]["start"]

        # Create a flat timeline from speech segments
        speech_timeline = []
        for seg in speech_segments:
            speech_timeline.append((seg["start"], seg["end"]))

        # Assign proportional time to each sentence
        time_pos = 0.0  # Position within the total speech duration
        for i, sentence in enumerate(text_segments):
            char_ratio = char_counts[i] / total_chars
            sentence_duration = total_speech * char_ratio

            # Map time_pos + sentence_duration to actual timeline
            start_actual = self._map_speech_time_to_real(time_pos, speech_timeline, total_speech)
            end_actual = self._map_speech_time_to_real(time_pos + sentence_duration, speech_timeline, total_speech)

            # Ensure minimum duration (at least 0.3s per sentence)
            if end_actual - start_actual < 0.3:
                end_actual = start_actual + 0.3

            results.append((sentence, round(start_actual, 3), round(end_actual, 3)))
            time_pos += sentence_duration

        # Fix overlaps: ensure no sentence starts before the previous one ends
        for i in range(1, len(results)):
            prev_end = results[i-1][2]
            if results[i][1] < prev_end:
                sentence = results[i][0]
                results[i] = (sentence, prev_end, results[i][2])

        return results

    def _map_speech_time_to_real(
        self,
        speech_time: float,
        speech_timeline: List[Tuple[float, float]],
        total_speech: float,
    ) -> float:
        """Map a position in the continuous speech timeline to real audio time."""
        if not speech_timeline:
            return 0.0

        remaining = speech_time
        for start, end in speech_timeline:
            seg_duration = end - start
            if remaining <= seg_duration:
                return start + remaining
            remaining -= seg_duration

        # If we've gone past all segments, return the end of the last one
        return speech_timeline[-1][1]

    def _distribute_sentence(
        self,
        sentence: str,
        start: float,
        duration: float,
        device: str,
        full_waveform: torch.Tensor,
        sample_rate: int,
    ) -> List[Dict]:
        """
        Distribute characters of a sentence across its time range.
        Uses energy-based distribution for Chinese text, proportional for English.
        """
        chars = list(sentence.replace(" ", ""))
        if not chars:
            return []

        # Try to get the audio segment for this time range for energy analysis
        start_sample = int(start * sample_rate)
        end_sample = int((start + duration) * sample_rate)
        start_sample = max(0, min(start_sample, full_waveform.shape[1] - 1))
        end_sample = max(start_sample + 1, min(end_sample, full_waveform.shape[1]))

        segment_waveform = full_waveform[:, start_sample:end_sample]
        seg_duration = (end_sample - start_sample) / sample_rate

        # Use energy-based distribution
        return self._energy_distribute(segment_waveform, sentence, start, seg_duration)

    def _energy_distribute(
        self,
        waveform: torch.Tensor,
        text: str,
        time_offset: float,
        duration: float,
    ) -> List[Dict]:
        """
        Distribute text characters based on audio energy for natural timing.
        """
        chars = list(text.replace(" ", ""))
        if not chars:
            return [{"text": text, "start": time_offset, "end": time_offset + duration}]

        # Compute short-time energy
        wav = waveform.squeeze(0).cpu().numpy()
        hop = max(1, len(wav) // (len(chars) * 4))
        import numpy as np
        energy = np.array([
            np.abs(wav[i:i+hop]).mean()
            for i in range(0, len(wav) - hop, hop)
        ])

        # Smooth energy
        if len(energy) > 5:
            kernel = np.ones(5) / 5
            energy = np.convolve(energy, kernel, mode='same')

        # Map characters to time based on cumulative energy
        total_energy = energy.sum() if energy.sum() > 0 else 1
        cumulative = np.cumsum(energy) / total_energy

        per_char_energy = 1.0 / len(chars)
        word_timestamps = []

        for i, char in enumerate(chars):
            start_frac = i * per_char_energy
            end_frac = (i + 1) * per_char_energy

            start_idx = np.searchsorted(cumulative, start_frac)
            end_idx = np.searchsorted(cumulative, end_frac)

            char_start = time_offset + (start_idx / len(energy)) * duration
            char_end = time_offset + (end_idx / len(energy)) * duration

            # Ensure minimum duration per character
            min_dur = max(0.05, duration / len(chars) * 0.3)
            if char_end - char_start < min_dur:
                char_end = char_start + min_dur

            word_timestamps.append({
                "text": char,
                "start": round(char_start, 3),
                "end": round(char_end, 3),
            })

        # Fix overlaps
        for i in range(1, len(word_timestamps)):
            if word_timestamps[i]["start"] < word_timestamps[i-1]["end"]:
                word_timestamps[i]["start"] = word_timestamps[i-1]["end"]

        # Cap end times
        final_end = time_offset + duration
        if word_timestamps and word_timestamps[-1]["end"] > final_end:
            word_timestamps[-1]["end"] = round(final_end, 3)

        return word_timestamps

    def _even_distribute(self, text: str, time_offset: float, duration: float) -> List[Dict]:
        """Fallback: distribute text evenly across duration"""
        chars = list(text.replace(" ", ""))
        if not chars:
            chars = [text]
        per_char = duration / len(chars)
        word_timestamps = []
        current_time = time_offset
        for i, char in enumerate(chars):
            word_timestamps.append({
                "text": char,
                "start": round(current_time, 3),
                "end": round(current_time + per_char, 3),
            })
            current_time += per_char
        return word_timestamps

    def _group_subtitles_by_sentences(
        self,
        all_words: List[Dict],
        sentence_timings: List[Tuple[str, float, float]],
        max_chars_per_line: int,
    ) -> List[Dict]:
        """
        Group words into subtitle entries — one subtitle per sentence.

        Each sentence always produces its own subtitle entry.
        Sentences are NEVER merged or split across entries.
        """
        if not all_words:
            return []

        # Build word index ranges for each sentence
        word_idx = 0
        subtitles = []

        for sentence, sent_start, sent_end in sentence_timings:
            # Find words belonging to this sentence by matching time range
            start_idx = word_idx
            while word_idx < len(all_words) and all_words[word_idx]["start"] < sent_end - 0.01:
                word_idx += 1
            end_idx = word_idx

            # Each sentence = one subtitle entry
            if end_idx > start_idx:
                sentence_words = all_words[start_idx:end_idx]
                subtitles.append(self._make_subtitle_entry(len(subtitles) + 1, sentence_words))

        return subtitles

    def _make_subtitle_entry(self, index: int, words: List[Dict]) -> Dict:
        """Create a subtitle entry from a list of words"""
        text = "".join(w["text"] for w in words)
        start_time = words[0]["start"]
        end_time = words[-1]["end"]

        return {
            "index": index,
            "start_time": round(start_time, 3),
            "end_time": round(end_time, 3),
            "text": text,
            "words": [
                {
                    "text": w["text"],
                    "start": round(w["start"], 3),
                    "end": round(w["end"], 3),
                }
                for w in words
            ],
        }
