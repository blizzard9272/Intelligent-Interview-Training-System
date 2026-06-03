<template>
  <AppShell>
    <div class="grid">
      <section class="panel">
        <h2>新建知识库</h2>
        <el-form :model="form" label-position="top">
          <el-form-item label="名称">
            <el-input v-model="form.name" placeholder="例如：AI Agent" />
          </el-form-item>
          <el-form-item label="岗位方向">
            <el-input v-model="form.job_role" placeholder="例如：AI Agent 工程师" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="4" placeholder="输入知识库描述" />
          </el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleCreate">创建知识库</el-button>
        </el-form>
        <p v-if="message" class="success">{{ message }}</p>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </section>
      <section class="panel">
        <h2>知识库列表</h2>
        <el-button text @click="loadItems">刷新</el-button>
        <div v-if="loading">加载中...</div>
        <div v-else-if="items.length === 0">暂无知识库</div>
        <div v-else class="list">
          <article v-for="item in items" :key="item.id" class="item">
            <h3>{{ item.name }}</h3>
            <p>{{ item.job_role || "未设置岗位方向" }}</p>
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
    errorMessage.value = "获取知识库列表失败，请确认后端已启动";
  } finally {
    loading.value = false;
  }
}

async function handleCreate() {
  if (!form.name) {
    errorMessage.value = "请输入知识库名称";
    return;
  }
  submitting.value = true;
  message.value = "";
  errorMessage.value = "";
  try {
    await createKnowledgeBase(form);
    message.value = "知识库创建成功";
    form.name = "";
    form.description = "";
    form.job_role = "";
    await loadItems();
  } catch {
    errorMessage.value = "创建知识库失败";
  } finally {
    submitting.value = false;
  }
}

onMounted(() => {
  void loadItems();
});
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
}

.panel {
  padding: 28px;
  background: #ffffff;
  border-radius: 20px;
}

.list {
  display: grid;
  gap: 16px;
  margin-top: 16px;
}

.item {
  padding: 18px;
  border-radius: 14px;
  background: #f8fafc;
}

.item h3 {
  margin: 0 0 8px;
}

.item p {
  margin: 6px 0;
  color: #475569;
}

.error {
  color: #dc2626;
}

.success {
  color: #15803d;
}
</style>
