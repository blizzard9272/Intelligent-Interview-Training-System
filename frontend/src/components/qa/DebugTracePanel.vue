<template>
  <div class="debug-panel">
    <div class="debug-group">
      <h4>路由结果</h4>
      <p class="debug-line">问题意图：{{ formatIntent(trace.route_intent) }}</p>
      <p class="debug-line">是否开启重排：{{ trace.rerank_enabled ? "是" : "否" }}</p>
    </div>

    <div class="debug-group">
      <h4>检索计划</h4>
      <div v-if="trace.query_plan.length === 0" class="debug-empty">没有检索计划。</div>
      <ol v-else class="debug-list">
        <li v-for="(item, index) in trace.query_plan" :key="index">
          <code>{{ formatFilterObject(item) }}</code>
        </li>
      </ol>
    </div>

    <div class="debug-group">
      <h4>检索结果</h4>
      <div v-if="trace.retrieval_steps.length === 0" class="debug-empty">没有检索结果。</div>
      <div v-else class="debug-step-list">
        <article
          v-for="(step, index) in trace.retrieval_steps"
          :key="index"
          class="debug-step"
        >
          <div class="debug-step-head">
            <strong>步骤 {{ index + 1 }}</strong>
            <span class="pill">返回 {{ step.returned_count }} 条</span>
          </div>
          <p class="debug-line">过滤条件：<code>{{ formatFilterObject(step.filters) }}</code></p>
          <ul class="debug-candidate-list">
            <li
              v-for="(candidate, candidateIndex) in step.candidates"
              :key="`${candidate.file_name}-${candidate.chunk_index}-${candidateIndex}`"
            >
              {{ candidate.file_name }} / 分块 {{ candidate.chunk_index }}
              <span v-if="candidate.section_title"> / {{ candidate.section_title }}</span>
              <span v-if="candidate.content_type_hint"> / {{ formatContentType(candidate.content_type_hint) }}</span>
              <span v-if="candidate.distance !== null && candidate.distance !== undefined">
                / 距离 {{ formatNumber(candidate.distance) }}
              </span>
            </li>
          </ul>
        </article>
      </div>
    </div>

    <div class="debug-group">
      <h4>重排结果</h4>
      <div v-if="trace.reranked_results.length === 0" class="debug-empty">没有重排结果。</div>
      <ol v-else class="debug-list">
        <li
          v-for="(candidate, index) in trace.reranked_results"
          :key="`${candidate.file_name}-${candidate.chunk_index}-${index}`"
        >
          {{ candidate.file_name }} / 分块 {{ candidate.chunk_index }}
          <span v-if="candidate.context_role"> / {{ formatContextRole(candidate.context_role) }}</span>
          <span v-if="candidate.rerank_score !== null && candidate.rerank_score !== undefined">
            / 分数 {{ formatNumber(candidate.rerank_score) }}
          </span>
        </li>
      </ol>
    </div>

    <div class="debug-group">
      <h4>上下文组织</h4>
      <div v-if="trace.context_blocks.length === 0" class="debug-empty">没有上下文分组。</div>
      <ul v-else class="debug-list">
        <li v-for="(block, index) in trace.context_blocks" :key="`${block.role}-${index}`">
          {{ block.title }}：{{ block.references.length }} 条
        </li>
      </ul>
      <pre class="structured-context">{{ trace.structured_context }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { QADebugTrace } from "../../api/qa";

defineProps<{
  trace: QADebugTrace;
}>();

const intentLabelMap: Record<string, string> = {
  concept: "概念题",
  interview: "面试题",
  design: "设计题",
  implementation: "实现题",
  general: "通用问题",
};

const contentTypeLabelMap: Record<string, string> = {
  concept_explanation: "概念讲解",
  question_answer: "问答片段",
  design_discussion: "设计讨论",
  implementation_detail: "实现细节",
  example_driven: "示例场景",
  general: "通用内容",
};

const documentKindLabelMap: Record<string, string> = {
  concept_guide: "概念文档",
  interview_qa: "面试问答",
  design_notes: "设计笔记",
  project_review: "项目复盘",
  general: "通用文档",
};

const contextRoleLabelMap: Record<string, string> = {
  core_answer: "核心回答",
  concept: "概念与原理",
  design: "设计与权衡",
  implementation: "实现细节",
  example: "示例与场景",
  qa_pair: "问答材料",
  general: "补充上下文",
};

function formatIntent(value: string) {
  return intentLabelMap[value] ?? value;
}

function formatContentType(value?: string | null) {
  if (!value) {
    return "";
  }
  return contentTypeLabelMap[value] ?? value;
}

function formatDocumentKind(value?: string | null) {
  if (!value) {
    return "";
  }
  return documentKindLabelMap[value] ?? value;
}

function formatContextRole(value?: string | null) {
  if (!value) {
    return "";
  }
  return contextRoleLabelMap[value] ?? value;
}

function formatFilterObject(value: Record<string, unknown>) {
  const entries = Object.entries(value);
  if (entries.length === 0) {
    return "通用召回";
  }
  return entries
    .map(([key, rawValue]) => `${formatFilterKey(key)}=${formatFilterValue(key, rawValue)}`)
    .join("，");
}

function formatFilterKey(key: string) {
  const keyMap: Record<string, string> = {
    content_type_hint: "内容类型",
    document_kind: "文档类型",
    starts_with_question: "是否问句开头",
  };
  return keyMap[key] ?? key;
}

function formatFilterValue(key: string, rawValue: unknown) {
  if (key === "content_type_hint" && typeof rawValue === "string") {
    return formatContentType(rawValue);
  }
  if (key === "document_kind" && typeof rawValue === "string") {
    return formatDocumentKind(rawValue);
  }
  if (key === "starts_with_question" && typeof rawValue === "boolean") {
    return rawValue ? "是" : "否";
  }
  if (typeof rawValue === "string") {
    return rawValue;
  }
  return JSON.stringify(rawValue);
}

function formatNumber(value: number) {
  return value.toFixed(3);
}
</script>

<style scoped>
.debug-panel {
  display: grid;
  gap: 16px;
}

.debug-group {
  display: grid;
  gap: 10px;
}

.debug-group h4 {
  margin: 0;
}

.debug-line,
.debug-empty {
  margin: 0;
  color: var(--text-secondary);
}

.debug-list,
.debug-candidate-list {
  margin: 0;
  padding-left: 18px;
  display: grid;
  gap: 8px;
}

.debug-step-list {
  display: grid;
  gap: 12px;
}

.debug-step {
  padding: 12px;
  border-radius: 12px;
  background: rgba(243, 247, 251, 0.92);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.debug-step-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}

.structured-context {
  margin: 0;
  white-space: pre-wrap;
  font-family: "Consolas", "Courier New", monospace;
  font-size: 0.9rem;
  padding: 14px;
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.92);
  color: #f8fafc;
}
</style>
