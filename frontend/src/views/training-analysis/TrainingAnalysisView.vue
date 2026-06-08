<template>
  <AppShell>
    <div class="page-stack">
      <section class="panel analysis-controls">
        <div class="panel-header">
          <div class="panel-title">
            <h2>训练分析</h2>
            <p>回顾面试练习中的分数趋势、重复出现的薄弱点，以及训练最集中的资料来源。</p>
          </div>
          <el-button text @click="loadAnalysis">刷新</el-button>
        </div>

        <el-form inline class="analysis-filter">
          <el-form-item label="知识库">
            <el-select
              v-model="selectedKnowledgeBaseId"
              placeholder="全部知识库"
              clearable
              class="kb-select"
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
      </section>

      <div v-if="loading" class="panel empty-state">正在加载训练分析...</div>
      <div v-else class="page-stack">
        <section class="stats-grid">
          <article class="stat-card">
            <span>总会话数</span>
            <strong>{{ analysis?.total_sessions ?? 0 }}</strong>
            <p class="meta-text">当前筛选条件下的全部面试会话数量。</p>
          </article>
          <article class="stat-card">
            <span>已完成会话</span>
            <strong>{{ analysis?.completed_sessions ?? 0 }}</strong>
            <p class="meta-text">只有已完成的会话才会进入训练分析。</p>
          </article>
          <article class="stat-card">
            <span>平均分</span>
            <strong>{{ analysis?.average_score ?? "N/A" }}</strong>
            <p class="meta-text">快速反映你当前面试表现稳定度的指标。</p>
          </article>
          <article class="stat-card">
            <span>最近得分</span>
            <strong>{{ analysis?.latest_score ?? "N/A" }}</strong>
            <p class="meta-text">最近一次已完成面试训练的结果。</p>
          </article>
        </section>

        <div class="analysis-grid">
          <section class="panel soft analysis-grid-wide">
            <div class="panel-title">
              <h2>专项训练效果</h2>
              <p>跟踪针对某个薄弱点的反复专项训练，是否真的带来了分数提升。</p>
            </div>
            <div v-if="analysis?.focus_drill_effects.length" class="effect-card-list">
              <article
                v-for="item in analysis.focus_drill_effects"
                :key="item.focus_label"
                class="effect-card"
              >
                <div class="effect-copy">
                  <span class="section-label">专项主题</span>
                  <h3>{{ item.focus_label }}</h3>
                  <p>已进行了 {{ item.session_count }} 次专项训练，最近一次练习时间为 {{ formatDate(item.last_practiced_at) }}。</p>
                </div>
                <div class="effect-metrics">
                  <div class="effect-metric">
                    <span>平均分</span>
                    <strong>{{ item.average_score }}</strong>
                  </div>
                  <div class="effect-metric">
                    <span>最近分数</span>
                    <strong>{{ item.latest_score }}</strong>
                  </div>
                  <div class="effect-metric">
                    <span>最佳分数</span>
                    <strong>{{ item.best_score }}</strong>
                  </div>
                  <div class="effect-metric">
                    <span>变化值</span>
                    <strong :class="item.score_delta >= 0 ? 'trend-up' : 'trend-down'">
                      {{ item.score_delta >= 0 ? "+" : "" }}{{ item.score_delta }}
                    </strong>
                  </div>
                </div>
              </article>
            </div>
            <div v-else class="empty-state">先做几次专项训练，系统才会开始追踪薄弱点改善情况。</div>
          </section>

          <section class="panel soft analysis-grid-wide">
            <div class="panel-title">
              <h2>薄弱点专项计划</h2>
              <p>把反复出现的薄弱点直接转成可一键开始的专项面试训练。</p>
            </div>
            <div v-if="analysis?.focus_drills.length" class="drill-card-list">
              <article
                v-for="item in analysis.focus_drills"
                :key="`${item.focus_label}-${item.question_type}`"
                class="drill-card"
              >
                <div class="drill-copy">
                  <span class="section-label">{{ item.question_type ? formatQuestionType(item.question_type) : "专项训练" }}</span>
                  <h3>{{ item.title }}</h3>
                  <p>{{ item.description }}</p>
                  <div class="chip-list">
                    <span class="analysis-chip">{{ formatDrillMode(item.drill_mode) }}</span>
                    <span class="analysis-chip">题目数 | {{ item.question_count }}</span>
                    <span v-if="item.source_document_name" class="analysis-chip document-chip">{{ item.source_document_name }}</span>
                  </div>
                </div>
                <el-button type="primary" @click="startFocusDrill(item)">
                  开始训练
                </el-button>
              </article>
            </div>
            <div v-else class="empty-state">完成更多面试训练后，这里会生成专项训练方案。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>推荐训练方向</h2>
              <p>这些建议基于重复薄弱点、题型分布和最近分数变化自动生成。</p>
            </div>
            <div v-if="analysis?.recommended_focus.length" class="focus-list">
              <article
                v-for="item in analysis.recommended_focus"
                :key="item"
                class="focus-card"
              >
                {{ item }}
              </article>
            </div>
            <div v-else class="empty-state">完成更多面试训练后，这里会出现更稳定的建议。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>最近成绩</h2>
              <p>按时间从近到远展示最近完成的面试训练结果。</p>
            </div>
            <div v-if="analysis?.recent_scores.length" class="score-list">
              <article
                v-for="item in analysis.recent_scores"
                :key="item.session_id"
                class="score-row"
              >
                <div>
                  <strong>{{ item.score }}/10</strong>
                  <p>{{ formatDate(item.started_at) }}</p>
                </div>
                <span class="pill">{{ item.session_id.slice(0, 8) }}</span>
              </article>
            </div>
            <div v-else class="empty-state">暂时还没有已完成的面试成绩。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>高频薄弱点</h2>
              <p>从逐轮反馈和面试总结中提取出的重复改进主题。</p>
            </div>
            <div v-if="analysis?.common_weak_points.length" class="ranking-list">
              <article
                v-for="item in analysis.common_weak_points"
                :key="item.label"
                class="ranking-row"
              >
                <div class="ranking-copy">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.count }} 次会话</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill danger" :style="{ width: `${barWidth(item.count, maxWeakPointCount)}%` }" />
                </div>
              </article>
            </div>
            <div v-else class="empty-state">暂时还没有薄弱点数据。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>高频亮点</h2>
              <p>你在面试回答中已经比较稳定展现出的正向能力模式。</p>
            </div>
            <div v-if="analysis?.common_strengths.length" class="ranking-list">
              <article
                v-for="item in analysis.common_strengths"
                :key="item.label"
                class="ranking-row"
              >
                <div class="ranking-copy">
                  <strong>{{ item.label }}</strong>
                  <span>{{ item.count }} 次会话</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill success" :style="{ width: `${barWidth(item.count, maxStrengthCount)}%` }" />
                </div>
              </article>
            </div>
            <div v-else class="empty-state">暂时还没有亮点数据。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>题型分布</h2>
              <p>查看你已完成的面试练习中，哪些题型出现得最多。</p>
            </div>
            <div v-if="analysis?.question_type_breakdown.length" class="chip-list">
              <span
                v-for="item in analysis.question_type_breakdown"
                :key="item.label"
                class="analysis-chip"
              >
                {{ item.label }} | {{ item.count }}
              </span>
            </div>
            <div v-else class="empty-state">暂时还没有题型数据。</div>
          </section>

          <section class="panel soft">
            <div class="panel-title">
              <h2>资料来源分布</h2>
              <p>查看最近训练中最常被用到的是哪些上传资料。</p>
            </div>
            <div v-if="analysis?.source_document_breakdown.length" class="chip-list">
              <span
                v-for="item in analysis.source_document_breakdown"
                :key="item.label"
                class="analysis-chip document-chip"
              >
                {{ item.label }} | {{ item.count }}
              </span>
            </div>
            <div v-else class="empty-state">暂时还没有来源文档数据。</div>
          </section>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";

import { getKnowledgeBases, type KnowledgeBaseItem } from "../../api/knowledgeBase";
import {
  getTrainingAnalysis,
  type TrainingAnalysisResponse,
  type TrainingDrillRecommendation,
} from "../../api/interview";
import AppShell from "../../layout/AppShell.vue";

const router = useRouter();
const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const analysis = ref<TrainingAnalysisResponse | null>(null);
const loading = ref(false);

const maxWeakPointCount = computed(() => {
  return Math.max(...(analysis.value?.common_weak_points.map((item) => item.count) ?? [1]));
});

const maxStrengthCount = computed(() => {
  return Math.max(...(analysis.value?.common_strengths.map((item) => item.count) ?? [1]));
});

async function loadKnowledgeBases() {
  knowledgeBases.value = await getKnowledgeBases();
}

async function loadAnalysis() {
  loading.value = true;
  try {
    analysis.value = await getTrainingAnalysis(selectedKnowledgeBaseId.value);
  } finally {
    loading.value = false;
  }
}

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("zh-CN");
}

function barWidth(value: number, max: number) {
  if (max <= 0) {
    return 0;
  }
  return Math.max(14, Math.round((value / max) * 100));
}

function formatQuestionType(value: string) {
  if (value === "concept") {
    return "概念题专项";
  }
  if (value === "scenario") {
    return "场景题专项";
  }
  if (value === "followup") {
    return "追问题专项";
  }
  if (value === "design") {
    return "设计题专项";
  }
  return value;
}

function formatDrillMode(value: string) {
  if (value === "question_set") {
    return "题组训练";
  }
  return "单题深挖";
}

function startFocusDrill(item: TrainingDrillRecommendation) {
  const query: Record<string, string> = {
    drillMode: item.drill_mode,
    questionCount: String(item.question_count),
    questionStrategy: item.question_strategy,
    autoStart: "1",
    focusLabel: item.focus_label,
    focusTopic: item.focus_label,
  };
  if (item.knowledge_base_id) {
    query.knowledgeBaseId = String(item.knowledge_base_id);
  }
  if (item.question_type) {
    query.questionType = item.question_type;
  }
  if (item.source_document_id) {
    query.sourceDocumentId = String(item.source_document_id);
  }
  void router.push({
    path: "/interview",
    query,
  });
}

watch(selectedKnowledgeBaseId, async () => {
  await loadAnalysis();
});

onMounted(async () => {
  await loadKnowledgeBases();
  await loadAnalysis();
});
</script>

<style scoped>
.analysis-controls {
  display: grid;
  gap: 16px;
}

.analysis-filter {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.kb-select {
  min-width: 260px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}

.analysis-grid-wide {
  grid-column: 1 / -1;
}

.focus-list,
.score-list,
.ranking-list,
.chip-list {
  display: grid;
  gap: 12px;
}

.drill-card-list {
  display: grid;
  gap: 14px;
}

.effect-card-list {
  display: grid;
  gap: 14px;
}

.drill-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--border-soft);
}

.effect-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 18px;
  align-items: center;
  padding: 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--border-soft);
}

.drill-copy {
  display: grid;
  gap: 10px;
}

.effect-copy {
  display: grid;
  gap: 8px;
}

.drill-copy h3,
.drill-copy p {
  margin: 0;
}

.effect-copy h3,
.effect-copy p {
  margin: 0;
}

.drill-copy p {
  color: var(--text-secondary);
  line-height: 1.7;
}

.effect-copy p {
  color: var(--text-secondary);
  line-height: 1.7;
}

.effect-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(88px, 1fr));
  gap: 12px;
}

.effect-metric {
  padding: 14px 12px;
  border-radius: 14px;
  background: rgba(243, 247, 251, 0.82);
  border: 1px solid rgba(20, 33, 61, 0.08);
  text-align: center;
}

.effect-metric span {
  display: block;
  margin-bottom: 6px;
  color: var(--text-secondary);
}

.effect-metric strong {
  font-size: 1.1rem;
}

.trend-up {
  color: #0f9f6e;
}

.trend-down {
  color: #d14343;
}

.focus-card {
  padding: 16px 18px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--border-soft);
  line-height: 1.7;
}

.score-row,
.ranking-row {
  display: grid;
  gap: 12px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid var(--border-soft);
}

.score-row {
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
}

.score-row p,
.ranking-copy span {
  margin: 4px 0 0;
  color: var(--text-secondary);
}

.ranking-copy {
  display: grid;
  gap: 4px;
}

.bar-track {
  height: 10px;
  border-radius: 999px;
  background: rgba(20, 33, 61, 0.08);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
}

.bar-fill.danger {
  background: linear-gradient(90deg, #f97316, #ef4444);
}

.bar-fill.success {
  background: linear-gradient(90deg, #10b981, #53b3cb);
}

.analysis-chip {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(31, 111, 235, 0.08);
  border: 1px solid rgba(31, 111, 235, 0.14);
  color: var(--text-secondary);
}

.document-chip {
  background: rgba(16, 185, 129, 0.08);
  border-color: rgba(16, 185, 129, 0.16);
}

@media (max-width: 1080px) {
  .stats-grid,
  .analysis-grid {
    grid-template-columns: 1fr;
  }

  .analysis-grid-wide {
    grid-column: auto;
  }
}

@media (max-width: 780px) {
  .drill-card,
  .effect-card {
    grid-template-columns: 1fr;
    align-items: stretch;
  }

  .effect-metrics {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
