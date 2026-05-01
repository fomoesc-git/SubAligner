<script setup lang="ts">
import { NConfigProvider, NMessageProvider, darkTheme, zhCN, dateZhCN } from "naive-ui";
import { useSettingsStore } from "./stores/settings";
import AppHeader from "./components/AppHeader.vue";

const settings = useSettingsStore();
</script>

<template>
  <NConfigProvider :theme="settings.isDark ? darkTheme : undefined" :locale="zhCN" :dateLocale="dateZhCN">
    <NMessageProvider>
      <div class="app-shell">
        <AppHeader />
        <div class="app-body">
          <RouterView />
        </div>
      </div>
    </NMessageProvider>
  </NConfigProvider>
</template>

<style>
:root {
  --accent: #e8792b;
  --accent-light: #f5a623;
  --accent-bg: rgba(245, 166, 35, 0.06);
  --accent-border: rgba(245, 166, 35, 0.3);
  --surface: #ffffff;
  --surface-secondary: #f5f5f6;
  --surface-hover: #eeeef0;
  --border: rgba(0, 0, 0, 0.12);
  --text-primary: #1a1a1a;
  --text-secondary: #555;
  --text-muted: #888;
  --btn-text: #ffffff;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
  --radius: 10px;
  --radius-sm: 6px;
  --radius-lg: 14px;
}

html.dark {
  --surface: #1e1e20;
  --surface-secondary: #27272a;
  --surface-hover: #2e2e32;
  --border: rgba(255, 255, 255, 0.1);
  --text-primary: #e8e8e8;
  --text-secondary: #b0b0b0;
  --text-muted: #777;
  --btn-text: #ffffff;
  --accent-bg: rgba(245, 166, 35, 0.1);
  --accent-border: rgba(245, 166, 35, 0.3);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4);
}

* { margin: 0; padding: 0; box-sizing: border-box; }

html, body, #app {
  height: 100%;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
  color: var(--text-primary);
  background: var(--surface);
}

.app-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--surface);
}

.app-body {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
}

.app-body > * {
  flex: 1;
  min-height: 0;
}

/* Scrollbar styling */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: rgba(128, 128, 128, 0.25);
  border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(128, 128, 128, 0.4); }

/* Selection color */
::selection {
  background: rgba(245, 166, 35, 0.2);
}
</style>
