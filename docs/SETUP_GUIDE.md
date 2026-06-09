# 环境搭建指南

本指南用于帮助你基于当前仓库启动前后端开发环境，并完成 PostgreSQL / PGVector 相关准备。

## 1. 前置条件

- Python 3.11+
- Node.js 18+
- PostgreSQL
- 已安装 `pgvector` 扩展

## 2. 后端启动

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

执行数据库迁移：

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

启动后端：

```powershell
uvicorn app.main:app --reload
```

## 3. 前端启动

```powershell
cd frontend
npm install
npm run dev
```

## 4. PGVector 验证

确认数据库已安装扩展：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extname FROM pg_extension WHERE extname = 'vector';
```

确认 `document_chunks` 表存在并可写入。

## 5. 当前项目状态

当前仓库已经不是单纯的骨架状态，而是具备可运行的 RAG 主链路：

- 文档上传与异步入库
- 文本清洗与 chunk 构建
- PGVector 向量写入
- 检索、重排、回答生成
- 引用返回与 debug trace

## 6. 初次验证建议

推荐按以下顺序验证：

1. 创建用户与知识库
2. 上传一篇 Markdown 文档
3. 等待入库完成
4. 查看文档 chunk
5. 发起一次问答
6. 检查引用与 debug trace 是否正常返回
