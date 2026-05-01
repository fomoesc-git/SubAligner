<script setup lang="ts">
import { NProgress, NText, NIcon } from "naive-ui";
import { useProjectStore } from "../stores/project";
import { PulseOutline } from "@vicons/ionicons5";

const project = useProjectStore();

const stageLabels: Record<string, string> = {
  preprocess: "音频预处理中...",
  vad: "语音活动检测中...",
  align: "AI 强制对齐中...",
  generate: "生成字幕中...",
};
</script>

<template>
  <Transition name="overlay">
    <div v-if="project.isProcessing" class="progress-overlay">
      <div class="progress-card">
        <div class="progress-icon">
          <NIcon size="28"><PulseOutline /></NIcon>
        </div>
        <NText strong style="font-size: 14px; color: var(--text-primary)">
          {{ stageLabels[project.processStage] || "处理中..." }}
        </NText>
        <NProgress
          type="line"
          :percentage="project.processPercent"
          :show-indicator="true"
          :height="6"
          :border-radius="3"
          color="var(--accent)"
          rail-color="var(--border)"
          style="width: 240px"
        />
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.progress-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.progress-card {
  background: var(--surface);
  border-radius: var(--radius-lg);
  padding: 28px 40px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
  box-shadow: var(--shadow-md);
  min-width: 280px;
}

.progress-icon {
  color: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.1); }
}

.overlay-enter-active,
.overlay-leave-active {
  transition: opacity 0.25s ease;
}

.overlay-enter-from,
.overlay-leave-to {
  opacity: 0;
}
</style>
