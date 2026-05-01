<script setup lang="ts">
import { NIcon } from "naive-ui";
import { CloudUploadOutline, TrashOutline, SwapHorizontalOutline, MusicalNotesOutline } from "@vicons/ionicons5";
import { useProjectStore } from "../stores/project";
import { openFileDialog, getAudioInfo, setupFileDropListener } from "../composables/useApi";
import { useMessage } from "naive-ui";
import { onMounted } from "vue";

const project = useProjectStore();
const message = useMessage();

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
}

function fileName(path: string): string {
  return path.split("/").pop() || path.split("\\").pop() || path;
}

async function loadAudioFile(path: string) {
  try {
    const info = await getAudioInfo(path);
    project.setAudio(info);
  } catch (e: any) {
    message.error(`无法读取音频: ${e.message}`);
  }
}

async function handleSelectFile() {
  const path = await openFileDialog();
  if (!path) return;
  await loadAudioFile(path);
}

onMounted(() => {
  setupFileDropListener(async (path: string) => {
    await loadAudioFile(path);
  });
});
</script>

<template>
  <div class="audio-uploader">
    <template v-if="!project.hasAudio">
      <div class="drop-zone" @click="handleSelectFile">
        <div class="drop-icon-wrap">
          <NIcon size="32" class="drop-icon"><CloudUploadOutline /></NIcon>
        </div>
        <span class="drop-title">拖拽音频到此处</span>
        <span class="drop-hint">或点击选择文件</span>
        <div class="drop-formats">
          <span class="format-tag">MP3</span>
          <span class="format-tag">WAV</span>
          <span class="format-tag">FLAC</span>
          <span class="format-tag">M4A</span>
        </div>
      </div>
    </template>
    <template v-else>
      <div class="audio-card">
        <div class="audio-meta">
          <div class="audio-icon-box">
            <NIcon size="20" :component="MusicalNotesOutline" />
          </div>
          <div class="audio-details">
            <span class="audio-name">{{ fileName(project.audioInfo!.path) }}</span>
            <div class="audio-stats">
              <span class="stat">{{ formatDuration(project.audioInfo!.duration) }}</span>
              <span class="stat-sep">·</span>
              <span class="stat">{{ formatSize(project.audioInfo!.size) }}</span>
              <span class="stat-sep">·</span>
              <span class="stat">{{ project.audioInfo!.sample_rate / 1000 }}kHz</span>
            </div>
          </div>
        </div>
        <div class="audio-actions">
          <button class="action-btn" @click="handleSelectFile" title="更换音频">
            <NIcon size="16" :component="SwapHorizontalOutline" />
          </button>
          <button class="action-btn action-btn-danger" @click="project.clearAudio()" title="移除音频">
            <NIcon size="16" :component="TrashOutline" />
          </button>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.audio-uploader {
  min-height: 100px;
}

.drop-zone {
  border: 2px dashed var(--accent-border);
  border-radius: var(--radius);
  min-height: 100px;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: var(--accent-bg);
}

.drop-zone:hover {
  border-color: var(--accent);
  background: rgba(245, 166, 35, 0.1);
  transform: translateY(-1px);
}

.drop-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 3px 10px rgba(232, 121, 43, 0.2);
}

.drop-icon { color: #fff; }

.drop-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.drop-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.drop-formats {
  display: flex;
  gap: 6px;
  margin-top: 4px;
}

.format-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--surface-hover);
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

/* Audio card */
.audio-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 100px;
  padding: 12px;
  border: 1px solid var(--accent-border);
  border-radius: var(--radius);
  background: var(--accent-bg);
  transition: background 0.15s;
}

.audio-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.audio-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

.audio-details {
  min-width: 0;
}

.audio-name {
  font-size: 13px;
  font-weight: 600;
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 220px;
  color: var(--text-primary);
}

.audio-stats {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 2px;
}

.stat {
  font-size: 11px;
  color: var(--text-muted);
}

.stat-sep {
  font-size: 10px;
  color: var(--text-muted);
  opacity: 0.4;
}

.audio-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: var(--surface);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}

.action-btn-danger:hover {
  background: rgba(208, 48, 80, 0.1);
  color: #d03050;
}
</style>
