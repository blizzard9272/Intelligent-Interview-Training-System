<template>
  <AppShell>
    <div class="documents-layout">
      <section class="panel upload-panel">
        <div class="panel-header">
          <div class="panel-title">
            <h2>上传文档</h2>
            <p>选择知识库并上传面试资料，系统会自动创建入库任务并写入向量库。</p>
          </div>
        </div>

        <el-form label-position="top">
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

          <el-form-item label="文件">
            <input class="file-input" type="file" accept=".txt,.md,.pdf" @change="handleFileChange" />
          </el-form-item>

          <p class="support-note">支持上传的文件类型：`.txt`、`.md`、`.pdf`，单个文件最大 50 MB</p>

          <el-button type="primary" :loading="uploading" class="full-width" @click="handleUpload">
            上传并创建任务
          </el-button>
        </el-form>

        <p v-if="selectedFile" class="input-note">已选择文件：{{ selectedFile.name }}</p>
        <p v-if="message" class="status-message success">{{ message }}</p>
        <p v-if="errorMessage" class="status-message error">{{ errorMessage }}</p>

        <div class="template-entry">
          <div class="template-entry-copy">
            <div class="panel-title">
              <h2>文件模板</h2>
              <p>上传前先看模板示例，确认什么样的资料更适合后续的分块、检索和问答。</p>
            </div>
            <div class="template-entry-actions">
              <el-button @click="downloadTemplate">下载模板</el-button>
              <el-button @click="templatePreviewVisible = true">查看模板预览</el-button>
            </div>
          </div>
        </div>
      </section>

      <section class="panel documents-panel">
        <div class="toolbar">
          <div class="panel-title">
            <h2>文档列表</h2>
            <p>查看文档入库状态、分块数量与更新时间，并支持继续预览分块内容。</p>
          </div>

          <div class="toolbar-actions">
            <el-select
              v-model="filterKnowledgeBaseId"
              clearable
              placeholder="按知识库筛选"
              class="filter"
            >
              <el-option
                v-for="item in knowledgeBases"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-button @click="loadDocuments">刷新文档</el-button>
          </div>
        </div>

        <div v-if="loadingDocuments" class="empty-state">正在加载文档...</div>
        <div v-else-if="documents.length === 0" class="empty-state">还没有文档，先上传一份资料开始吧。</div>
        <div v-else class="stack-list">
          <DocumentListCard
            v-for="item in documents"
            :key="item.id"
            :item="item"
            :size-label="formatSize(item.file_size)"
            :updated-at-label="formatDate(item.updated_at)"
            @preview="openChunkDrawer(item)"
            @delete="handleDelete(item.id)"
          />
        </div>
      </section>
    </div>

    <el-drawer
      v-model="drawerVisible"
      title="文档分块预览"
      direction="rtl"
      size="50%"
      class="chunk-drawer"
    >
      <div v-if="activeDocument" class="drawer-body">
        <div class="drawer-header">
          <h3>{{ activeDocument.file_name }}</h3>
          <p>
            {{ activeDocument.file_type.toUpperCase() }} / 共 {{ activeDocument.chunk_count }} 段 /
            状态：{{ activeDocument.status }}
          </p>
        </div>

        <div v-if="loadingChunks" class="empty-state">正在加载分块内容...</div>
        <div v-else-if="chunkItems.length === 0" class="empty-state">当前文档还没有可展示的分块内容。</div>
        <div v-else class="chunk-list">
          <DocumentChunkCard
            v-for="chunk in chunkItems"
            :key="chunk.chunk_index"
            :chunk="chunk"
          />
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="templatePreviewVisible"
      title="文件模板预览"
      width="min(960px, 92vw)"
      align-center
      class="template-dialog"
    >
      <div class="template-guide">
        <div class="guide-head">
          <span class="section-label">推荐模板</span>
          <h3>什么样的资料更适合分块、检索和问答</h3>
          <p>如果资料本身结构清晰，后续分块、召回和引用展示的效果都会明显更好。</p>
        </div>

        <div class="guide-grid">
          <article class="guide-card">
            <h4>推荐结构</h4>
            <ul class="guide-list">
              <li>优先使用带明确标题层级的 `Markdown` 或可复制文字的 `PDF`。</li>
              <li>一份文档尽量围绕一个主题，例如“LangChain 基础”或“面试题题解”。</li>
              <li>使用清晰的小节标题，例如“概念解释 / 示例代码 / 常见问题 / 面试考点”。</li>
              <li>长文档建议按章节拆分，而不是把多个主题混在同一个 PDF 里。</li>
            </ul>
          </article>

          <article class="guide-card">
            <h4>最佳实践</h4>
            <ul class="guide-list">
              <li>如果是题库资料，建议每道题保持“问题 + 回答 + 关键点总结”的固定结构。</li>
              <li>如果是技术笔记，建议保留代码块、术语定义和场景说明。</li>
              <li>尽量减少大段图片截图，因为纯图片内容无法直接参与文本检索。</li>
              <li>上传前可以先检查 PDF 是否支持复制文字，支持则通常更容易成功入库。</li>
            </ul>
          </article>

          <article class="guide-card warning">
            <h4>需要避免</h4>
            <ul class="guide-list">
              <li>扫描件 PDF 或拍照生成的图片型 PDF，没有文字层时通常需要 OCR。</li>
              <li>整份资料只有大段连续文本、没有标题或没有换段，会影响分块质量。</li>
              <li>过多页眉页脚、广告、水印和目录噪声，会降低检索结果质量。</li>
              <li>把简历、八股、项目题、系统设计等完全不同主题硬塞进一个文件。</li>
            </ul>
          </article>
        </div>

        <el-tabs v-model="activeTemplateKey" class="template-tabs">
          <el-tab-pane
            v-for="template in templateOptions"
            :key="template.key"
            :label="template.label"
            :name="template.key"
          >
            <div class="template-preview-sheet">
              <div class="sheet-header">
                <div>
                  <span class="sheet-kicker">{{ template.kicker }}</span>
                  <h4>{{ template.title }}</h4>
                </div>
                <div class="sheet-actions">
                  <span class="pill">{{ template.badge }}</span>
                  <el-button @click="downloadTemplate">下载当前模板</el-button>
                </div>
              </div>

              <div class="sheet-body">
                <pre class="template-code template-preview-code">{{ activeTemplate?.content }}</pre>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </AppShell>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";

import {
  deleteDocument,
  getDocumentChunks,
  getDocuments,
  uploadDocument,
  type DocumentChunkItem,
  type DocumentItem
} from "../../api/document";
import { getKnowledgeBases, type KnowledgeBaseItem } from "../../api/knowledgeBase";
import DocumentChunkCard from "../../components/documents/DocumentChunkCard.vue";
import DocumentListCard from "../../components/documents/DocumentListCard.vue";
import AppShell from "../../layout/AppShell.vue";

const knowledgeBases = ref<KnowledgeBaseItem[]>([]);
const documents = ref<DocumentItem[]>([]);
const selectedKnowledgeBaseId = ref<number | undefined>();
const filterKnowledgeBaseId = ref<number | undefined>();
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const loadingDocuments = ref(false);
const loadingChunks = ref(false);
const drawerVisible = ref(false);
const activeDocument = ref<DocumentItem | null>(null);
const chunkItems = ref<DocumentChunkItem[]>([]);
const templatePreviewVisible = ref(false);
const activeTemplateKey = ref("interview-qa");
const message = ref("");
const errorMessage = ref("");

const templateOptions = [
  {
    key: "interview-qa",
    label: "八股题库模板",
    kicker: "模板示例",
    title: "LangChain 面试资料建议排版",
    badge: "Markdown / PDF 都适用",
    fileName: "langchain-interview-template.md",
    content: `# LangChain 面试高频题
## 1. 什么是 LangChain
- 定义：
- 适用场景：
- 面试回答要点：

## 2. Chain 和 Agent 的区别
- 核心区别：
- 适合举的例子：
- 常见追问：

## 3. 向量数据库如何配合 RAG
- 基本流程：
- 常见组件：
- 容易答错的点：`,
  },
  {
    key: "project-review",
    label: "项目复盘模板",
    kicker: "模板示例",
    title: "项目经历 / 项目复盘建议排版",
    badge: "适合项目面试",
    fileName: "project-review-template.md",
    content: `# 项目名称

## 1. 项目背景
- 业务目标：
- 为什么要做：
- 你的角色：

## 2. 系统设计
- 核心模块：
- 技术选型：
- 数据流转：

## 3. 难点与解决方案
- 难点 1：
- 解决方式：
- 最终效果：

## 4. 可量化结果
- 性能提升：
- 成本优化：
- 业务指标：`,
  },
  {
    key: "tech-notes",
    label: "技术笔记模板",
    kicker: "模板示例",
    title: "技术知识笔记建议排版",
    badge: "适合长期沉淀",
    fileName: "tech-notes-template.md",
    content: `# 主题名称

## 1. 核心概念
- 定义：
- 关键词：
- 与相近概念的区别：

## 2. 示例代码
\`\`\`python
# 在这里放最小可运行示例
\`\`\`

## 3. 常见问题
- 问题 1：
- 问题 2：

## 4. 面试考点
- 高频问题：
- 容易混淆的点：
- 推荐回答结构：`,
  },
];

const activeTemplate = computed(() => {
  return templateOptions.find((item) => item.key === activeTemplateKey.value) ?? templateOptions[0];
});

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
    errorMessage.value = "加载文档失败。";
  } finally {
    loadingDocuments.value = false;
  }
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedFile.value = target.files?.[0] ?? null;
}

async function handleUpload() {
  if (knowledgeBases.value.length === 0) {
    errorMessage.value = "请先创建知识库。";
    return;
  }
  if (!selectedKnowledgeBaseId.value) {
    errorMessage.value = "请选择知识库。";
    return;
  }
  if (!selectedFile.value) {
    errorMessage.value = "请选择要上传的文件。";
    return;
  }

  uploading.value = true;
  errorMessage.value = "";
  message.value = "";
  try {
    const result = await uploadDocument(selectedKnowledgeBaseId.value, selectedFile.value);
    message.value = `上传完成，已创建任务 #${result.task_id}。`;
    selectedFile.value = null;
    drawerVisible.value = false;
    activeDocument.value = null;
    chunkItems.value = [];
    await loadDocuments();
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail ||
      "上传失败，请检查文件类型或后端服务状态。";
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(documentId: number) {
  errorMessage.value = "";
  message.value = "";
  try {
    await deleteDocument(documentId);
    message.value = "文档已删除。";
    if (activeDocument.value?.id === documentId) {
      drawerVisible.value = false;
      activeDocument.value = null;
      chunkItems.value = [];
    }
    await loadDocuments();
  } catch {
    errorMessage.value = "删除失败。";
  }
}

async function openChunkDrawer(document: DocumentItem) {
  activeDocument.value = document;
  drawerVisible.value = true;
  loadingChunks.value = true;
  errorMessage.value = "";
  try {
    chunkItems.value = await getDocumentChunks(document.id);
  } catch {
    chunkItems.value = [];
    errorMessage.value = "加载文档分块失败。";
  } finally {
    loadingChunks.value = false;
  }
}

function formatSize(size: number | null) {
  if (!size) {
    return "未知大小";
  }
  if (size < 1024) {
    return `${size} B`;
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  }
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit"
  });
}

function downloadTemplate() {
  const template = activeTemplate.value;
  const blob = new Blob([template.content], { type: "text/markdown;charset=utf-8" });
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = template.fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  window.URL.revokeObjectURL(url);
}

watch(filterKnowledgeBaseId, () => {
  void loadDocuments();
});

onMounted(async () => {
  try {
    await loadKnowledgeBases();
    await loadDocuments();
  } catch {
    errorMessage.value = "初始化页面数据失败。";
  }
});
</script>

<style scoped>
.documents-layout {
  display: flex;
  gap: 24px;
  align-items: start;
}

.upload-panel {
  flex: 0 0 30%;
  max-width: 420px;
  min-width: 280px;
  align-self: start;
  position: sticky;
  top: 24px;
}

.documents-panel {
  flex: 1 1 70%;
  min-width: 0;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.filter {
  width: 220px;
}

.file-input {
  width: 100%;
  padding: 12px;
  border: 1px dashed var(--border-strong);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.72);
}

.support-note,
.input-note {
  color: var(--text-secondary);
  font-size: 0.92rem;
}

.support-note {
  margin: -2px 0 14px;
}

.input-note {
  margin-top: 12px;
}

.template-entry {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-top: 24px;
  padding-top: 22px;
  border-top: 1px solid rgba(20, 33, 61, 0.08);
}

.template-entry-copy {
  display: grid;
  gap: 12px;
}

.template-entry-copy p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.template-entry-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.template-guide {
  display: grid;
  gap: 18px;
}

.guide-head {
  display: grid;
  gap: 8px;
}

.guide-head h3,
.guide-card h4 {
  margin: 0;
}

.guide-head p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.guide-grid {
  display: grid;
  gap: 14px;
}

.guide-card {
  padding: 16px;
  border-radius: 16px;
  background: rgba(243, 247, 251, 0.82);
  border: 1px solid rgba(20, 33, 61, 0.08);
}

.guide-card.warning {
  background: rgba(255, 244, 232, 0.9);
  border-color: rgba(217, 119, 6, 0.16);
}

.guide-list {
  margin: 12px 0 0;
  padding-left: 18px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.guide-list li + li {
  margin-top: 8px;
}

.template-code {
  margin: 0;
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(20, 33, 61, 0.08);
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.7;
  color: var(--text-main);
  font-family: "Consolas", "SFMono-Regular", monospace;
  font-size: 0.92rem;
}

.template-preview-sheet {
  display: grid;
  gap: 18px;
  padding: 22px;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 249, 252, 0.96));
  border: 1px solid rgba(20, 33, 61, 0.08);
  box-shadow: var(--shadow-sm);
}

.template-tabs :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.template-tabs :deep(.el-tabs__nav-wrap::after) {
  background-color: rgba(20, 33, 61, 0.08);
}

.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(20, 33, 61, 0.08);
}

.sheet-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.sheet-kicker {
  display: inline-block;
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 0.82rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.sheet-header h4 {
  margin: 0;
  font-size: 1.25rem;
}

.sheet-body {
  display: grid;
  gap: 18px;
}

.template-preview-code {
  font-size: 0.95rem;
  min-height: 420px;
}

.drawer-body {
  display: grid;
  gap: 18px;
}

.drawer-header h3 {
  margin: 0 0 6px;
  font-size: 1.1rem;
}

.drawer-header p {
  margin: 0;
  color: var(--text-secondary);
}

.chunk-list {
  display: grid;
  gap: 14px;
}

@media (max-width: 860px) {
  .documents-layout {
    flex-direction: column;
  }

  .upload-panel {
    flex: none;
    max-width: none;
    width: 100%;
    position: static;
  }

  .documents-panel {
    width: 100%;
  }

  .template-entry,
  .sheet-header {
    flex-direction: column;
    align-items: stretch;
  }
}

@media (max-width: 960px) {
  .toolbar {
    flex-direction: column;
  }

  .toolbar-actions {
    width: 100%;
  }

  .filter {
    width: 100%;
  }
}
</style>
