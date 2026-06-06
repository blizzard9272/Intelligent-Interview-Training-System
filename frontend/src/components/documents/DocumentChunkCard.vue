<template>
  <article class="chunk-card">
    <div class="chunk-head">
      <strong>Chunk #{{ chunk.chunk_index + 1 }}</strong>
      <div class="chunk-head-meta">
        <span v-if="chunk.section_title" class="pill">{{ chunk.section_title }}</span>
        <span v-if="chunk.page_no" class="pill">页码 {{ chunk.page_no }}</span>
      </div>
    </div>
    <pre class="chunk-content">{{ chunk.content }}</pre>
  </article>
</template>

<script setup lang="ts">
import type { DocumentChunkItem } from "../../api/document";

defineProps<{
  chunk: DocumentChunkItem;
}>();
</script>

<style scoped>
.chunk-card {
  padding: 16px;
  border-radius: 16px;
  background: rgba(243, 247, 251, 0.85);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.chunk-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.chunk-head-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chunk-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  line-height: 1.7;
  color: var(--text-main);
}
</style>
