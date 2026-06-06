<template>
  <div class="shell">
    <header class="app-header">
      <div class="header-brand">
        <div class="brand-mark">IA</div>
        <div class="brand-copy">
          <p class="brand-kicker">Interview Workspace</p>
          <h1>Interview Agent</h1>
        </div>
      </div>

      <nav class="header-nav" aria-label="Primary">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="header-nav-link"
        >
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="header-actions">
        <div class="account-card">
          <span class="account-label">当前账号</span>
          <strong>{{ authStore.user?.username || "未加载用户" }}</strong>
          <small>{{ authStore.user?.email || "登录后可查看账号信息" }}</small>
        </div>
        <el-button class="logout-button" @click="handleLogout">退出登录</el-button>
      </div>
    </header>

    <main class="content">
      <div class="page-header">
        <div class="page-heading">
          <div class="page-title-row">
            <h2>{{ currentSection.label }}</h2>
            <span class="page-summary">{{ currentSection.description }}</span>
          </div>
        </div>

        <div class="page-meta">
          <span class="pill">RAG Interview Copilot</span>
          <span class="pill">{{ authStore.user?.username || "访客" }}</span>
        </div>
      </div>

      <slot />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

import { useAuthStore } from "../stores/auth";

const route = useRoute();
const router = useRouter();
const authStore = useAuthStore();

const navItems = [
  { to: "/", label: "概览", description: "查看系统状态与常用入口" },
  { to: "/knowledge-bases", label: "知识库", description: "创建并管理岗位资料集合" },
  { to: "/documents", label: "文档中心", description: "上传资料并跟踪入库进度" },
  { to: "/qa", label: "问答助手", description: "像专属面试助手一样使用你的知识库进行对话" },
  { to: "/history", label: "历史记录", description: "查看会话历史与处理轨迹" }
];

const currentSection = computed(() => {
  return navItems.find((item) => item.to === route.path) || navItems[0];
});

async function handleLogout() {
  authStore.clearAuth();
  await router.push("/login");
}
</script>

<style scoped>
.shell {
  min-height: 100vh;
  padding: 18px;
}

.app-header {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 18px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.9);
  border-radius: 28px;
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand-mark {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: linear-gradient(135deg, #53b3cb 0%, #78c6e2 100%);
  color: #0d1b2a;
  font-weight: 800;
  letter-spacing: 0.06em;
}

.brand-copy {
  min-width: 0;
}

.brand-kicker,
.account-label {
  margin: 0 0 4px;
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.brand-copy h1 {
  margin: 0;
  font-size: 1.45rem;
}

.header-nav {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: nowrap;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 2px;
  scrollbar-width: none;
}

.header-nav::-webkit-scrollbar {
  display: none;
}

.header-nav-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 16px;
  border-radius: 999px;
  border: 1px solid rgba(20, 33, 61, 0.08);
  background: rgba(255, 255, 255, 0.54);
  color: var(--text-secondary);
  font-weight: 700;
  transition: transform 180ms ease, border-color 180ms ease, background 180ms ease, color 180ms ease;
  white-space: nowrap;
  flex: 0 0 auto;
}

.header-nav-link:hover {
  transform: translateY(-1px);
  border-color: rgba(31, 111, 235, 0.2);
  background: rgba(31, 111, 235, 0.08);
  color: #1f6feb;
}

.header-nav-link.router-link-active {
  border-color: rgba(31, 111, 235, 0.24);
  background: linear-gradient(135deg, rgba(31, 111, 235, 0.14), rgba(58, 166, 185, 0.12));
  color: #123b8f;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.account-card {
  display: grid;
  gap: 2px;
  min-width: 220px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(243, 247, 251, 0.92);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.account-card strong,
.account-card small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.account-card small {
  color: var(--text-secondary);
}

.logout-button {
  border: none;
  white-space: nowrap;
}

.content {
  min-width: 0;
  padding: 20px 8px 28px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 24px;
}

.page-heading {
  min-width: 0;
}

.page-title-row {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 12px;
}

.page-title-row h2 {
  margin: 0;
  font-size: clamp(1.7rem, 3vw, 2.3rem);
  line-height: 1.1;
}

.page-summary {
  color: var(--text-secondary);
  line-height: 1.6;
}

.page-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

@media (max-width: 1280px) {
  .app-header {
    grid-template-columns: 1fr;
    justify-items: stretch;
    gap: 14px;
  }

  .header-nav {
    justify-content: flex-start;
  }

  .header-actions {
    justify-content: space-between;
    flex-wrap: wrap;
  }
}

@media (max-width: 820px) {
  .shell {
    padding: 12px;
  }

  .app-header {
    padding: 16px;
    gap: 14px;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .account-card {
    min-width: 0;
  }

  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 640px) {
  .page-title-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
