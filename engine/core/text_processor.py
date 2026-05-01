"""
Text preprocessing for alignment

Key principles:
1. Line breaks (\n, \r\n, \r) are HARD boundaries — each line is at least one sentence
2. ANY punctuation mark within a line creates a split point
3. Consecutive punctuation marks are treated as ONE split point
4. Very short fragments (< 2 content chars) are merged back
5. After splitting, all punctuation is stripped before alignment
"""
import re
from typing import List, Tuple


class TextProcessor:
    """Preprocess transcript text for alignment"""

    # All punctuation that should be stripped from final output
    ALL_PUNCT = r'[，,。！？；：、""''（）【】《》…—–·～~\-.!?;:\'"()\[\]{}<>～]'

    # All punctuation that should create a SPLIT point
    # Includes: sentence-ending, comma-level, dash, ellipsis, middle dot, etc.
    # Consecutive marks are handled by the + quantifier in the regex
    SPLIT_PUNCT = r'[。！？!?；;…，,、：:—–·～~]'

    def split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences for alignment.

        Priority:
        1. Line breaks are HARD boundaries — each line is at least one sentence
        2. ANY punctuation within a line creates a split point
        3. Consecutive punctuation marks = one split point
        4. Very short fragments (< 2 content chars) are merged back

        After splitting, punctuation is stripped from each sentence.
        """
        text = text.strip()
        if not text:
            return []

        # Step 0: Normalize line breaks — \r\n and \r both become \n
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Step 1: Split by line breaks (hard boundary)
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Step 2: For each line, split by ALL punctuation
        sentences = []
        for line in lines:
            line_sentences = self._split_line_by_punctuation(line)
            sentences.extend(line_sentences)

        # Step 3: Clean punctuation from each sentence
        cleaned = []
        for s in sentences:
            clean = self._strip_punctuation(s)
            if clean:
                cleaned.append(clean)

        return cleaned if cleaned else [self._strip_punctuation(text)]

    def _split_line_by_punctuation(self, line: str) -> List[str]:
        """
        Split a single line by ALL punctuation marks.

        Every punctuation mark creates a split. Consecutive punctuation
        marks (like ！！ or —— or ……) are treated as a single split point.
        Very short trailing fragments (< 2 content chars) are merged back.
        """
        # Split by punctuation, keeping punctuation as separate parts
        # The + quantifier groups consecutive punctuation together
        parts = re.split(f'({self.SPLIT_PUNCT}+)', line)

        # Reassemble: each segment includes its trailing punctuation
        segments = []
        current = ""
        for part in parts:
            current += part
            if re.match(f'^{self.SPLIT_PUNCT}+$', part):
                segments.append(current.strip())
                current = ""

        if current.strip():
            segments.append(current.strip())

        # Merge very short trailing fragments (< 2 content chars) with previous segment
        merged = []
        for seg in segments:
            clean = self._strip_punctuation(seg)
            if merged and len(clean) < 2:
                merged[-1] = merged[-1] + seg
            else:
                merged.append(seg)

        return merged if merged else segments

    def _strip_punctuation(self, text: str) -> str:
        """Remove all punctuation from text, keep only content characters"""
        clean = re.sub(self.ALL_PUNCT, '', text)
        clean = re.sub(r'\s+', ' ', clean).strip()
        return clean

    def clean_text(self, text: str) -> str:
        """
        Clean text for alignment:
        - Remove content in brackets (stage directions)
        - Normalize whitespace
        """
        text = re.sub(r'[\[【（(].*?[\]】）)]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def get_sentence_char_counts(self, sentences: List[str]) -> List[int]:
        """Get character count for each sentence (excluding spaces)"""
        return [len(s.replace(" ", "")) for s in sentences]

    def get_sentence_boundaries(self, sentences: List[str]) -> List[Tuple[int, int]]:
        """
        Get character position boundaries for each sentence in the full text.
        Returns list of (start, end) tuples.
        """
        boundaries = []
        pos = 0
        for s in sentences:
            length = len(s.replace(" ", ""))
            boundaries.append((pos, pos + length))
            pos += length
        return boundaries
