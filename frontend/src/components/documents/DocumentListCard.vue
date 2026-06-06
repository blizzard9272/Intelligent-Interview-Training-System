<template>
  <article class="list-card document-card">
    <div class="item-top">
      <div class="document-main">
        <div class="document-info">
          <h3>{{ item.file_name }}</h3>
          <p>{{ item.file_type.toUpperCase() }} / {{ sizeLabel }}</p>
          <p>状态：{{ item.status }}</p>
        </div>

        <div class="document-meta">
          <span class="pill">共 {{ item.chunk_count }} 段</span>
          <span class="pill">{{ updatedAtLabel }}</span>
        </div>
      </div>

      <div class="document-actions">
        <el-button @click="$emit('preview')">查看分块</el-button>
        <el-button type="danger" text @click="$emit('delete')">删除</el-button>
      </div>
    </div>

    <p v-if="item.parse_error" class="parse-error">解析提示：{{ item.parse_error }}</p>
  </article>
</template>

<script setup lang="ts">
import type { DocumentItem } from "../../api/document";

defineProps<{
  item: DocumentItem;
  sizeLabel: string;
  updatedAtLabel: string;
}>();

defineEmits<{
  (event: "preview"): void;
  (event: "delete"): void;
}>();
</script>

<style scoped>
.item-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.document-card {
  padding: 14px 16px;
}

.document-main {
  display: flex;
  flex: 1;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  min-width: 0;
}

.document-info {
  min-width: 0;
}

.document-meta,
.document-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.document-actions {
  margin-left: 12px;
}

.parse-error {
  margin-top: 10px;
  color: #c2410c;
}

.list-card h3 {
  margin: 0 0 6px;
}

.list-card p {
  margin: 4px 0;
  color: var(--text-secondary);
  line-height: 1.5;
}

@media (max-width: 960px) {
  .item-top,
  .document-main {
    flex-direction: column;
  }

  .document-actions {
    width: 100%;
    margin-left: 0;
  }
}
</style>
