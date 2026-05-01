<script setup lang="ts">
import { NButton, NSpin } from "naive-ui";
import { useProjectStore } from "../stores/project";
import { useSettingsStore } from "../stores/settings";
import { startEngine, restartEngine, setupEngineListener, alignAudio } from "../composables/useApi";
import { useMessage } from "naive-ui";
import AudioUploader from "../components/AudioUploader.vue";
import ScriptEditor from "../components/ScriptEditor.vue";
import SubtitleList from "../components/SubtitleList.vue";
import ProgressOverlay from "../components/ProgressOverlay.vue";
import { onMounted, ref, computed } from "vue";

const project = useProjectStore();
const settings = useSettingsStore();
const message = useMessage();

const engineStarting = ref(false);
const engineFailed = ref(false);
const engineFailMsg = ref("");

const engineStatus = computed(() => {
  if (settings.engineReady) return "ready";
  if (engineStarting.value) return "starting";
  if (engineFailed.value) return "failed";
  return "idle";
});

onMounted(async () => {
  if (!settings.engineReady) {
    await doStartEngine();
  }

  // Listen for engine crash events
  setupEngineListener((msg) => {
    settings.setEngineReady(false);
    engineFailed.value = true;
    engineFailMsg.value = msg;
    message.error("AI 引擎意外退出，请点击重试", { duration: 10000 });
  });
});

async function doStartEngine() {
  engineStarting.value = true;
  engineFailed.value = false;
  engineFailMsg.value = "";

  try {
    await startEngine();
    message.success("AI 引擎已就绪");
  } catch (e: any) {
    engineFailed.value = true;
    engineFailMsg.value = e?.message || "未知错误";
    message.error(`AI 引擎启动失败`, { duration: 10000 });
  } finally {
    engineStarting.value = false;
  }
}

async function handleRetry() {
  await doStartEngine();
}

async function handleGenerate() {
  if (!project.canGenerate) return;
  if (!settings.engineReady) {
    message.error("AI 引擎未就绪，请等待引擎启动");
    return;
  }
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
        <!-- Engine Status Banner -->
        <div v-if="engineStatus === 'starting'" class="engine-banner engine-banner-starting">
          <NSpin size="small" />
          <span>AI 引擎启动中，请稍候（首次启动可能需要30-60秒）...</span>
        </div>
        <div v-if="engineStatus === 'failed'" class="engine-banner engine-banner-failed">
          <div class="engine-banner-content">
            <span class="engine-fail-icon">⚠️</span>
            <div class="engine-fail-text">
              <strong>AI 引擎启动失败</strong>
              <span v-if="engineFailMsg" class="engine-fail-detail">{{ engineFailMsg }}</span>
            </div>
          </div>
          <NButton size="small" type="primary" @click="handleRetry">重试</NButton>
        </div>

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
          :disabled="!project.canGenerate || !settings.engineReady"
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

/* Engine status banner */
.engine-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  border-radius: var(--radius);
  margin-bottom: 14px;
  font-size: 13px;
  flex-shrink: 0;
}

.engine-banner-starting {
  background: rgba(245, 166, 35, 0.1);
  border: 1px solid rgba(245, 166, 35, 0.3);
  color: var(--text-secondary);
}

.engine-banner-failed {
  background: rgba(208, 48, 80, 0.08);
  border: 1px solid rgba(208, 48, 80, 0.25);
  justify-content: space-between;
}

.engine-banner-content {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.engine-fail-icon {
  flex-shrink: 0;
  font-size: 16px;
}

.engine-fail-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.engine-fail-text strong {
  font-size: 13px;
  color: #d03050;
}

.engine-fail-detail {
  font-size: 11px;
  color: var(--text-muted);
  word-break: break-word;
  max-height: 60px;
  overflow-y: auto;
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
