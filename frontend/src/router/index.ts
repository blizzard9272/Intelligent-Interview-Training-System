import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import AuthLoginView from "../views/auth/LoginView.vue";
import AuthRegisterView from "../views/auth/RegisterView.vue";
import DashboardView from "../views/dashboard/DashboardView.vue";
import DocumentsView from "../views/documents/DocumentsView.vue";
import HistoryView from "../views/history/HistoryView.vue";
import InterviewView from "../views/interview/InterviewView.vue";
import KnowledgeBaseView from "../views/knowledge-base/KnowledgeBaseView.vue";
import QAView from "../views/qa/QAView.vue";
import pinia from "../stores";
import { useAuthStore } from "../stores/auth";

const routes: RouteRecordRaw[] = [
  { path: "/login", name: "login", component: AuthLoginView },
  { path: "/register", name: "register", component: AuthRegisterView },
  { path: "/", name: "dashboard", component: DashboardView },
  { path: "/knowledge-bases", name: "knowledge-bases", component: KnowledgeBaseView },
  { path: "/documents", name: "documents", component: DocumentsView },
  { path: "/qa", name: "qa", component: QAView },
  { path: "/history", name: "history", component: HistoryView },
  { path: "/interview", name: "interview", component: InterviewView },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore(pinia);
  const publicPaths = ["/login", "/register"];
  if (!publicPaths.includes(to.path) && !authStore.token) {
    return "/login";
  }
  if (authStore.token && !authStore.user && !publicPaths.includes(to.path)) {
    try {
      await authStore.loadCurrentUser();
    } catch {
      authStore.clearAuth();
      return "/login";
    }
  }
  if (publicPaths.includes(to.path) && authStore.token) {
    return "/";
  }
  return true;
});

export default router;
