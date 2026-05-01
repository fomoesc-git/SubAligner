/**
 * Format seconds to SRT timestamp: HH:MM:SS,mmm
 */
export function formatTimestamp(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 1000);
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")},${ms.toString().padStart(3, "0")}`;
}

/**
 * Parse SRT timestamp to seconds
 */
export function parseTimestamp(ts: string): number | null {
  const match = ts.match(/(\d{2}):(\d{2}):(\d{2})[,.](\d{3})/);
  if (!match) return null;
  const [, h, m, s, ms] = match;
  return parseInt(h) * 3600 + parseInt(m) * 60 + parseInt(s) + parseInt(ms) / 1000;
}

/**
 * Generate SRT content string from subtitle entries
 */
export function generateSrtContent(
  subtitles: { index: number; start_time: number; end_time: number; text: string }[]
): string {
  return subtitles
    .map((entry) => {
      const start = formatTimestamp(entry.start_time);
      const end = formatTimestamp(entry.end_time);
      return `${entry.index}\r\n${start} --> ${end}\r\n${entry.text}\r\n`;
    })
    .join("\r\n");
}
