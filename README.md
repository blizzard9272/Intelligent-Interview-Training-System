# Interview Agent

`Interview Agent` 是一个面向求职训练场景的智能面试知识库与训练系统。用户可以上传自己的面试资料、技术笔记、八股文、项目复盘与外部参考文档，系统基于 RAG 构建私有知识库，并在此基础上提供问答、引用溯源、题库生成、模拟面试与训练分析能力。

## 当前能力

当前仓库已经具备一条可运行的后端主链路：

- 用户、知识库、文档、任务、问答、题库、面试训练的基础数据模型与接口
- `txt / md / pdf` 文档上传与异步入库
- Markdown / PDF / Text 文档解析与文本清洗
- 文档分块、Embedding 生成、PGVector 向量存储
- 基于知识库的 RAG 问答
- 引用片段、检索步骤、重排结果与结构化上下文返回
- 问答历史与会话管理
- 题库生成与面试训练闭环

## 当前 RAG 实现

项目当前采用 `PostgreSQL + PGVector` 作为向量存储方案，并围绕 RAG 主链路实现了以下能力：

1. 文档解析与切分
   - `md` 按标题分节，并保留首个标题前的引言内容
   - `pdf` 按页抽取文本
   - `txt` 直接整体读取
   - 文本统一做清洗与规范化处理

2. 元数据增强
   - 为 chunk 增加 `document_kind`、`content_type_hint`、`section_title`、`page_no`、`section_index`、`starts_with_question` 等元数据
   - 支持按文档类型与内容类型做检索过滤

3. 检索与重排
   - 支持基于问题意图的检索路由，如概念题、设计题、实现题、问答题
   - 支持多步候选召回与轻量级 rerank
   - 对“什么是 / 定义类”问题增加定义型 chunk 优先级提升

4. 可解释问答
   - 返回引用片段
   - 返回检索步骤与候选信息
   - 返回重排结果
   - 返回结构化上下文 `structured_context`
   - 支持无证据场景下的受控 fallback

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

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 数据库迁移

推荐始终使用 Alembic：

```bash
cd backend
.venv\Scripts\python.exe -m alembic upgrade head
```

如果你使用 PGVector，请先确认 PostgreSQL 已安装 `vector` 扩展，并且迁移已成功创建 `document_chunks` 表。

## 当前优化重点

项目当前已经从“RAG MVP”进入“RAG 质量优化”阶段，后续重点包括：

- chunk 策略试验
- metadata 增强与更细粒度过滤
- rerank / hybrid retrieval
- 检索调试与评估闭环
- 引用片段展示与 fallback 体验优化
