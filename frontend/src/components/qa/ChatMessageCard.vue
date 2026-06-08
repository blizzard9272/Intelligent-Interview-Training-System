<template>
  <article class="message-card" :class="roleClass">
    <div class="message-role">{{ roleLabel }}</div>
    <MarkdownContent class="message-content" :content="message.content" />

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

    <div
      v-if="showDebugTrace"
      class="references debug-trace"
    >
      <div class="references-toggle-row">
        <h4>RAG 调试日志</h4>
        <el-button v-if="collapsible" text @click="$emit('toggle-debug')">
          {{ debugExpanded ? "收起" : "展开" }}
        </el-button>
      </div>
      <DebugTracePanel
        v-if="!collapsible || debugExpanded"
        :trace="message.debug_trace!"
      />
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { QAMessage } from "../../api/qa";
import DebugTracePanel from "./DebugTracePanel.vue";
import MarkdownContent from "./MarkdownContent.vue";
import ReferenceList from "./ReferenceList.vue";

const props = withDefaults(
  defineProps<{
    message: QAMessage;
    collapsible?: boolean;
    referencesExpanded?: boolean;
    debugExpanded?: boolean;
  }>(),
  {
    collapsible: false,
    referencesExpanded: false,
    debugExpanded: false,
  }
);

defineEmits<{
  (event: "toggle-references"): void;
  (event: "toggle-debug"): void;
}>();

const roleClass = computed(() => (props.message.role === "assistant" ? "assistant" : "user"));
const roleLabel = computed(() => (props.message.role === "assistant" ? "助手" : "你"));
const showReferences = computed(
  () => props.message.role === "assistant" && Boolean(props.message.references_json?.length)
);
const showDebugTrace = computed(
  () => props.message.role === "assistant" && Boolean(props.message.debug_trace)
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
