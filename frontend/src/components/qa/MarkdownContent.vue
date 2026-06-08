<template>
  <div class="markdown-body" v-html="renderedHtml"></div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  content: string;
}>();

const renderedHtml = computed(() => renderMarkdown(props.content));

function renderMarkdown(source: string) {
  const escaped = escapeHtml(source || "");
  const blocks = escaped.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let inCodeBlock = false;
  let codeBuffer: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let paragraphBuffer: string[] = [];

  const flushParagraph = () => {
    if (paragraphBuffer.length === 0) {
      return;
    }
    html += `<p>${formatInline(paragraphBuffer.join("<br />"))}</p>`;
    paragraphBuffer = [];
  };

  const closeList = () => {
    if (listType) {
      html += `</${listType}>`;
      listType = null;
    }
  };

  const flushCodeBlock = () => {
    if (!inCodeBlock) {
      return;
    }
    html += `<pre><code>${codeBuffer.join("\n")}</code></pre>`;
    inCodeBlock = false;
    codeBuffer = [];
  };

  for (const line of blocks) {
    if (line.trim().startsWith("```")) {
      flushParagraph();
      closeList();
      if (inCodeBlock) {
        flushCodeBlock();
      } else {
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeList();
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = Math.min(heading[1].length, 6);
      html += `<h${level}>${formatInline(heading[2])}</h${level}>`;
      continue;
    }

    const unordered = line.match(/^\s*[-+*]\s+(.*)$/);
    if (unordered) {
      flushParagraph();
      if (listType !== "ul") {
        closeList();
        listType = "ul";
        html += "<ul>";
      }
      html += `<li>${formatInline(unordered[1])}</li>`;
      continue;
    }

    const ordered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (ordered) {
      flushParagraph();
      if (listType !== "ol") {
        closeList();
        listType = "ol";
        html += "<ol>";
      }
      html += `<li>${formatInline(ordered[1])}</li>`;
      continue;
    }

    closeList();
    paragraphBuffer.push(line);
  }

  flushParagraph();
  closeList();
  flushCodeBlock();
  return html;
}

function formatInline(value: string) {
  return value
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

function escapeHtml(value: string) {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}
</script>

<style scoped>
.markdown-body {
  line-height: 1.75;
  color: var(--text-primary);
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4) {
  margin: 0 0 12px;
  line-height: 1.35;
}

.markdown-body :deep(p) {
  margin: 0 0 14px;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 0 0 14px;
  padding-left: 22px;
}

.markdown-body :deep(li) {
  margin-bottom: 6px;
}

.markdown-body :deep(code) {
  font-family: "Consolas", "Courier New", monospace;
  font-size: 0.92em;
  background: rgba(20, 33, 61, 0.08);
  padding: 2px 6px;
  border-radius: 6px;
}

.markdown-body :deep(pre) {
  margin: 0 0 14px;
  padding: 14px;
  border-radius: 12px;
  background: rgba(15, 23, 42, 0.92);
  color: #f8fafc;
  overflow-x: auto;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  color: inherit;
}
</style>
