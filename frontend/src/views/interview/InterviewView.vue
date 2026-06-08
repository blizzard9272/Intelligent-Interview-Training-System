<template>
  <AppShell>
    <div class="interview-workspace">
      <aside class="panel interview-sidebar">
        <div class="panel-header interview-sidebar-header">
          <div class="panel-title">
            <h2>面试控制台</h2>
            <p>按知识库、来源文档、题型、难度和训练模式发起一场更聚焦的模拟面试。</p>
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

          <el-form-item label="训练模式">
            <el-select
              v-model="selectedDrillMode"
              placeholder="请选择训练模式"
              class="full-width"
            >
              <el-option
                v-for="item in drillModeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>

          <el-form-item v-if="selectedDrillMode === 'question_set'" label="题目数量">
            <el-input-number
              v-model="selectedQuestionCount"
              :min="2"
              :max="10"
              class="full-width number-input"
            />
          </el-form-item>

          <el-form-item label="来源文档">
            <el-select
              v-model="selectedSourceDocumentId"
              placeholder="默认使用所有已完成入库的文档"
              clearable
              class="full-width"
            >
              <el-option
                v-for="item in availableDocuments"
                :key="item.id"
                :label="item.file_name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>

          <el-form-item label="难度">
            <el-select
              v-model="selectedDifficulty"
              placeholder="不限难度"
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

          <el-form-item label="题型">
            <el-select
              v-model="selectedQuestionType"
              placeholder="不限题型"
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

          <el-form-item label="选题策略">
            <el-select
              v-model="selectedQuestionStrategy"
              placeholder="请选择题目选择方式"
              class="full-width"
            >
              <el-option
                v-for="item in questionStrategyOptions"
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
            开始面试
          </el-button>
          <p class="meta-text">
            `单题深挖` 适合围绕一个主题持续追问。`题组训练` 会在一次会话中按计划连续练习多道题。
          </p>
        </div>

        <div class="session-section">
          <div class="panel-title">
            <h2>面试历史</h2>
            <p>切换查看已保存的面试会话，并回顾每次训练时使用的配置。</p>
          </div>

          <div v-if="loadingSessions" class="empty-state">正在加载面试会话...</div>
          <div v-else-if="sessions.length === 0" class="empty-state">还没有面试会话，先从上面的控制区发起一次训练吧。</div>
          <div v-else class="session-list">
            <div
              v-for="session in sessions"
              :key="session.session_id"
              class="session-entry"
            >
              <SessionListItem
                :title="session.question"
                :badge="session.overall_score !== null ? `得分 ${session.overall_score}/10` : `轮次 ${session.current_round}`"
                :time-label="formatDate(session.updated_at)"
                :secondary-label="buildSessionSubtitle(session)"
                :active="activeSessionId === session.session_id"
                @select="loadSessionDetail(session.session_id)"
              />
              <div class="session-actions">
                <el-popconfirm
                  title="确认删除这条面试会话吗？删除后无法恢复。"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm="handleDeleteSession(session.session_id)"
                >
                  <template #reference>
                    <el-button
                      text
                      type="danger"
                      :loading="deletingSessionId === session.session_id"
                    >
                      删除这条会话
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <section class="panel interview-main">
        <div class="panel-header interview-main-header">
          <div class="panel-title">
            <h2>面试会话</h2>
            <p>查看当前题目、提交回答、检查反馈，并在完成后查看自动生成的会话总结。</p>
          </div>
          <div class="interview-meta">
            <span class="pill">{{ activeSessionId ? "会话进行中" : "等待开始" }}</span>
            <span class="pill">{{ activeSession ? `轮次 ${activeSession.current_round}/${activeSession.max_rounds}` : "尚未出题" }}</span>
            <span v-if="activeSession" class="pill">题目 {{ activeSession.active_question_number }}/{{ activeSession.question_count }}</span>
          </div>
        </div>

        <div v-if="loadingDetail" class="empty-state interview-empty">正在加载会话详情...</div>
        <div v-else-if="!activeSession" class="empty-state interview-empty">
          先在左侧选择知识库和可选筛选条件，然后开始一场新的模拟面试。
        </div>
        <div v-else class="interview-content">
          <section v-if="hasPresetFocus" class="list-card preset-banner">
            <span class="section-label">专项训练</span>
            <strong>{{ presetFocusLabel }}</strong>
            <p>这场会话来自训练分析页面，用于针对一个反复出现的薄弱点进行强化练习。</p>
          </section>

          <section class="question-panel">
            <div class="section-label">当前题目</div>
            <h3>{{ activeSession.question }}</h3>
            <p class="meta-text">
              开始时间：{{ formatDate(activeSession.started_at) }}。当前状态：{{ formatStatus(activeSession.status) }}。
            </p>
            <div class="question-meta-row">
              <span class="pill">{{ formatDrillMode(activeSession.drill_mode) }}</span>
              <span v-if="activeSession.focus_topic" class="pill">专项：{{ activeSession.focus_topic }}</span>
              <span class="pill">题目 {{ activeSession.active_question_number }} / {{ activeSession.question_count }}</span>
              <span class="pill">当前轮次 {{ activeSession.current_round }}</span>
              <span class="pill">最多 {{ activeSession.max_rounds }} 轮</span>
              <span class="pill">{{ activeSession.can_continue ? "仍可继续追问" : "本会话已完成" }}</span>
              <span v-if="activeSession.difficulty" class="pill">难度：{{ formatDifficulty(activeSession.difficulty) }}</span>
              <span v-if="activeSession.source_document_name" class="pill">文档：{{ activeSession.source_document_name }}</span>
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
                <span class="pill">用于评分参考</span>
              </div>
              <pre>{{ activeSession.reference_answer }}</pre>
            </div>
          </section>

          <section class="answer-panel">
            <div class="panel-title">
              <h2>候选人回答</h2>
              <p>提交你在当前轮次的回答。系统会给出评分、改进建议，并决定继续追问还是进入下一道计划题目。</p>
            </div>
            <el-input
              v-model="answerDraft"
              type="textarea"
              :rows="8"
              resize="none"
              :disabled="activeSession.status === 'completed'"
              placeholder="请输入你在当前轮次的回答..."
              @keydown.ctrl.enter.prevent="handleSubmitAnswer"
            />
            <div class="answer-actions">
              <span class="meta-text">按 `Ctrl + Enter` 可直接提交当前回答。</span>
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
              <span class="section-label">得分</span>
              <strong>{{ activeSession.overall_score }}/10</strong>
              <p>{{ activeSession.feedback }}</p>
            </article>

            <article class="list-card insight-card">
              <h3>亮点</h3>
              <ul class="insight-list">
                <li v-for="item in activeSession.strengths" :key="item">{{ item }}</li>
              </ul>
            </article>

            <article class="list-card insight-card">
              <h3>待改进点</h3>
              <ul class="insight-list">
                <li v-for="item in activeSession.improvements" :key="item">{{ item }}</li>
              </ul>
            </article>

            <article v-if="activeSession.suggested_followup" class="list-card followup-card">
              <h3>建议追问方向</h3>
              <p>{{ activeSession.suggested_followup }}</p>
            </article>

            <article v-if="activeSession.next_question" class="list-card followup-card emphasize">
              <h3>{{ activeSession.next_prompt_type === 'next_question' ? '下一道计划题目' : '下一轮追问题目' }}</h3>
              <p>{{ activeSession.next_question }}</p>
            </article>
          </section>

          <section v-if="activeSession.summary" class="summary-panel">
            <article class="list-card summary-card">
              <div class="summary-head">
                <div>
                  <span class="section-label">面试总结</span>
                  <h3>会话完成后自动生成</h3>
                </div>
                <span class="pill">{{ activeSession.summary_meta?.overall_score ?? activeSession.overall_score }}/10</span>
              </div>
              <p class="summary-text">{{ activeSession.summary }}</p>
              <div class="summary-grid">
                <div v-if="summaryHighlights.length" class="summary-block">
                  <h4>亮点总结</h4>
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
                  <h4>下一步建议</h4>
                  <ul class="insight-list">
                    <li v-for="item in summaryNextActions" :key="item">{{ item }}</li>
                  </ul>
                </div>
              </div>
            </article>
          </section>

          <section class="turns-panel">
            <div class="panel-title">
              <h2>会话记录</h2>
              <p>回顾本次面试中的完整题目、回答、反馈、追问和总结轨迹。</p>
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
import { useRoute, useRouter } from "vue-router";

import { getDocuments, type DocumentItem } from "../../api/document";
import {
  deleteInterviewSession,
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

const route = useRoute();
const router = useRouter();
const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const documents = ref<DocumentItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const selectedSourceDocumentId = ref<number | undefined>();
const selectedDifficulty = ref<string>();
const selectedQuestionType = ref<string>();
const selectedQuestionStrategy = ref("random");
const selectedDrillMode = ref("single_question");
const selectedQuestionCount = ref(3);
const selectedFocusTopic = ref<string>();
const sessions = ref<InterviewSessionListItem[]>([]);
const activeSession = ref<InterviewSessionDetail | null>(null);
const activeSessionId = ref<string | undefined>();
const answerDraft = ref("");
const loadingSessions = ref(false);
const loadingDetail = ref(false);
const startingInterview = ref(false);
const submittingAnswer = ref(false);
const deletingSessionId = ref<string | null>(null);
const presetApplied = ref(false);
const presetFocusLabel = ref("");

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

const questionStrategyOptions = [
  { label: "随机选题", value: "random" },
  { label: "优先最近题目", value: "recent_first" },
  { label: "尽量避开最近题目", value: "avoid_recent" },
];

const drillModeOptions = [
  { label: "单题深挖", value: "single_question" },
  { label: "题组训练", value: "question_set" },
];

const availableDocuments = computed(() =>
  documents.value.filter((item) => item.status === "completed"),
);

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

const hasPresetFocus = computed(() => Boolean(presetFocusLabel.value));

async function loadKnowledgeBases() {
  knowledgeBases.value = await getKnowledgeBases();
  if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length > 0) {
    selectedKnowledgeBaseId.value = knowledgeBases.value[0].id;
  }
}

async function loadDocuments() {
  if (!selectedKnowledgeBaseId.value) {
    documents.value = [];
    selectedSourceDocumentId.value = undefined;
    return;
  }

  documents.value = await getDocuments(selectedKnowledgeBaseId.value);
  if (
    selectedSourceDocumentId.value &&
    !documents.value.some((item) => item.id === selectedSourceDocumentId.value && item.status === "completed")
  ) {
    selectedSourceDocumentId.value = undefined;
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
      source_document_id: selectedSourceDocumentId.value || undefined,
      focus_topic: selectedFocusTopic.value || undefined,
      difficulty: selectedDifficulty.value || undefined,
      question_type: selectedQuestionType.value || undefined,
      question_strategy: selectedQuestionStrategy.value,
      drill_mode: selectedDrillMode.value,
      question_count: selectedDrillMode.value === "question_set" ? selectedQuestionCount.value : undefined,
    });
    activeSessionId.value = result.session_id;
    answerDraft.value = "";
    await Promise.all([loadSessions(), loadSessionDetail(result.session_id)]);
    await clearAutoStartQuery();
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

async function handleDeleteSession(sessionId: string) {
  deletingSessionId.value = sessionId;
  try {
    await deleteInterviewSession(sessionId);

    if (activeSessionId.value === sessionId) {
      activeSessionId.value = undefined;
      activeSession.value = null;
      answerDraft.value = "";
    }

    await loadSessions();

    if (!activeSessionId.value && sessions.value.length > 0) {
      await loadSessionDetail(sessions.value[0].session_id);
    }
  } finally {
    deletingSessionId.value = null;
  }
}

async function refreshAll() {
  await Promise.all([loadKnowledgeBases(), loadDocuments(), loadSessions()]);
  if (activeSessionId.value) {
    await loadSessionDetail(activeSessionId.value);
  }
}

function applyRoutePreset() {
  const knowledgeBaseId = Number(route.query.knowledgeBaseId);
  if (!Number.isNaN(knowledgeBaseId) && knowledgeBaseId > 0) {
    selectedKnowledgeBaseId.value = knowledgeBaseId;
  }

  const sourceDocumentId = Number(route.query.sourceDocumentId);
  if (!Number.isNaN(sourceDocumentId) && sourceDocumentId > 0) {
    selectedSourceDocumentId.value = sourceDocumentId;
  }

  const questionType = typeof route.query.questionType === "string" ? route.query.questionType : undefined;
  if (questionType) {
    selectedQuestionType.value = questionType;
  }

  const questionStrategy = typeof route.query.questionStrategy === "string" ? route.query.questionStrategy : undefined;
  if (questionStrategy) {
    selectedQuestionStrategy.value = questionStrategy;
  }

  const drillMode = typeof route.query.drillMode === "string" ? route.query.drillMode : undefined;
  if (drillMode) {
    selectedDrillMode.value = drillMode;
  }

  const questionCount = Number(route.query.questionCount);
  if (!Number.isNaN(questionCount) && questionCount > 0) {
    selectedQuestionCount.value = questionCount;
  }

  const focusLabel = typeof route.query.focusLabel === "string" ? route.query.focusLabel : "";
  presetFocusLabel.value = focusLabel;
  const focusTopic = typeof route.query.focusTopic === "string" ? route.query.focusTopic : undefined;
  if (focusTopic) {
    selectedFocusTopic.value = focusTopic;
  }
}

async function maybeAutoStartFromPreset() {
  if (presetApplied.value) {
    return;
  }
  presetApplied.value = true;
  if (route.query.autoStart !== "1" || !selectedKnowledgeBaseId.value) {
    return;
  }
  await handleStartInterview();
}

async function clearAutoStartQuery() {
  if (route.query.autoStart !== "1") {
    return;
  }
  const nextQuery = { ...route.query };
  delete nextQuery.autoStart;
  await router.replace({
    path: route.path,
    query: nextQuery,
  });
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
    return "等待回答";
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
    return "面试官";
  }
  if (role === "interviewer_followup") {
    return "面试官追问";
  }
  if (role === "candidate") {
    return "候选人";
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

function formatDrillMode(mode: string) {
  if (mode === "question_set") {
    return "题组训练";
  }
  return "单题深挖";
}

function visibleQuestionTags(tags: string[]) {
  return tags.filter((tag) => ["concept", "scenario", "followup", "design"].includes(tag.toLowerCase()));
}

function buildSessionSubtitle(session: InterviewSessionListItem) {
  const parts = [
    `模式：${formatDrillMode(session.drill_mode)}`,
    `题目 ${session.active_question_number}/${session.question_count}`,
    `状态：${formatStatus(session.status)}`,
  ];
  if (session.difficulty) {
    parts.push(`难度：${formatDifficulty(session.difficulty)}`);
  }
  const primaryTag = visibleQuestionTags(session.question_tags)[0];
  if (primaryTag) {
    parts.push(`题型：${formatQuestionTag(primaryTag)}`);
  }
  if (session.source_document_name) {
    parts.push(`文档：${session.source_document_name}`);
  }
  return parts.join(" | ");
}

watch(selectedKnowledgeBaseId, async () => {
  activeSession.value = null;
  activeSessionId.value = undefined;
  answerDraft.value = "";
  selectedSourceDocumentId.value = undefined;
  await Promise.all([loadDocuments(), loadSessions()]);
});

watch(selectedDrillMode, (value) => {
  if (value === "single_question") {
    selectedQuestionCount.value = 3;
  }
});

onMounted(async () => {
  await loadKnowledgeBases();
  applyRoutePreset();
  await Promise.all([loadDocuments(), loadSessions()]);
  await maybeAutoStartFromPreset();
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

.session-entry {
  display: grid;
  gap: 8px;
}

.session-actions {
  display: flex;
  justify-content: flex-end;
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

.preset-banner {
  display: grid;
  gap: 8px;
  background: rgba(255, 246, 220, 0.82);
  border-color: rgba(245, 158, 11, 0.18);
}

.preset-banner strong,
.preset-banner p {
  margin: 0;
}

.preset-banner p {
  color: var(--text-secondary);
  line-height: 1.7;
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

.number-input {
  width: 100%;
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
  .summary-head,
  .session-actions {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
