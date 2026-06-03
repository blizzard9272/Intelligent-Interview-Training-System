<template>
  <AppShell>
    <div class="grid">
      <section class="panel">
        <h2>Upload Document</h2>
        <el-form label-position="top">
          <el-form-item label="Knowledge Base">
            <el-select v-model="selectedKnowledgeBaseId" placeholder="Select a knowledge base" class="full">
              <el-option
                v-for="item in knowledgeBases"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="File">
            <input class="file-input" type="file" accept=".txt,.md,.pdf" @change="handleFileChange" />
          </el-form-item>
          <el-button type="primary" :loading="uploading" @click="handleUpload">Upload and Create Task</el-button>
        </el-form>
        <p v-if="selectedFile">Selected file: {{ selectedFile.name }}</p>
        <p v-if="message" class="success">{{ message }}</p>
        <p v-if="errorMessage" class="error">{{ errorMessage }}</p>
      </section>

      <section class="panel">
        <div class="toolbar">
          <h2>Documents</h2>
          <div class="toolbar-actions">
            <el-select v-model="filterKnowledgeBaseId" clearable placeholder="Filter by knowledge base" class="filter">
              <el-option
                v-for="item in knowledgeBases"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-button @click="loadDocuments">Refresh Documents</el-button>
            <el-button @click="loadTasks">Refresh Tasks</el-button>
          </div>
        </div>

        <div v-if="loadingDocuments">Loading documents...</div>
        <div v-else-if="documents.length === 0">No documents yet.</div>
        <div v-else class="list">
          <article v-for="item in documents" :key="item.id" class="item">
            <div class="item-top">
              <div>
                <h3>{{ item.file_name }}</h3>
                <p>{{ item.file_type.toUpperCase() }} / {{ formatSize(item.file_size) }}</p>
                <p>Status: {{ item.status }}</p>
              </div>
              <el-button type="danger" text @click="handleDelete(item.id)">Delete</el-button>
            </div>
          </article>
        </div>
      </section>
    </div>

    <section class="panel tasks-panel">
      <h2>Ingestion Tasks</h2>
      <div v-if="loadingTasks">Loading tasks...</div>
      <div v-else-if="tasks.length === 0">No tasks yet.</div>
      <div v-else class="task-list">
        <article v-for="task in tasks" :key="task.id" class="task-item">
          <div class="task-header">
            <strong>Task #{{ task.id }}</strong>
            <span>{{ task.status }}</span>
          </div>
          <p>Document ID: {{ task.document_id }}</p>
          <p>Progress: {{ task.progress }}%</p>
          <p>{{ task.message || "No message" }}</p>
        </article>
      </div>
    </section>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import { deleteDocument, getDocuments, uploadDocument, type DocumentItem } from "../../api/document";
import { getKnowledgeBases, type KnowledgeBaseItem } from "../../api/knowledgeBase";
import { getTasks, type IngestionTaskItem } from "../../api/task";
import AppShell from "../../layout/AppShell.vue";

const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const documents = ref<DocumentItem[]>([]);
const tasks = ref<IngestionTaskItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const filterKnowledgeBaseId = ref<number | undefined>();
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const loadingDocuments = ref(false);
const loadingTasks = ref(false);
const message = ref("");
const errorMessage = ref("");

const hasKnowledgeBase = computed(() => knowledgeBases.value.length > 0);

async function loadKnowledgeBases() {
  knowledgeBases.value = await getKnowledgeBases();
  if (!selectedKnowledgeBaseId.value && knowledgeBases.value.length > 0) {
    selectedKnowledgeBaseId.value = knowledgeBases.value[0].id;
  }
}

async function loadDocuments() {
  loadingDocuments.value = true;
  errorMessage.value = "";
  try {
    documents.value = await getDocuments(filterKnowledgeBaseId.value);
  } catch {
    errorMessage.value = "Failed to load documents";
  } finally {
    loadingDocuments.value = false;
  }
}

async function loadTasks() {
  loadingTasks.value = true;
  errorMessage.value = "";
  try {
    tasks.value = await getTasks();
  } catch {
    errorMessage.value = "Failed to load tasks";
  } finally {
    loadingTasks.value = false;
  }
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] ?? null;
}

async function handleUpload() {
  if (!hasKnowledgeBase.value) {
    errorMessage.value = "Create a knowledge base first";
    return;
  }
  if (!selectedKnowledgeBaseId.value) {
    errorMessage.value = "Select a knowledge base";
    return;
  }
  if (!selectedFile.value) {
    errorMessage.value = "Select a file to upload";
    return;
  }

  uploading.value = true;
  errorMessage.value = "";
  message.value = "";
  try {
    const result = await uploadDocument(selectedKnowledgeBaseId.value, selectedFile.value);
    message.value = `Upload complete. Task #${result.task_id} created.`;
    selectedFile.value = null;
    await Promise.all([loadDocuments(), loadTasks()]);
  } catch {
    errorMessage.value = "Upload failed. Check the file type or backend status.";
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(documentId: number) {
  errorMessage.value = "";
  message.value = "";
  try {
    await deleteDocument(documentId);
    message.value = "Document deleted.";
    await Promise.all([loadDocuments(), loadTasks()]);
  } catch {
    errorMessage.value = "Delete failed.";
  }
}

function formatSize(size: number | null) {
  if (!size) {
    return "Unknown";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

watch(filterKnowledgeBaseId, () => {
  void loadDocuments();
});

onMounted(async () => {
  try {
    await loadKnowledgeBases();
    await Promise.all([loadDocuments(), loadTasks()]);
  } catch {
    errorMessage.value = "Failed to initialize page data";
  }
});
</script>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.panel {
  padding: 28px;
  background: #ffffff;
  border-radius: 20px;
}

.tasks-panel {
  margin-top: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: center;
}

.toolbar-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filter,
.full {
  width: 100%;
}

.list,
.task-list {
  display: grid;
  gap: 16px;
  margin-top: 20px;
}

.item,
.task-item {
  padding: 18px;
  border-radius: 16px;
  background: #f8fafc;
}

.item-top,
.task-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.item h3 {
  margin: 0 0 8px;
}

.item p,
.task-item p {
  margin: 6px 0;
  color: #475569;
}

.file-input {
  width: 100%;
}

.error {
  color: #dc2626;
}

.success {
  color: #15803d;
}
</style>
