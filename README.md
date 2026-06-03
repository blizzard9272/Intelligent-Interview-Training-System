# Interview Agent

`Interview Agent` 是一个面向求职者的智能面试训练系统。用户可以持续上传八股文资料、面试复盘、学习笔记和外部技术文档，系统基于 RAG 构建个人知识库，并在后续支持模拟面试、回答评分、追问和总结报告。

当前仓库已经包含：

- 中文化且可直接开发的产品与技术文档
- 第一版前后端项目骨架
- 后端基础配置、数据库模型、认证结构与接口占位
- 前端 Vue3 + Vite 基础页面与路由骨架

## 一期目标

一期聚焦可落地的核心闭环：

- 用户注册与登录
- 知识库分类管理
- `txt` / `md` / `pdf` 文档上传
- 异步文档入库任务
- RAG 问答
- 引用来源展示
- 问答历史

二期扩展方向：

- 自动抽题
- 模拟面试
- 回答评分
- 追问
- 总结报告
- LangGraph + ReAct Agent 工作流

## 文档入口

- [docs/PRD.md](docs/PRD.md)
- [docs/TECHNICAL_DESIGN.md](docs/TECHNICAL_DESIGN.md)
- [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- [docs/API_SPEC.md](docs/API_SPEC.md)
- [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

## 项目结构

```text
ai_project/
  docs/
  backend/
  frontend/
  storage/
```

## 推荐技术栈

- 前端：Vue 3、Vite、TypeScript、Pinia、Vue Router、Element Plus
- 后端：FastAPI、Pydantic、SQLAlchemy 2.x、Alembic
- 数据库：PostgreSQL
- 向量库：Chroma
- 异步任务：Celery + Redis
- LLM 编排：LangChain
- 二期工作流：LangGraph

## 当前开发顺序

建议按以下顺序继续推进：

1. 完善后端配置与数据库迁移
2. 实现认证、知识库、文档上传接口
3. 接入文档解析、切分、Embedding 与 Chroma
4. 实现 RAG 检索与问答接口
5. 完成前端页面联调

## 说明

当前版本以“能尽快进入开发”为目标，优先保证：

- 目录结构清晰
- 分层职责明确
- 二期可扩展
- 一期两周内可交付

## 本地启动建议

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

说明：

- 当前后端默认不自动建表，推荐使用 Alembic 迁移
- 如需临时自动建表，可在 `.env` 中将 `DB_AUTO_CREATE=true`
- 问答、抽题和入库任务目前还是骨架实现，下一步会逐步替换为真实 RAG 能力
