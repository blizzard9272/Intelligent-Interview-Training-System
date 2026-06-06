<template>
  <AppShell>
    <div class="interview-workspace">
      <aside class="panel interview-sidebar">
        <div class="panel-header interview-sidebar-header">
          <div class="panel-title">
            <h2>面试控制台</h2>
            <p>选择知识库、题型和难度，发起一轮更聚焦的专项模拟面试。</p>
          </div>
          <el-button text @click="refreshAll">刷新</el-button>
        </div>

        <el-form label-position="top" class="interview-form">
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

          <el-form-item label="题目难度">
            <el-select
              v-model="selectedDifficulty"
              placeholder="默认随机难度"
              clearable
              class="full-width"
            >
              <el-option
                v-for="item in difficultyOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="题目类型">
            <el-select
              v-model="selectedQuestionType"
              placeholder="默认随机题型"
              clearable
              class="full-width"
            >
              <el-option
                v-for="item in questionTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-form>

        <div class="sidebar-actions">
          <el-button
            type="primary"
            class="full-width"
            :loading="startingInterview"
            @click="handleStartInterview"
          >
            开始专项面试
          </el-button>
          <p class="meta-text">
            系统会按当前知识库、难度和题型筛选题目；如果不选筛选项，就从该知识库题库里随机出题。
          </p>
        </div>

        <div class="session-section">
          <div class="panel-title">
            <h2>面试历史</h2>
            <p>这里展示已经持久化的会话记录，方便回看不同专项训练的表现。</p>
          </div>

          <div v-if="loadingSessions" class="empty-state">正在加载面试会话...</div>
          <div v-else-if="sessions.length === 0" class="empty-state">还没有面试记录，先开始一轮模拟面试吧。</div>
          <div v-else class="session-list">
            <SessionListItem
              v-for="session in sessions"
              :key="session.session_id"
              :title="session.question"
              :badge="session.overall_score !== null ? `得分 ${session.overall_score}/10` : `第 ${session.current_round} 轮`"
              :time-label="formatDate(session.updated_at)"
              :secondary-label="buildSessionSubtitle(session)"
              :active="activeSessionId === session.session_id"
              @select="loadSessionDetail(session.session_id)"
            />
          </div>
        </div>
      </aside>

      <section class="panel interview-main">
        <div class="panel-header interview-main-header">
          <div class="panel-title">
            <h2>面试进行中</h2>
            <p>这里展示当前题目、候选人回答、系统反馈，以及会话结束后自动生成的总结。</p>
          </div>
          <div class="interview-meta">
            <span class="pill">{{ activeSessionId ? "已创建会话" : "未开始会话" }}</span>
            <span class="pill">{{ activeSession ? `第 ${activeSession.current_round}/${activeSession.max_rounds} 轮` : "等待出题" }}</span>
          </div>
        </div>

        <div v-if="loadingDetail" class="empty-state interview-empty">正在加载会话详情...</div>
        <div v-else-if="!activeSession" class="empty-state interview-empty">
          先从左侧选择知识库和筛选条件，开始一轮新的专项面试，题目、反馈和总结都会显示在这里。
        </div>
        <div v-else class="interview-content">
          <section class="question-panel">
            <div class="section-label">当前题目</div>
            <h3>{{ activeSession.question }}</h3>
            <p class="meta-text">
              会话创建于 {{ formatDate(activeSession.started_at) }}，当前状态：{{ formatStatus(activeSession.status) }}
            </p>
            <div class="question-meta-row">
              <span class="pill">第 {{ activeSession.current_round }} 轮</span>
              <span class="pill">最多 {{ activeSession.max_rounds }} 轮</span>
              <span class="pill">{{ activeSession.can_continue ? "可继续追问" : "本轮可结束" }}</span>
              <span v-if="activeSession.difficulty" class="pill">难度：{{ formatDifficulty(activeSession.difficulty) }}</span>
            </div>
            <div v-if="activeSession.question_tags.length" class="tag-row">
              <span
                v-for="tag in visibleQuestionTags(activeSession.question_tags)"
                :key="tag"
                class="tag-chip"
              >
                {{ formatQuestionTag(tag) }}
              </span>
            </div>
            <div v-if="activeSession.reference_answer" class="reference-answer">
              <div class="reference-answer-head">
                <strong>参考答案</strong>
                <span class="pill">用于反馈评估</span>
              </div>
              <pre>{{ activeSession.reference_answer }}</pre>
            </div>
          </section>

          <section class="answer-panel">
            <div class="panel-title">
              <h2>候选人回答</h2>
              <p>输入本轮作答后提交，系统会返回评分、优点、改进建议，并在需要时自动生成追问。</p>
            </div>
            <el-input
              v-model="answerDraft"
              type="textarea"
              :rows="8"
              resize="none"
              :disabled="activeSession.status === 'completed'"
              placeholder="请在这里输入本轮面试回答..."
              @keydown.ctrl.enter.prevent="handleSubmitAnswer"
            />
            <div class="answer-actions">
              <span class="meta-text">按 `Ctrl + Enter` 可以直接提交本轮作答。</span>
              <el-button
                type="primary"
                :loading="submittingAnswer"
                :disabled="!activeSessionId || activeSession.status === 'completed'"
                @click="handleSubmitAnswer"
              >
                提交回答
              </el-button>
            </div>
          </section>

          <section v-if="activeSession.feedback" class="feedback-grid">
            <article class="list-card score-card">
              <span class="section-label">综合评分</span>
              <strong>{{ activeSession.overall_score }}/10</strong>
              <p>{{ activeSession.feedback }}</p>
            </article>

            <article class="list-card insight-card">
              <h3>亮点总结</h3>
              <ul class="insight-list">
                <li v-for="item in activeSession.strengths" :key="item">{{ item }}</li>
              </ul>
            </article>

            <article class="list-card insight-card">
              <h3>改进建议</h3>
              <ul class="insight-list">
                <li v-for="item in activeSession.improvements" :key="item">{{ item }}</li>
              </ul>
            </article>

            <article v-if="activeSession.suggested_followup" class="list-card followup-card">
              <h3>建议追问方向</h3>
              <p>{{ activeSession.suggested_followup }}</p>
            </article>

            <article v-if="activeSession.next_question" class="list-card followup-card emphasize">
              <h3>下一轮追问</h3>
              <p>{{ activeSession.next_question }}</p>
            </article>
          </section>

          <section v-if="activeSession.summary" class="summary-panel">
            <article class="list-card summary-card">
              <div class="summary-head">
                <div>
                  <span class="section-label">面试总结</span>
                  <h3>会话结束后自动生成</h3>
                </div>
                <span class="pill">{{ activeSession.summary_meta?.overall_score ?? activeSession.overall_score }}/10</span>
              </div>
              <p class="summary-text">{{ activeSession.summary }}</p>
              <div class="summary-grid">
                <div v-if="summaryHighlights.length" class="summary-block">
                  <h4>本次亮点</h4>
                  <ul class="insight-list">
                    <li v-for="item in summaryHighlights" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="summaryWeakPoints.length" class="summary-block">
                  <h4>薄弱点</h4>
                  <ul class="insight-list">
                    <li v-for="item in summaryWeakPoints" :key="item">{{ item }}</li>
                  </ul>
                </div>
                <div v-if="summaryNextActions.length" class="summary-block summary-block-wide">
                  <h4>下一步训练建议</h4>
                  <ul class="insight-list">
                    <li v-for="item in summaryNextActions" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </article>
          </section>

          <section class="turns-panel">
            <div class="panel-title">
              <h2>会话轨迹</h2>
              <p>查看题目、追问、作答、反馈与总结记录，便于后续做针对性复盘。</p>
            </div>
            <div class="turn-list">
              <article
                v-for="turn in activeSession.turns"
                :key="turn.id"
                class="list-card turn-card"
                :class="turn.role"
              >
                <div class="turn-head">
                  <strong>{{ formatTurnRole(turn.role) }}</strong>
                  <span class="pill">{{ formatDate(turn.created_at) }}</span>
                </div>
                <pre class="turn-content">{{ turn.content }}</pre>
              </article>
            </div>
          </section>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import {
  getInterviewSessionDetail,
  getInterviewSessions,
  startInterview,
  submitInterviewAnswer,
  type InterviewSessionDetail,
  type InterviewSessionListItem,
} from "../../api/interview";
import { getKnowledgeBases, type KnowledgeBaseItem } from "../../api/knowledgeBase";
import SessionListItem from "../../components/qa/SessionListItem.vue";
import AppShell from "../../layout/AppShell.vue";

const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const selectedDifficulty = ref<string>();
const selectedQuestionType = ref<string>();
const sessions = ref<InterviewSessionListItem[]>([]);
const activeSession = ref<InterviewSessionDetail | null>(null);
const activeSessionId = ref<string | undefined>();
const answerDraft = ref("");
const loadingSessions = ref(false);
const loadingDetail = ref(false);
const startingInterview = ref(false);
const submittingAnswer = ref(false);

const difficultyOptions = [
  { label: "简单", value: "easy" },
  { label: "中等", value: "medium" },
  { label: "困难", value: "hard" },
];

const questionTypeOptions = [
  { label: "概念题", value: "concept" },
  { label: "场景题", value: "scenario" },
  { label: "追问题", value: "followup" },
  { label: "设计题", value: "design" },
];

const summaryHighlights = computed(() => {
  const value = activeSession.value?.summary_meta?.highlights;
  return Array.isArray(value) ? value : [];
});

const summaryWeakPoints = computed(() => {
  const value = activeSession.value?.summary_meta?.weak_points;
  return Array.isArray(value) ? value : [];
});

const summaryNextActions = computed(() => {
  const value = activeSession.value?.summary_meta?.next_actions;
  return Array.isArray(value) ? value : [];
});

async function loadKnowledgeBases() {
  knowledgeBases.value = await getKnowledgeBases();
  if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length > 0) {
    selectedKnowledgeBaseId.value = knowledgeBases.value[0].id;
  }
}

async function loadSessions() {
  loadingSessions.value = true;
  try {
    sessions.value = await getInterviewSessions(selectedKnowledgeBaseId.value);
    if (!activeSessionId.value && sessions.value.length > 0) {
      await loadSessionDetail(sessions.value[0].session_id);
    }
  } finally {
    loadingSessions.value = false;
  }
}

async function loadSessionDetail(sessionId: string) {
  loadingDetail.value = true;
  activeSessionId.value = sessionId;
  try {
    activeSession.value = await getInterviewSessionDetail(sessionId);
    answerDraft.value = activeSession.value.status === "completed" ? activeSession.value.answer || "" : "";
  } finally {
    loadingDetail.value = false;
  }
}

async function handleStartInterview() {
  if (!selectedKnowledgeBaseId.value) {
    return;
  }
  startingInterview.value = true;
  try {
    const result = await startInterview({
      knowledge_base_id: selectedKnowledgeBaseId.value,
      difficulty: selectedDifficulty.value || undefined,
      question_type: selectedQuestionType.value || undefined,
    });
    activeSessionId.value = result.session_id;
    answerDraft.value = "";
    await Promise.all([loadSessions(), loadSessionDetail(result.session_id)]);
  } finally {
    startingInterview.value = false;
  }
}

async function handleSubmitAnswer() {
  if (!activeSessionId.value || !answerDraft.value.trim() || activeSession.value?.status === "completed") {
    return;
  }
  submittingAnswer.value = true;
  try {
    const result = await submitInterviewAnswer({
      session_id: activeSessionId.value,
      answer: answerDraft.value,
    });
    answerDraft.value = "";
    await Promise.all([loadSessions(), loadSessionDetail(result.session_id)]);
  } finally {
    submittingAnswer.value = false;
  }
}

async function refreshAll() {
  await Promise.all([loadKnowledgeBases(), loadSessions()]);
  if (activeSessionId.value) {
    await loadSessionDetail(activeSessionId.value);
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN");
}

function formatStatus(status: string) {
  if (status === "awaiting_answer") {
    return "等待首轮回答";
  }
  if (status === "awaiting_followup_answer") {
    return "等待追问回答";
  }
  if (status === "completed") {
    return "已完成";
  }
  return status;
}

function formatTurnRole(role: string) {
  if (role === "interviewer") {
    return "面试官题目";
  }
  if (role === "interviewer_followup") {
    return "面试官追问";
  }
  if (role === "candidate") {
    return "候选人回答";
  }
  if (role === "interviewer_feedback") {
    return "系统反馈";
  }
  if (role === "interview_summary") {
    return "面试总结";
  }
  return role;
}

function formatDifficulty(value: string) {
  if (value === "easy") {
    return "简单";
  }
  if (value === "medium") {
    return "中等";
  }
  if (value === "hard") {
    return "困难";
  }
  return value;
}

function formatQuestionTag(tag: string) {
  if (tag === "concept") {
    return "概念题";
  }
  if (tag === "scenario") {
    return "场景题";
  }
  if (tag === "followup") {
    return "追问题";
  }
  if (tag === "design") {
    return "设计题";
  }
  return tag;
}

function visibleQuestionTags(tags: string[]) {
  return tags.filter((tag) => ["concept", "scenario", "followup", "design"].includes(tag.toLowerCase()));
}

function buildSessionSubtitle(session: InterviewSessionListItem) {
  const parts = [`状态：${formatStatus(session.status)}`];
  if (session.difficulty) {
    parts.push(`难度：${formatDifficulty(session.difficulty)}`);
  }
  const primaryTag = visibleQuestionTags(session.question_tags)[0];
  if (primaryTag) {
    parts.push(`题型：${formatQuestionTag(primaryTag)}`);
  }
  return parts.join(" · ");
}

watch(selectedKnowledgeBaseId, async () => {
  activeSession.value = null;
  activeSessionId.value = undefined;
  answerDraft.value = "";
  await loadSessions();
});

onMounted(async () => {
  await loadKnowledgeBases();
  await loadSessions();
});
</script>

<style scoped>
.interview-workspace {
  display: grid;
  grid-template-columns: minmax(300px, 360px) minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

.interview-sidebar,
.interview-main {
  display: flex;
  flex-direction: column;
}

.interview-sidebar {
  gap: 18px;
  position: sticky;
  top: 24px;
  max-height: calc(100vh - 48px);
  overflow: hidden;
}

.interview-sidebar-header,
.interview-main-header {
  margin-bottom: 0;
}

.interview-form,
.sidebar-actions,
.session-section,
.interview-content,
.feedback-grid,
.turn-list,
.summary-grid {
  display: grid;
  gap: 16px;
}

.session-section {
  min-height: 0;
  flex: 1;
}

.session-list {
  display: grid;
  gap: 12px;
  overflow-y: auto;
  min-height: 0;
}

.interview-main {
  gap: 18px;
}

.interview-meta,
.question-meta-row,
.summary-head,
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.summary-head {
  justify-content: space-between;
}

.interview-empty {
  min-height: 420px;
  display: grid;
  place-items: center;
  text-align: center;
}

.interview-content {
  gap: 20px;
}

.question-panel,
.answer-panel,
.turns-panel,
.summary-panel {
  display: grid;
  gap: 14px;
}

.question-panel h3,
.summary-card h3,
.summary-card h4 {
  margin: 0;
}

.question-panel h3 {
  font-size: 1.3rem;
  line-height: 1.5;
}

.tag-chip {
  padding: 6px 12px;
  border-radius: 999px;
  background: rgba(31, 111, 235, 0.08);
  border: 1px solid rgba(31, 111, 235, 0.14);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.reference-answer {
  display: grid;
  gap: 12px;
  padding: 16px;
  border-radius: var(--radius-md);
  background: rgba(243, 247, 251, 0.84);
  border: 1px solid var(--border-soft);
}

.reference-answer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.reference-answer pre,
.turn-content {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  font-family: "Segoe UI", "PingFang SC", sans-serif;
}

.answer-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.feedback-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.score-card {
  grid-column: 1 / -1;
}

.score-card strong {
  display: block;
  margin-top: 10px;
  font-size: 2rem;
}

.score-card p,
.followup-card p,
.summary-text {
  margin: 0;
  line-height: 1.7;
  color: var(--text-secondary);
}

.insight-card h3,
.followup-card h3 {
  margin: 0;
}

.insight-list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.followup-card.emphasize,
.summary-card {
  background: rgba(225, 243, 255, 0.75);
  border-color: rgba(31, 111, 235, 0.16);
}

.summary-card {
  display: grid;
  gap: 18px;
}

.summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.summary-block {
  padding: 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(31, 111, 235, 0.12);
}

.summary-block-wide {
  grid-column: 1 / -1;
}

.turn-card.interviewer,
.turn-card.interviewer_followup {
  background: rgba(243, 247, 251, 0.86);
}

.turn-card.candidate {
  background: rgba(218, 235, 255, 0.58);
}

.turn-card.interviewer_feedback {
  background: rgba(244, 249, 240, 0.86);
}

.turn-card.interview_summary {
  background: rgba(255, 246, 220, 0.88);
}

.turn-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

@media (max-width: 1180px) {
  .interview-workspace {
    grid-template-columns: 1fr;
  }

  .interview-sidebar {
    position: static;
    max-height: none;
  }
}

@media (max-width: 840px) {
  .feedback-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .summary-block-wide {
    grid-column: auto;
  }

  .answer-actions,
  .reference-answer-head,
  .turn-head,
  .summary-head {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
