<template>
  <article class="message-card" :class="roleClass">
    <div class="message-role">{{ roleLabel }}</div>
    <pre class="message-content">{{ message.content }}</pre>

    <div
      v-if="showReferences"
      class="references"
    >
      <div class="references-toggle-row">
        <h4>引用片段</h4>
        <el-button v-if="collapsible" text @click="$emit('toggle-references')">
          {{ referencesExpanded ? "收起" : "展开" }}
        </el-button>
      </div>
      <ReferenceList
        v-if="!collapsible || referencesExpanded"
        :references="message.references_json ?? []"
      />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { QAMessage } from "../../api/qa";
import ReferenceList from "./ReferenceList.vue";

const props = withDefaults(
  defineProps<{
    message: QAMessage;
    collapsible?: boolean;
    referencesExpanded?: boolean;
  }>(),
  {
    collapsible: false,
    referencesExpanded: false,
  }
);

defineEmits<{
  (event: "toggle-references"): void;
}>();

const roleClass = computed(() => (props.message.role === "assistant" ? "assistant" : "user"));
const roleLabel = computed(() => (props.message.role === "assistant" ? "助手" : "你"));
const showReferences = computed(
  () => props.message.role === "assistant" && Boolean(props.message.references_json?.length)
);
</script>

<style scoped>
.message-card {
  padding: 18px;
  border-radius: 16px;
  border: 1px solid rgba(20, 33, 61, 0.06);
}

.message-card.user {
  background: rgba(218, 235, 255, 0.58);
}

.message-card.assistant {
  background: rgba(248, 250, 252, 0.9);
}

.message-role {
  font-weight: 700;
  margin-bottom: 10px;
}

.message-content {
  margin: 0;
  white-space: pre-wrap;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
  line-height: 1.6;
}

.references {
  margin-top: 16px;
  padding-top: 12px;
  border-top: 1px solid rgba(20, 33, 61, 0.08);
}

.references-toggle-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.references-toggle-row h4 {
  margin: 0;
}
</style>
