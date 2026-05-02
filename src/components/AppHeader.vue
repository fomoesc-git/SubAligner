<script setup lang="ts">
import { NIcon, NTooltip } from "naive-ui";
import { useSettingsStore } from "../stores/settings";
import { SunnyOutline, MoonOutline } from "@vicons/ionicons5";

const settings = useSettingsStore();
</script>

<template>
  <header class="app-header">
    <div class="header-brand">
      <div class="brand-icon">S</div>
      <span class="brand-name">SubAligner</span>
      <span class="brand-tag">配音字幕生成</span>
      <span class="brand-version">V1.0.5</span>
    </div>
    <div class="header-meta">
      <span class="meta-credit">本工具由@常宁千影设计</span>
    </div>
    <div class="header-actions">
      <NTooltip trigger="hover">
        <template #trigger>
          <button class="icon-btn" @click="settings.toggleDark()">
            <NIcon size="18" :component="settings.isDark ? SunnyOutline : MoonOutline" />
          </button>
        </template>
        {{ settings.isDark ? '浅色模式' : '深色模式' }}
      </NTooltip>
    </div>
  </header>
</template>

<style scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 48px;
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  -webkit-app-region: drag;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  -webkit-app-region: no-drag;
}

.brand-icon {
  width: 28px;
  height: 28px;
  border-radius: 7px;
  background: linear-gradient(135deg, var(--accent-light), var(--accent));
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 15px;
  letter-spacing: -0.5px;
  box-shadow: 0 2px 8px rgba(232, 121, 43, 0.3);
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.3px;
  color: var(--text-primary);
}

.brand-tag {
  font-size: 11px;
  opacity: 0.5;
  margin-left: -4px;
  color: var(--text-secondary);
}

.brand-version {
  font-size: 10px;
  font-weight: 500;
  color: var(--accent);
  background: var(--accent-bg);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: 4px;
  letter-spacing: 0.3px;
}

.header-meta {
  display: flex;
  align-items: center;
  -webkit-app-region: no-drag;
}

.meta-credit {
  font-size: 11px;
  color: var(--text-muted);
  opacity: 0.6;
  white-space: nowrap;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  -webkit-app-region: no-drag;
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.icon-btn:hover {
  background: var(--surface-hover);
  color: var(--text-primary);
}
</style>
