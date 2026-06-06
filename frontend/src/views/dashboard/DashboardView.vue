<template>
  <AppShell>
    <div class="page-stack">
      <section class="hero-card">
        <span class="section-label">智能面试知识工作台</span>
        <h1>把知识库、文档入库和问答会话整合在同一个简洁空间里。</h1>
        <p>
          当前版本已经覆盖知识库创建、文档上传、异步入库任务追踪和 RAG 问答闭环。
          现在你可以从左侧导航进入各模块，继续完成资料沉淀与面试问答。
        </p>
      </section>

      <section class="stats-grid">
        <article class="stat-card">
          <span>系统焦点</span>
          <strong>RAG</strong>
          <p class="meta-text">围绕面试材料构建知识增强问答体验。</p>
        </article>
        <article class="stat-card">
          <span>功能模块</span>
          <strong>4+</strong>
          <p class="meta-text">知识库、文档、任务、问答已经联通。</p>
        </article>
        <article class="stat-card">
          <span>当前用户</span>
          <strong>{{ authStore.user?.username || "未加载" }}</strong>
          <p class="meta-text">{{ authStore.user?.email || "登录后可查看账号信息" }}</p>
        </article>
      </section>

      <section class="panel soft">
        <div class="panel-header">
          <div class="panel-title">
            <h2>推荐操作路径</h2>
            <p>如果你想快速开始，可以按下面的顺序完成一次完整流程。</p>
          </div>
        </div>
        <div class="steps">
          <article class="step-card">
            <span class="step-index">01</span>
            <h3>创建知识库</h3>
            <p>先为某个岗位或主题建立一个专属知识空间。</p>
          </article>
          <article class="step-card">
            <span class="step-index">02</span>
            <h3>上传资料文档</h3>
            <p>将面试题、JD、简历、项目说明等材料上传并入库。</p>
          </article>
          <article class="step-card">
            <span class="step-index">03</span>
            <h3>开始追问与验证</h3>
            <p>通过问答会话验证知识召回质量，并逐步优化内容。</p>
          </article>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import AppShell from "../../layout/AppShell.vue";
import { useAuthStore } from "../../stores/auth";

const authStore = useAuthStore();
</script>

<style scoped>
.steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.step-card {
  padding: 22px;
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--border-soft);
}

.step-card h3 {
  margin: 12px 0 8px;
}

.step-card p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.7;
}

.step-index {
  color: #1f6feb;
  font-size: 0.86rem;
  font-weight: 800;
  letter-spacing: 0.08em;
}
</style>
