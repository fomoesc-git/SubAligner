<script setup lang="ts">
import { NButton } from "naive-ui";
import { useProjectStore } from "../stores/project";
import { useSettingsStore } from "../stores/settings";
import { alignAudio, startEngine } from "../composables/useApi";
import { useMessage } from "naive-ui";
import AudioUploader from "../components/AudioUploader.vue";
import ScriptEditor from "../components/ScriptEditor.vue";
import SubtitleList from "../components/SubtitleList.vue";
import ProgressOverlay from "../components/ProgressOverlay.vue";
import { onMounted } from "vue";

const project = useProjectStore();
const settings = useSettingsStore();
const message = useMessage();

onMounted(async () => {
  if (!settings.engineReady) {
    try {
      await startEngine();
      message.success("AI 引擎已就绪");
    } catch (e: any) {
      message.error(`AI 引擎启动失败: ${e.message}`);
    }
  }
});

async function handleGenerate() {
  if (!project.canGenerate) return;
  project.isProcessing = true;
  project.processStage = "vad";
  project.processPercent = 10;

  try {
    const subtitles = await alignAudio(
      project.audioInfo!.path,
      project.scriptText,
      settings.maxCharsPerLine
    );
    project.setSubtitles(subtitles);
    project.processPercent = 100;
    message.success(`生成完成，共 ${subtitles.length} 条字幕`);
  } catch (e: any) {
    const detail = e?.message || "未知错误";
    message.error(`生成失败: ${detail}`, { duration: 8000 });
  } finally {
    project.isProcessing = false;
  }
}
</script>

<template>
  <div class="main-layout">
    <!-- Left Panel: Input -->
    <div class="panel-left">
      <div class="panel-left-top">
        <div class="panel-section">
          <div class="section-label">
            <span class="label-dot" />
            <span class="label-text">音频文件</span>
          </div>
          <AudioUploader />
        </div>

        <div class="panel-section script-section">
          <div class="section-label">
            <span class="label-dot" />
            <span class="label-text">配音文案</span>
            <span v-if="project.scriptCharCount" class="label-count">
              {{ project.scriptCharCount }} 字
            </span>
          </div>
          <ScriptEditor />
        </div>
      </div>

      <div class="panel-bottom">
        <NButton
          type="primary"
          size="large"
          block
          :disabled="!project.canGenerate"
          :loading="project.isProcessing"
          @click="handleGenerate"
          class="generate-btn"
        >
          {{ project.isProcessing ? '生成中...' : '生成字幕' }}
        </NButton>
      </div>
    </div>

    <!-- Right Panel: Results -->
    <div class="panel-right">
      <template v-if="project.hasSubtitles">
        <SubtitleList />
      </template>
      <template v-else>
        <div class="empty-state">
          <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <span class="empty-title">字幕将在此处显示</span>
          <span class="empty-hint">导入音频 + 填写文案 → 点击生成</span>
        </div>
      </template>
    </div>
  </div>

  <ProgressOverlay />
</template>

<style scoped>
.main-layout {
  display: flex;
  height: 100%;
  overflow: hidden;
}

.panel-left {
  width: 400px;
  min-width: 340px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--surface);
  height: 100%;
}

.panel-left-top {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
}

.panel-right {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface-secondary);
  height: 100%;
  overflow: hidden;
  padding: 16px 20px;
}

.panel-section {
  flex-shrink: 0;
  margin-bottom: 14px;
}

.script-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.panel-bottom {
  padding: 12px 18px 16px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.section-label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  flex-shrink: 0;
}

.label-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
}

.label-text {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
}

.label-count {
  font-size: 11px;
  margin-left: auto;
  color: var(--text-muted);
}

.generate-btn {
  height: 44px;
  font-size: 15px;
  font-weight: 600;
  border-radius: var(--radius);
  background: linear-gradient(135deg, var(--accent-light), var(--accent)) !important;
  border: none !important;
  outline: none !important;
  color: var(--btn-text) !important;
  box-shadow: 0 2px 8px rgba(232, 121, 43, 0.25);
  transition: all 0.2s;
}

.generate-btn:hover:not(:disabled) {
  box-shadow: 0 4px 16px rgba(232, 121, 43, 0.35);
  transform: translateY(-1px);
  color: var(--btn-text) !important;
  border: none !important;
}

.generate-btn:focus:not(:disabled) {
  border: none !important;
  outline: none !important;
  box-shadow: 0 2px 8px rgba(232, 121, 43, 0.25);
}

.generate-btn:active:not(:disabled) {
  transform: translateY(0);
  color: var(--btn-text) !important;
  border: none !important;
}

.generate-btn:disabled {
  opacity: 0.5;
  color: var(--btn-text) !important;
  border: none !important;
  box-shadow: none;
}

/* Override Naive UI internal border */
.generate-btn :deep(.n-button__border),
.generate-btn :deep(.n-button__state-border) {
  display: none !important;
  border: none !important;
}

/* Empty state */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 8px;
  padding: 40px;
}

.empty-icon {
  color: var(--text-muted);
  opacity: 0.4;
  margin-bottom: 8px;
}

.empty-title {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-secondary);
}

.empty-hint {
  font-size: 13px;
  opacity: 0.7;
  color: var(--text-muted);
}

/* Responsive: stack on narrow */
@media (max-width: 800px) {
  .main-layout {
    flex-direction: column;
  }
  .panel-left {
    width: 100%;
    min-width: 0;
    border-right: none;
    border-bottom: 1px solid var(--border);
    max-height: 50vh;
  }
  .panel-right {
    flex: 1;
  }
}
</style>
