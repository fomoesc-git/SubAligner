"""
SRT timestamp remapping after silence removal
"""
from typing import List, Dict


def remap_srt_timestamps(
    subtitles: List[Dict],
    removed_segments: List[Dict],
    padding: float = 0.1,
) -> List[Dict]:
    """
    Remap SRT timestamps to align with the clean audio timeline

    When silence segments are removed, all subsequent timestamps shift.
    This function calculates the new timestamps.

    Args:
        subtitles: Original subtitle entries
        removed_segments: List of segments that were removed
        padding: Padding kept around removed segments

    Returns:
        List of subtitle entries with remapped timestamps
    """
    if not subtitles or not removed_segments:
        return [_copy_sub(s) for s in subtitles]

    # Sort removed segments by start time
    sorted_removals = sorted(
        [s for s in removed_segments if s.get("remove", True)],
        key=lambda s: s["start"],
    )

    if not sorted_removals:
        return [_copy_sub(s) for s in subtitles]

    # Build cumulative offset map
    # Each removal shifts all subsequent timestamps backward
    cumulative_offset = 0.0
    offsets = []  # List of (time_threshold, total_offset_up_to_here)

    for seg in sorted_removals:
        seg_duration = seg["end"] - seg["start"]
        # Net removal = segment duration - 2x padding (kept on each side)
        # But only if padding doesn't exceed segment duration
        net_removal = seg_duration - min(2 * padding, seg_duration)
        cumulative_offset += max(0, net_removal)
        offsets.append((seg["end"], cumulative_offset))

    # Remap each subtitle timestamp
    clean_subtitles = []
    for sub in subtitles:
        new_start = _remap_time(sub["start_time"], offsets)
        new_end = _remap_time(sub["end_time"], offsets)

        # Skip subtitles that fall entirely within a removed segment
        if new_end <= new_start:
            continue

        clean_subtitles.append({
            "index": len(clean_subtitles) + 1,
            "start_time": round(new_start, 3),
            "end_time": round(new_end, 3),
            "text": sub["text"],
            "words": sub.get("words"),
        })

    # Re-index
    for i, sub in enumerate(clean_subtitles):
        sub["index"] = i + 1

    return clean_subtitles


def _remap_time(original_time: float, offsets: List[tuple]) -> float:
    """
    Remap a single timestamp

    Args:
        original_time: Original timestamp in seconds
        offsets: List of (threshold, cumulative_offset) pairs

    Returns:
        Remapped timestamp in seconds
    """
    total_offset = 0.0
    for threshold, cum_offset in offsets:
        if original_time >= threshold:
            total_offset = cum_offset
        else:
            break
    return original_time - total_offset


def _copy_sub(sub: Dict) -> Dict:
    """Deep copy a subtitle entry"""
    result = dict(sub)
    if "words" in sub and sub["words"]:
        result["words"] = [dict(w) for w in sub["words"]]
    return result
