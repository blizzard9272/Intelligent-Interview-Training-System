# Interview Agent

`Interview Agent` 是一个面向求职训练场景的智能面试知识库与训练系统。用户可以上传自己的面试资料、技术笔记、八股文、项目复盘与外部参考文档，系统基于 RAG 构建私有知识库，并在此基础上提供问答、引用溯源、题库生成、模拟面试与训练分析能力。

## 项目亮点

- 基于 `PostgreSQL + PGVector` 构建向量检索能力，统一业务数据与向量数据存储
- 支持 `txt / md / pdf` 文档上传、异步入库、文本清洗、分块与向量化
- 支持基于问题意图的检索路由、轻量级 rerank 与可解释问答
- 支持引用片段、检索步骤、重排结果、结构化上下文与 debug trace 返回
- 面向面试训练场景，已形成“知识库问答 + 题库生成 + 模拟面试 + 训练分析”的产品雏形

## 当前已实现能力

### 1. 知识库与文档管理

- 用户、知识库、文档、任务、问答、题库、面试训练的基础数据模型与接口
- 文档上传与异步入库任务
- 支持查看文档状态、入库状态与文档 chunk
- 删除文档时同步删除对应向量数据

### 2. RAG 入库链路

- `md` 文档按标题分节，并保留首个标题前的引言内容
- `pdf` 文档按页抽取文本
- `txt` 文档整体读取
- 文本统一做清洗与规范化处理
- 生成 embedding 后写入 `document_chunks` 向量表

### 3. RAG 检索与问答

- 基于知识库范围进行检索，支持用户隔离与知识库隔离
- 支持问题意图识别：概念题、设计题、实现题、问答题
- 支持 metadata 增强检索，利用 `document_kind`、`content_type_hint`、`section_title` 等字段做检索控制
- 支持多步候选召回与启发式 rerank
- 针对“什么是 / 定义类”问题增加定义型 chunk 优先级提升
- 在无证据场景下支持受控 fallback，并提醒用户上传相关资料

### 4. 可解释性与调试能力

- 返回引用片段
- 返回检索步骤与候选结果
- 返回重排结果
- 返回结构化上下文 `structured_context`
- 保存问答历史与 debug trace，便于持续定位文档切分、标注和召回质量问题

## 当前 RAG 技术实现

项目当前围绕 RAG 主链路实现了以下能力：

1. 文档解析与切分
   - 按文档结构切 section，而不是直接把全文粗暴拼接
   - 为 Markdown 文档保留定义型引言内容，避免首段知识丢失
   - 支持后续围绕 chunk 策略继续优化

2. 元数据增强
   - 为每个 chunk 写入：
     - `document_kind`
     - `content_type_hint`
     - `section_title`
     - `page_no`
     - `section_index`
     - `starts_with_question`
   - 支撑后续 query routing、rerank 与 debug trace

3. 检索与重排
   - 基于 query intent 做检索路由
   - 先做多步候选召回，再做轻量级 rerank
   - 让定义型问题优先命中定义型 chunk，而不是被示例段或补充段抢占

4. 回答生成与展示
   - 优先依据检索证据生成回答
   - 支持无证据时的受控 fallback
   - 优化引用片段展示，尽量按句子边界截断，减少半句话被截断的问题

## 技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus
- 后端：FastAPI、Pydantic、SQLAlchemy 2.x、Alembic
- 数据库：PostgreSQL
- 向量存储：PGVector
- 异步任务：FastAPI BackgroundTasks
- 模型接入：Qwen / 本地 fallback

## 项目结构

```text
ai_project/
  docs/
  backend/
  frontend/
  storage/
```

## 文档入口

- [docs/PRD.md](docs/PRD.md)
- [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md)
- [docs/PROJECT_CONTEXT.md](docs/PROJECT_CONTEXT.md)
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- [docs/API_SPEC.md](docs/API_SPEC.md)
- [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)
- [docs/PGVECTOR_MIGRATION_AND_RAG_NEXT_STEPS.md](docs/PGVECTOR_MIGRATION_AND_RAG_NEXT_STEPS.md)

## 本地启动

### 后端

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

## 数据库迁移

推荐始终使用 Alembic：

```bash
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

如果你使用 PGVector，请先确认 PostgreSQL 已安装 `vector` 扩展，并且迁移已成功创建 `document_chunks` 表。

## 当前优化重点

项目当前已经从“RAG MVP”进入“RAG 质量优化”阶段，后续重点包括：

- chunk 策略试验
- metadata 增强与更细粒度过滤
- rerank / hybrid retrieval
- 检索调试与评估闭环
- 引用片段展示与 fallback 体验优化
