import { defineStore } from "pinia";
import { ref, watch } from "vue";

function getTimeBasedDark(): boolean {
  const h = new Date().getHours();
  return h < 6 || h >= 20;
}

export const useSettingsStore = defineStore("settings", () => {
  const isDark = ref(getTimeBasedDark());
  const maxCharsPerLine = ref(14);
  const enginePort = ref<number | null>(null);
  const engineReady = ref(false);
  const userManualChoice = ref(false);

  function toggleDark() {
    isDark.value = !isDark.value;
    userManualChoice.value = true;
  }

  function setEnginePort(port: number | null) {
    enginePort.value = port;
  }

  function setEngineReady(ready: boolean) {
    engineReady.value = ready;
    if (!ready) {
      enginePort.value = null;
    }
  }

  // Auto-switch dark mode based on time every 2 minutes
  // Only if user hasn't manually chosen a theme
  let timer: ReturnType<typeof setInterval> | null = null;

  function startAutoTheme() {
    if (timer) return;
    timer = setInterval(() => {
      if (userManualChoice.value) return;
      const target = getTimeBasedDark();
      if (isDark.value !== target) isDark.value = target;
    }, 120_000);
  }

  // Apply dark class to html element for CSS variables
  watch(isDark, (v) => {
    document.documentElement.classList.toggle("dark", v);
  }, { immediate: true });

  startAutoTheme();

  return {
    isDark,
    maxCharsPerLine,
    enginePort,
    engineReady,
    toggleDark,
    setEnginePort,
    setEngineReady,
  };
});
