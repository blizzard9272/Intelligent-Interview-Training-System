<template>
  <div class="reference-list">
    <div
      v-for="(reference, index) in references"
      :key="`${reference.document_id}-${reference.chunk_index}-${index}`"
      class="reference-item"
    >
      <div class="reference-head">
        <strong>{{ reference.file_name }}</strong>
        <span class="pill">分块 #{{ reference.chunk_index }}</span>
      </div>
      <p>{{ reference.snippet }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { QAReference } from "../../api/qa";

defineProps<{
  references: QAReference[];
}>();
</script>

<style scoped>
.reference-list {
  display: grid;
  gap: 10px;
  margin-top: 12px;
}

.reference-item {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.92);
}

.reference-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.reference-item p {
  margin: 8px 0 0;
  color: var(--text-secondary);
  white-space: pre-wrap;
}
</style>
