<script setup lang="ts">
import { ref } from "vue";
import { NIcon } from "naive-ui";
import { useProjectStore } from "../stores/project";
import { exportSrt, saveFileDialog } from "../composables/useApi";
import { useMessage } from "naive-ui";
import { DownloadOutline, CopyOutline } from "@vicons/ionicons5";
import { formatTimestamp, parseTimestamp } from "../utils/srt";

const project = useProjectStore();
const message = useMessage();

const editingId = ref<number | null>(null);
const editField = ref<"time" | "text" | null>(null);
const editStart = ref("");
const editEnd = ref("");
const editText = ref("");

function formatTimeShort(s: number): string {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  const ms = Math.round((s % 1) * 100);
  return `${m.toString().padStart(2, "0")}:${sec.toString().padStart(2, "0")}.${ms.toString().padStart(2, "0")}`;
}

function startEditTime(index: number, startTime: number, endTime: number) {
  editingId.value = index;
  editField.value = "time";
  editStart.value = formatTimeShort(startTime);
  editEnd.value = formatTimeShort(endTime);
}

function startEditText(index: number, text: string) {
  editingId.value = index;
  editField.value = "text";
  editText.value = text;
}

function confirmEdit(sub: { index: number; start_time: number; end_time: number; text: string }) {
  if (editingId.value === null) return;

  if (editField.value === "time") {
    const startParsed = parseTimestamp("00:" + editStart.value.replace(".", ","));
    const endParsed = parseTimestamp("00:" + editEnd.value.replace(".", ","));
    if (startParsed !== null) sub.start_time = startParsed;
    if (endParsed !== null) sub.end_time = endParsed;
  } else if (editField.value === "text") {
    const trimmed = editText.value.trim();
    if (trimmed) sub.text = trimmed;
  }
  editingId.value = null;
  editField.value = null;
}

function cancelEdit() {
  editingId.value = null;
}

async function handleExport() {
  const defaultName = (project.audioInfo?.path.split("/").pop() || "subtitle").replace(/\.\w+$/, "") + ".srt";
  const outputPath = await saveFileDialog(defaultName);
  if (!outputPath) return;
  try {
    await exportSrt(project.subtitles, outputPath);
    message.success("SRT 已导出");
  } catch (e: any) {
    message.error(`导出失败: ${e.message}`);
  }
}

function handleCopy() {
  const content = project.subtitles
    .map((s) => `${formatTimestamp(s.start_time)} --> ${formatTimestamp(s.end_time)}\n${s.text}`)
    .join("\n\n");
  navigator.clipboard.writeText(content).then(() => {
    message.success("已复制到剪贴板");
  }).catch(() => {
    message.error("复制失败");
  });
}
</script>

<template>
  <div class="subtitle-panel">
    <div class="subtitle-header">
      <span class="subtitle-title">字幕结果</span>
      <div class="subtitle-actions">
        <button class="action-btn" @click="handleCopy" title="复制 SRT">
          <NIcon size="15" :component="CopyOutline" />
          <span>复制</span>
        </button>
        <button class="action-btn action-btn-primary" @click="handleExport" title="导出 SRT">
          <NIcon size="15" :component="DownloadOutline" />
          <span>导出</span>
        </button>
      </div>
    </div>

    <div class="subtitle-count">
      共 {{ project.subtitles.length }} 条
    </div>

    <div class="subtitle-list">
      <div
        v-for="sub in project.subtitles"
        :key="sub.index"
        class="subtitle-row"
        :class="{ 'subtitle-row--editing': editingId === sub.index }"
      >
        <!-- Index -->
        <div class="cell-index">
          <span class="index-num">{{ sub.index }}</span>
        </div>

        <!-- Time -->
        <div
          class="cell-time"
          @click="startEditTime(sub.index, sub.start_time, sub.end_time)"
        >
          <template v-if="editingId === sub.index && editField === 'time'">
            <input
              class="time-input"
              v-model="editStart"
              @keydown.enter="confirmEdit(sub)"
              @keydown.escape="cancelEdit"
              @blur="confirmEdit(sub)"
              autofocus
            />
            <span class="time-arrow">→</span>
            <input
              class="time-input"
              v-model="editEnd"
              @keydown.enter="confirmEdit(sub)"
              @keydown.escape="cancelEdit"
              @blur="confirmEdit(sub)"
            />
          </template>
          <template v-else>
            <span class="time-start">{{ formatTimeShort(sub.start_time) }}</span>
            <span class="time-arrow">→</span>
            <span class="time-end">{{ formatTimeShort(sub.end_time) }}</span>
          </template>
        </div>

        <!-- Text -->
        <div
          class="cell-text"
          :class="{ 'cell-text--editing': editingId === sub.index && editField === 'text' }"
          @click="startEditText(sub.index, sub.text)"
        >
          <template v-if="editingId === sub.index && editField === 'text'">
            <input
              class="text-input"
              v-model="editText"
              @keydown.enter="confirmEdit(sub)"
              @keydown.escape="cancelEdit"
              @blur="confirmEdit(sub)"
              autofocus
            />
          </template>
          <template v-else>
            {{ sub.text }}
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.subtitle-panel {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.subtitle-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.subtitle-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--text-primary);
}

.subtitle-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text-secondary);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.action-btn:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}

.action-btn-primary {
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  color: #fff;
  border-color: transparent;
}

.action-btn-primary:hover {
  background: linear-gradient(135deg, var(--accent), #d06a1f);
  color: #fff;
  box-shadow: 0 2px 8px rgba(232, 121, 43, 0.3);
}

.subtitle-count {
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--text-muted);
}

/* ── Scrollable list ── */
.subtitle-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding-right: 4px;
}

/* ── Row: 3-cell layout ── */
.subtitle-row {
  display: flex;
  align-items: stretch;
  min-height: 36px;
  border-radius: var(--radius-sm);
  background: var(--surface);
  border: 1px solid var(--border);
  overflow: hidden;
  transition: all 0.15s;
}

.subtitle-row:hover {
  border-color: var(--accent-border);
  box-shadow: var(--shadow-sm);
}

.subtitle-row--editing {
  border-color: var(--accent);
  box-shadow: 0 0 0 2px rgba(232, 121, 43, 0.12);
}

/* ── Cell: Index ── */
.cell-index {
  width: 44px;
  min-width: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--accent-bg);
  border-right: 1px solid var(--border);
}

.index-num {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent);
  font-variant-numeric: tabular-nums;
}

/* ── Cell: Time ── */
.cell-time {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 10px;
  min-width: 170px;
  cursor: pointer;
  border-right: 1px solid var(--border);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.cell-time:hover {
  background: var(--surface-hover);
}

.time-start,
.time-end {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.3px;
}

.time-arrow {
  font-size: 11px;
  color: var(--text-muted);
  margin: 0 2px;
}

.time-input {
  width: 62px;
  padding: 2px 4px;
  border: 1px solid var(--accent);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-primary);
  font-size: 12px;
  font-family: inherit;
  font-variant-numeric: tabular-nums;
  outline: none;
  text-align: center;
}

/* ── Cell: Text ── */
.cell-text {
  flex: 1;
  min-width: 0;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
}

.cell-text:hover {
  background: var(--surface-hover);
}

.cell-text--editing {
  padding: 4px 6px;
}

.text-input {
  flex: 1;
  min-width: 0;
  padding: 4px 6px;
  border: 1px solid var(--accent);
  border-radius: 4px;
  background: var(--surface);
  color: var(--text-primary);
  font-size: 13px;
  font-family: inherit;
  line-height: 1.5;
  outline: none;
}
</style>
