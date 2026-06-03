# 本地开发启动指南

## 1. 启动目标

本指南用于帮助你基于当前仓库骨架，尽快启动第一版前后端开发环境。

## 2. 后端启动

进入目录：

```bash
cd backend
```

创建虚拟环境：

```bash
python -m venv .venv
```

激活虚拟环境：

```bash
.venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量：

```bash
copy .env.example .env
```

修改 `.env` 中的数据库连接：

```env
DATABASE_URL=postgresql+psycopg://postgres:你的数据库密码@localhost:5432/interview_agent
DB_AUTO_CREATE=false
```

执行数据库迁移：

```bash
alembic upgrade head
```

启动服务：

```bash
uvicorn app.main:app --reload
```

访问：

- 接口文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

## 3. 前端启动

进入目录：

```bash
cd frontend
```

安装依赖：

```bash
npm install
```

启动开发服务：

```bash
npm run dev
```

默认访问地址：

- `http://localhost:5173`

## 4. 当前骨架状态说明

已完成：

- 中文化产品与技术文档
- FastAPI 项目骨架
- 用户、知识库、文档、任务、问答、题库接口骨架
- Vue3 页面骨架

未完成：

- 真实 Celery 文档入库任务执行
- 真实 Chroma 向量写入
- 真实 LLM 问答
- 自动抽题

## 5. 推荐下一步开发顺序

1. 先把认证接口跑通
2. 再完成知识库 CRUD
3. 再把文档上传和任务状态串起来
4. 最后接入 RAG
