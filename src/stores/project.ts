import { defineStore } from "pinia";
import { ref, computed } from "vue";

export interface SubtitleWord {
  text: string;
  start: number;
  end: number;
}

export interface SubtitleEntry {
  index: number;
  start_time: number;
  end_time: number;
  text: string;
  words?: SubtitleWord[];
}

export interface AudioInfo {
  path: string;
  duration: number;
  format: string;
  size: number;
  sample_rate: number;
}

export const useProjectStore = defineStore("project", () => {
  const audioInfo = ref<AudioInfo | null>(null);
  const scriptText = ref("");
  const subtitles = ref<SubtitleEntry[]>([]);
  const isProcessing = ref(false);
  const processStage = ref("");
  const processPercent = ref(0);

  const scriptCharCount = computed(() => scriptText.value.replace(/\s/g, "").length);
  const hasAudio = computed(() => audioInfo.value !== null);
  const hasScript = computed(() => scriptText.value.trim().length > 0);
  const hasSubtitles = computed(() => subtitles.value.length > 0);
  const canGenerate = computed(() => hasAudio.value && hasScript.value && !isProcessing.value);

  function setAudio(info: AudioInfo) {
    audioInfo.value = info;
  }

  function clearAudio() {
    audioInfo.value = null;
  }

  function setSubtitles(entries: SubtitleEntry[]) {
    subtitles.value = entries;
  }

  function reset() {
    audioInfo.value = null;
    scriptText.value = "";
    subtitles.value = [];
    isProcessing.value = false;
    processStage.value = "";
    processPercent.value = 0;
  }

  return {
    audioInfo, scriptText, subtitles,
    isProcessing, processStage, processPercent,
    scriptCharCount, hasAudio, hasScript, hasSubtitles, canGenerate,
    setAudio, clearAudio, setSubtitles, reset,
  };
});
