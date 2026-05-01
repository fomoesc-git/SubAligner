<script setup lang="ts">
import { useProjectStore } from "../stores/project";

const project = useProjectStore();
</script>

<template>
  <div class="script-editor">
    <textarea
      v-model="project.scriptText"
      class="script-textarea"
      placeholder="在此粘贴配音文案，每行一句..."
      spellcheck="false"
    />
    <div v-if="project.scriptCharCount > 0" class="editor-footer">
      <span class="char-count">{{ project.scriptCharCount }} 字</span>
      <button class="clear-btn" @click="project.scriptText = ''">清空</button>
    </div>
  </div>
</template>

<style scoped>
.script-editor {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  transition: border-color 0.15s;
  background: var(--surface);
  flex: 1;
  min-height: 0;
}

.script-editor:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(245, 166, 35, 0.1);
}

.script-textarea {
  width: 100%;
  flex: 1;
  min-height: 100px;
  padding: 14px;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  background: transparent;
  font-family: inherit;
}

.script-textarea::placeholder {
  color: var(--text-muted);
  font-size: 13px;
}

.editor-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-top: 1px solid var(--border);
  background: var(--surface-secondary);
}

.char-count {
  font-size: 11px;
  color: var(--text-muted);
}

.clear-btn {
  font-size: 11px;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.15s;
}

.clear-btn:hover {
  color: #d03050;
  background: rgba(208, 48, 80, 0.08);
}
</style>
