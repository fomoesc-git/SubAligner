import { invoke } from "@tauri-apps/api/core";
import { open, save } from "@tauri-apps/plugin-dialog";
import { listen } from "@tauri-apps/api/event";
import { useSettingsStore } from "../stores/settings";
import type { SubtitleEntry } from "../stores/project";

async function request(path: string, options?: RequestInit, retries: number = 2): Promise<any> {
  const settings = useSettingsStore();
  if (!settings.enginePort) {
    throw new Error("引擎未启动，请等待引擎启动后重试");
  }
  const url = `http://127.0.0.1:${settings.enginePort}${path}`;

  for (let attempt = 0; attempt <= retries; attempt++) {
    let res: Response;
    try {
      const controller = new AbortController();
      const isHeavyOp = path.includes("align");
      const timeoutMs = isHeavyOp ? 300000 : 60000;
      const timer = setTimeout(() => controller.abort(), timeoutMs);

      res = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        ...options,
      });
      clearTimeout(timer);
    } catch (fetchErr: any) {
      const msg = fetchErr?.message || String(fetchErr);
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 1500 * (attempt + 1)));
        continue;
      }
      throw new Error(`网络请求失败 (${path}): ${msg}`);
    }
    if (!res.ok) {
      let errMsg = `HTTP ${res.status}`;
      try {
        const body = await res.json();
        errMsg = body.detail || body.message || errMsg;
      } catch {
        try { errMsg = await res.text(); } catch {}
      }
      throw new Error(errMsg);
    }
    return await res.json();
  }
  throw new Error(`请求失败 (${path}): 超过最大重试次数`);
}

export async function checkHealth(): Promise<boolean> {
  try {
    await request("/api/health", { method: "POST" });
    return true;
  } catch {
    return false;
  }
}

export async function startEngine(): Promise<number> {
  const port = await invoke<number>("start_engine");
  const settings = useSettingsStore();
  settings.setEnginePort(port);
  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 500));
    if (await checkHealth()) {
      settings.setEngineReady(true);
      return port;
    }
  }
  throw new Error("Engine failed to start within 15 seconds");
}

export async function getAudioInfo(audioPath: string) {
  return request("/api/audio/info", {
    method: "POST",
    body: JSON.stringify({ audio_path: audioPath }),
  });
}

export async function alignAudio(
  audioPath: string,
  scriptText: string,
  maxCharsPerLine: number = 14
): Promise<SubtitleEntry[]> {
  const data = await request("/api/align", {
    method: "POST",
    body: JSON.stringify({
      audio_path: audioPath,
      script_text: scriptText,
      max_chars_per_line: maxCharsPerLine,
    }),
  });
  return data.subtitles;
}

export async function exportSrt(
  subtitles: SubtitleEntry[],
  outputPath: string
): Promise<string> {
  const data = await request("/api/export/srt", {
    method: "POST",
    body: JSON.stringify({ subtitles, output_path: outputPath }),
  });
  return data.file_path;
}

export async function getModelStatus() {
  return request("/api/model/status", { method: "POST" });
}

export async function downloadModel() {
  return request("/api/model/download", { method: "POST" });
}

export async function openFileDialog(): Promise<string | null> {
  try {
    const selected = await open({
      multiple: false,
      filters: [{
        name: "Audio Files",
        extensions: ["mp3", "flac", "wav", "m4a", "ogg", "aac"],
      }],
    });
    if (!selected) return null;
    return typeof selected === "string" ? selected : null;
  } catch {
    return null;
  }
}

export async function saveFileDialog(defaultName: string, filterType?: string): Promise<string | null> {
  try {
    const extensions = filterType === "audio"
      ? ["mp3", "flac", "wav"]
      : ["srt"];
    const selected = await save({
      defaultPath: defaultName,
      filters: [{
        name: filterType === "audio" ? "Audio Files" : "SRT Files",
        extensions,
      }],
    });
    return selected ?? null;
  } catch {
    return null;
  }
}

// --- Drag & Drop ---
let dropListenerSetup = false;

export async function setupFileDropListener(onDrop: (path: string) => void) {
  if (dropListenerSetup) return;
  dropListenerSetup = true;

  await listen<{ paths: string[] }>("tauri://drag-drop", (event) => {
    const paths = event.payload.paths;
    if (paths && paths.length > 0) {
      const filePath = paths[0];
      const ext = filePath.split(".").pop()?.toLowerCase();
      if (["mp3", "flac", "wav", "m4a", "ogg", "aac"].includes(ext || "")) {
        onDrop(filePath);
      }
    }
  });
}
