<template>
  <AppShell>
    <div class="view-grid two-column">
      <section class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h2>新建知识库</h2>
            <p>为某个岗位、项目主题或面试方向建立独立的知识空间。</p>
          </div>
        </div>
        <el-form :model="form" label-position="top">
          <el-form-item label="名称">
            <el-input v-model="form.name" placeholder="例如：AI Agent 面试库" />
          </el-form-item>
          <el-form-item label="岗位方向">
            <el-input v-model="form.job_role" placeholder="例如：AI Agent 工程师" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="form.description"
              type="textarea"
              :rows="4"
              placeholder="输入该知识库的适用场景、资料范围或岗位背景"
            />
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleCreate">创建知识库</el-button>
        </el-form>
        <p v-if="message" class="status-message success">{{ message }}</p>
        <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>
      </section>

      <section class="panel">
        <div class="panel-header">
          <div class="panel-title">
            <h2>知识库列表</h2>
            <p>浏览当前可用的知识空间，并确认岗位方向和资料范围。</p>
          </div>
          <el-button text @click="loadItems">刷新</el-button>
        </div>
        <div v-if="loading" class="empty-state">正在加载知识库...</div>
        <div v-else-if="items.length === 0" class="empty-state">还没有知识库，先在左侧创建一个吧。</div>
        <div v-else class="item-list">
          <article v-for="item in items" :key="item.id" class="list-card">
            <div class="item-head">
              <h3>{{ item.name }}</h3>
              <span class="pill mono">#{{ item.id }}</span>
            </div>
            <p>{{ item.job_role || "尚未设置岗位方向" }}</p>
            <p>{{ item.description || "暂无描述" }}</p>
          </article>
        </div>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";

import AppShell from "../../layout/AppShell.vue";
import { createKnowledgeBase, getKnowledgeBases, KnowledgeBaseItem } from "../../api/knowledgeBase";

const form = reactive({
  name: "",
  description: "",
  job_role: ""
});
const items = ref<KnowledgeBaseItem[]>([]);
const loading = ref(false);
const submitting = ref(false);
const message = ref("");
const errorMessage = ref("");

async function loadItems() {
  loading.value = true;
  try {
    items.value = await getKnowledgeBases();
  } catch {
    errorMessage.value = "获取知识库列表失败，请确认后端服务已经启动。";
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!form.name) {
    errorMessage.value = "请输入知识库名称。";
    return;
  }
  submitting.value = true;
  message.value = "";
  errorMessage.value = "";
  try {
    await createKnowledgeBase(form);
    message.value = "知识库创建成功。";
    form.name = "";
    form.description = "";
    form.job_role = "";
    await loadItems();
  } catch {
    errorMessage.value = "创建知识库失败，请稍后重试。";
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  void loadItems();
});
</script>

<style scoped>
.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.list-card h3 {
  margin: 0;
}

.list-card p {
  margin: 10px 0 0;
  color: var(--text-secondary);
  line-height: 1.7;
}
</style>
