<template>
  <AppShell>
    <div class="qa-workspace">
      <aside class="panel qa-sidebar">
        <div class="panel-header qa-sidebar-header">
          <div class="panel-title">
            <h2>会话管理</h2>
            <p>在这里选择知识库、切换历史会话，左侧只负责会话管理。</p>
          </div>
          <el-button text @click="loadSessions">刷新</el-button>
        </div>

        <div class="session-section">
          <div class="panel-title">
            <h2>会话</h2>
            <p>选择一个历史会话继续追问，或从空白状态开始新的对话。</p>
          </div>

          <div v-if="loadingSessions" class="empty-state">正在加载会话...</div>
          <div v-else-if="sessions.length === 0" class="empty-state">暂时还没有会话。</div>
          <div v-else class="session-list">
            <button
              v-for="session in sessions"
              :key="session.id"
              type="button"
              class="session-item"
              :class="{ active: activeSessionId === session.id }"
              @click="loadSessionDetail(session.id)"
            >
              <strong>{{ session.title || `会话 #${session.id}` }}</strong>
              <span>{{ formatDate(session.updated_at) }}</span>
            </button>
          </div>
        </div>

        <el-form label-position="top" class="qa-form">
          <el-form-item label="知识库">
            <el-select
              v-model="selectedKnowledgeBaseId"
              placeholder="请选择知识库"
              class="full-width"
            >
              <el-option
                v-for="item in knowledgeBases"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="session-toolbar">
          <el-button type="primary" class="full-width" @click="startNewSession">新建会话</el-button>
          <p class="meta-text">切换会话后，右侧对话区会立即加载对应上下文。</p>
        </div>

        
      </aside>

      <section class="panel qa-conversation">
        <div class="panel-header qa-conversation-header">
          <div class="panel-title">
            <h2>AI 对话</h2>
            <p>主体区域专注于和 AI 对话，回答会在这里连续展开，并附带引用片段。</p>
          </div>
          <div class="conversation-meta">
            <span class="pill">{{ activeSessionId ? `会话 #${activeSessionId}` : "新会话" }}</span>
            <span class="pill">{{ selectedKnowledgeBaseId ? "已选择知识库" : "未选择知识库" }}</span>
          </div>
        </div>

        <div v-if="loadingDetail" class="empty-state conversation-empty">正在加载对话...</div>
        <div v-else-if="messages.length === 0" class="empty-state conversation-empty">
          先从左侧选择知识库与会话，然后在底部输入问题开始和 AI 对话。
        </div>
        <div v-else class="message-list">
          <article
            v-for="(item, index) in messages"
            :key="index"
            class="message"
            :class="item.role === 'assistant' ? 'assistant' : 'user'"
          >
            <div class="message-role">{{ item.role === "assistant" ? "助手" : "你" }}</div>
            <pre class="message-content">{{ item.content }}</pre>

            <div
              v-if="item.role === 'assistant' && item.references_json && item.references_json.length > 0"
              class="references"
            >
              <div class="references-toggle-row">
                <h4>引用片段</h4>
                <el-button text @click="toggleReferences(index)">
                  {{ isReferenceExpanded(index) ? "收起" : "展开" }}
                </el-button>
              </div>
              <div v-if="isReferenceExpanded(index)" class="reference-list">
                <div
                  v-for="(reference, refIndex) in item.references_json"
                  :key="refIndex"
                  class="reference-item"
                >
                  <div class="reference-head">
                    <strong>{{ reference.file_name }}</strong>
                    <span class="pill">分块 #{{ reference.chunk_index }}</span>
                  </div>
                  <p>{{ reference.snippet }}</p>
                </div>
              </div>
            </div>
          </article>
        </div>

        <footer class="composer">
          <div class="composer-head">
            <strong>继续提问</strong>
            <span class="meta-text">按 `Ctrl + Enter` 发送当前问题。</span>
          </div>
          <el-input
            v-model="question"
            type="textarea"
            :rows="4"
            resize="none"
            placeholder="围绕当前知识库输入一个基于资料的问题..."
            @keydown.ctrl.enter.prevent="handleAsk"
          />
          <div class="composer-actions">
            <div class="composer-status">
              <p v-if="message" class="status-message success">{{ message }}</p>
              <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>
            </div>
            <div class="actions">
              <el-button type="primary" :loading="asking" @click="handleAsk">发送问题</el-button>
              <el-button @click="startNewSession">清空当前会话</el-button>
            </div>
          </div>
        </footer>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";

import { askQuestion, getQASessionDetail, getQASessions, type QAMessage, type QASessionItem } from "../../api/qa";
import { getKnowledgeBases, type KnowledgeBaseItem } from "../../api/knowledgeBase";
import AppShell from "../../layout/AppShell.vue";

const route = useRoute();

const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const question = ref("");
const asking = ref(false);
const loadingSessions = ref(false);
const loadingDetail = ref(false);
const sessions = ref<QASessionItem[]>([]);
const messages = ref<QAMessage[]>([]);
const activeSessionId = ref<number | undefined>();
const message = ref("");
const errorMessage = ref("");
const expandedReferenceMap = ref<Record<number, boolean>>({});

function isReferenceExpanded(index: number) {
  return Boolean(expandedReferenceMap.value[index]);
}

function toggleReferences(index: number) {
  expandedReferenceMap.value = {
    ...expandedReferenceMap.value,
    [index]: !expandedReferenceMap.value[index],
  };
}

async function loadKnowledgeBases() {
  knowledgeBases.value = await getKnowledgeBases();
  if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length > 0) {
    selectedKnowledgeBaseId.value = knowledgeBases.value[0].id;
  }
}

async function loadSessions() {
  loadingSessions.value = true;
  errorMessage.value = "";
  try {
    sessions.value = await getQASessions();
    const querySessionId = Number(route.query.sessionId);
    if (Number.isInteger(querySessionId) && querySessionId > 0) {
      await loadSessionDetail(querySessionId);
    }
  } catch {
    errorMessage.value = "加载会话失败。";
  } finally {
    loadingSessions.value = false;
  }
}

async function loadSessionDetail(sessionId: number) {
  loadingDetail.value = true;
  activeSessionId.value = sessionId;
  errorMessage.value = "";
  expandedReferenceMap.value = {};
  try {
    const detail = await getQASessionDetail(sessionId);
    messages.value = detail.messages;
  } catch {
    errorMessage.value = "加载会话详情失败。";
  } finally {
    loadingDetail.value = false;
  }
}

function startNewSession() {
  activeSessionId.value = undefined;
  messages.value = [];
  message.value = "已开始新的会话。";
  errorMessage.value = "";
  expandedReferenceMap.value = {};
}

async function handleAsk() {
  if (!selectedKnowledgeBaseId.value) {
    errorMessage.value = "请先选择知识库。";
    return;
  }
  if (!question.value.trim()) {
    errorMessage.value = "请先输入问题。";
    return;
  }

  asking.value = true;
  errorMessage.value = "";
  message.value = "";
  try {
    const result = await askQuestion({
      knowledge_base_id: selectedKnowledgeBaseId.value,
      question: question.value,
      session_id: activeSessionId.value,
    });
    activeSessionId.value = result.session_id;
    question.value = "";
    message.value = "回答已生成。";
    await Promise.all([loadSessions(), loadSessionDetail(result.session_id)]);
  } catch (error: any) {
    if (error?.code === "ECONNABORTED") {
      errorMessage.value = "问答请求超时，模型响应时间过长。";
    } else if (error?.response?.data?.detail) {
      errorMessage.value = String(error.response.data.detail);
    } else {
      errorMessage.value = "问答失败，请稍后重试。";
    }
  } finally {
    asking.value = false;
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

onMounted(async () => {
  try {
    await loadKnowledgeBases();
    await loadSessions();
  } catch {
    errorMessage.value = "初始化问答页面失败。";
  }
});

watch(
  () => route.query.sessionId,
  async (value) => {
    const sessionId = Number(value);
    if (Number.isInteger(sessionId) && sessionId > 0 && sessionId !== activeSessionId.value) {
      await loadSessionDetail(sessionId);
    }
  }
);
</script>

<style scoped>
.qa-workspace {
  display: grid;
  grid-template-columns: minmax(280px, 340px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.qa-sidebar,
.qa-conversation {
  display: flex;
  flex-direction: column;
}

.qa-sidebar {
  gap: 18px;
  align-self: start;
  position: sticky;
  top: 24px;
  max-height: 100vh;
  overflow: hidden;
}

.qa-sidebar-header,
.qa-conversation-header {
  margin-bottom: 0;
}

.qa-form {
  display: grid;
  gap: 4px;
}

.session-toolbar {
  display: grid;
  gap: 12px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.session-section {
  display: grid;
  gap: 14px;
  min-height: 0;
  flex: 1;
}

.session-list {
  display: grid;
  gap: 12px;
  align-content: start;
  overflow-y: auto;
  min-height: 0;
}

.session-item {
  border: 1px solid rgba(20, 33, 61, 0.06);
  text-align: left;
  background: rgba(243, 247, 251, 0.86);
  border-radius: 16px;
  padding: 14px 16px;
  cursor: pointer;
  display: grid;
  gap: 6px;
  transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
}

.session-item:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 111, 235, 0.2);
  box-shadow: var(--shadow-sm);
}

.session-item.active {
  background: rgba(31, 111, 235, 0.12);
  border-color: rgba(31, 111, 235, 0.22);
}

.qa-conversation {
  gap: 18px;
  position: sticky;
  top: 24px;
  height: 150vh;
  overflow: hidden;
}

.conversation-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.conversation-empty {
  flex: 1;
  display: grid;
  place-items: center;
  text-align: center;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  min-height: 0;
  flex: 1;
  overflow-y: auto;
  padding-right: 6px;
  padding-bottom: 8px;
  align-items: stretch;
}

.message {
  padding: 18px;
  border-radius: 16px;
  border: 1px solid rgba(20, 33, 61, 0.06);
  flex: 0 0 auto;
  align-self: stretch;
}

.message.user {
  background: rgba(218, 235, 255, 0.58);
}

.message.assistant {
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
}

.composer {
  display: grid;
  gap: 14px;
  margin-top: auto;
  padding: 18px;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-md);
  background: rgba(243, 247, 251, 0.96);
  box-shadow: 0 -10px 24px rgba(31, 50, 81, 0.05);
  position: sticky;
  bottom: 0;
}

.composer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.composer-actions {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.composer-status {
  display: grid;
  gap: 8px;
}

.composer-status .status-message {
  margin: 0;
}

@media (max-width: 1080px) {
  .qa-workspace {
    grid-template-columns: 1fr;
  }

  .qa-sidebar,
  .qa-conversation {
    position: static;
    max-height: none;
    height: auto;
  }

  .message-list {
    max-height: none;
  }

  .composer {
    position: static;
  }

  .composer-head,
  .composer-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
