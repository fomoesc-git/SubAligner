"""
SRT subtitle generation from word timestamps
"""
from typing import List, Dict


def group_words_into_subtitles(
    words: List[Dict],
    max_chars_per_line: int = 14,
) -> List[Dict]:
    """
    Group word-level timestamps into subtitle entries

    Args:
        words: List of {"text", "start", "end"} word entries
        max_chars_per_line: Max characters per subtitle line

    Returns:
        List of subtitle entries with index, start_time, end_time, text, words
    """
    if not words:
        return []

    subtitles = []
    current_words = []
    current_chars = 0

    for word in words:
        char_count = len(word["text"])

        # Check if adding this word exceeds the limit
        if current_chars + char_count > max_chars_per_line and current_words:
            # Flush current subtitle
            subtitles.append(_make_subtitle_entry(len(subtitles) + 1, current_words))
            current_words = []
            current_chars = 0

        current_words.append(word)
        current_chars += char_count

    # Flush remaining words
    if current_words:
        subtitles.append(_make_subtitle_entry(len(subtitles) + 1, current_words))

    return subtitles


def _make_subtitle_entry(index: int, words: List[Dict]) -> Dict:
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


def format_timestamp(seconds: float) -> str:
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds % 1) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def generate_srt_content(subtitles: List[Dict]) -> str:
    """
    Generate SRT format string from subtitle entries

    Args:
        subtitles: List of subtitle entries

    Returns:
        SRT formatted string
    """
    lines = []
    for entry in subtitles:
        start = format_timestamp(entry["start_time"])
        end = format_timestamp(entry["end_time"])
        lines.append(f"{start} --> {end}")
        lines.append(entry["text"])
        lines.append("")  # Blank line between entries

    return "\r\n".join(lines)


def generate_srt_file(subtitles: List[Dict], output_path: str) -> str:
    """
    Write SRT content to file

    Args:
        subtitles: List of subtitle entries
        output_path: Path to output SRT file

    Returns:
        Path to written file
    """
    from pathlib import Path
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = generate_srt_content(subtitles)
    output_path.write_text(content, encoding="utf-8")

    return str(output_path)
