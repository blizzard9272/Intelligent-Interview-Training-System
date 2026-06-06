<template>
  <AppShell>
    <div class="page-stack">
      <section class="panel history-overview">
        <div class="panel-title">
          <h2>问答历史</h2>
          <p>查看已经保存的会话，快速回看消息内容，并从历史会话继续进入问答助手。</p>
        </div>
        <div class="overview-metrics">
          <article class="metric-card">
            <span>会话总数</span>
            <strong>{{ sessions.length }}</strong>
          </article>
          <article class="metric-card">
            <span>当前选中</span>
            <strong>{{ activeSession?.title || (activeSession ? `会话 #${activeSession.id}` : "未选择") }}</strong>
          </article>
          <article class="metric-card">
            <span>消息条数</span>
            <strong>{{ activeSessionDetail?.messages.length ?? 0 }}</strong>
          </article>
        </div>
      </section>

      <div class="history-layout">
        <section class="panel history-list-panel">
          <div class="panel-header">
            <div class="panel-title">
              <h2>会话列表</h2>
              <p>按更新时间排序，点击后可查看完整会话详情。</p>
            </div>
            <el-button text @click="loadSessions">刷新</el-button>
          </div>

          <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>

          <div v-if="loadingSessions" class="empty-state">正在加载会话...</div>
          <div v-else-if="sessions.length === 0" class="empty-state">还没有历史会话，先去问答助手开始一次对话吧。</div>
          <div v-else class="session-list">
            <SessionListItem
              v-for="session in sessions"
              :key="session.id"
              :title="session.title || `会话 #${session.id}`"
              :badge="`知识库 #${session.knowledge_base_id}`"
              :time-label="`更新于 ${formatDate(session.updated_at)}`"
              :active="activeSessionId === session.id"
              @select="loadSessionDetail(session.id)"
            />
          </div>
        </section>

        <section class="panel history-detail-panel">
          <div class="panel-header">
            <div class="panel-title">
              <h2>会话详情</h2>
              <p v-if="activeSession">
                {{ activeSession.title || `会话 #${activeSession.id}` }} · 更新于 {{ formatDate(activeSession.updated_at) }}
              </p>
              <p v-else>选择左侧会话后，可在这里查看完整消息记录。</p>
            </div>
            <el-button
              v-if="activeSession"
              type="primary"
              @click="continueInQA(activeSession.id)"
            >
              继续到问答助手
            </el-button>
          </div>

          <div v-if="loadingDetail" class="empty-state">正在加载会话详情...</div>
          <div v-else-if="!activeSessionDetail" class="empty-state">请选择一个历史会话查看详情。</div>
          <div v-else-if="activeSessionDetail.messages.length === 0" class="empty-state">当前会话还没有消息内容。</div>
          <div v-else class="detail-list">
            <ChatMessageCard
              v-for="(item, index) in activeSessionDetail.messages"
              :key="index"
              :message="item"
            />
          </div>
        </section>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

import { getQASessionDetail, getQASessions, type QASessionDetail, type QASessionItem } from "../../api/qa";
import ChatMessageCard from "../../components/qa/ChatMessageCard.vue";
import SessionListItem from "../../components/qa/SessionListItem.vue";
import AppShell from "../../layout/AppShell.vue";

const router = useRouter();

const sessions = ref<QASessionItem[]>([]);
const activeSessionId = ref<number | undefined>();
const activeSessionDetail = ref<QASessionDetail | null>(null);
const loadingSessions = ref(false);
const loadingDetail = ref(false);
const errorMessage = ref("");

const activeSession = computed(() => {
  return sessions.value.find((item) => item.id === activeSessionId.value);
});

async function loadSessions() {
  loadingSessions.value = true;
  errorMessage.value = "";
  try {
    sessions.value = await getQASessions();
    if (!activeSessionId.value && sessions.value.length > 0) {
      await loadSessionDetail(sessions.value[0].id);
    }
  } catch {
    errorMessage.value = "加载历史会话失败。";
  } finally {
    loadingSessions.value = false;
  }
}

async function loadSessionDetail(sessionId: number) {
  loadingDetail.value = true;
  activeSessionId.value = sessionId;
  errorMessage.value = "";
  try {
    activeSessionDetail.value = await getQASessionDetail(sessionId);
  } catch {
    activeSessionDetail.value = null;
    errorMessage.value = "加载会话详情失败。";
  } finally {
    loadingDetail.value = false;
  }
}

function continueInQA(sessionId: number) {
  void router.push({
    path: "/qa",
    query: { sessionId: String(sessionId) },
  });
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN");
}

onMounted(async () => {
  await loadSessions();
});
</script>

<style scoped>
.history-overview {
  display: grid;
  gap: 20px;
}

.overview-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  padding: 18px 20px;
  border-radius: var(--radius-md);
  background: rgba(243, 247, 251, 0.82);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.metric-card span {
  display: block;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.metric-card strong {
  display: block;
  font-size: 1.2rem;
}

.history-layout {
  display: grid;
  grid-template-columns: minmax(280px, 360px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.history-list-panel {
  position: sticky;
  top: 24px;
}

.session-list,
.detail-list {
  display: grid;
  gap: 14px;
}

@media (max-width: 1080px) {
  .overview-metrics,
  .history-layout {
    grid-template-columns: 1fr;
  }

  .history-list-panel {
    position: static;
  }
}
</style>
