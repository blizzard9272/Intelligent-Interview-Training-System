# 项目结构设计

## 1. 推荐仓库结构

```text
ai_project/
  README.md
  docs/
    PRD.md
    TECHNICAL_DESIGN.md
    PROJECT_STRUCTURE.md
    DATABASE_SCHEMA.md
    API_SPEC.md
    DEVELOPMENT_PLAN.md
  backend/
    app/
      api/
        v1/
      core/
      db/
        models/
      rag/
        loaders/
        splitters/
        embeddings/
        retrievers/
        prompts/
        generators/
      schemas/
      services/
      tasks/
      main.py
    alembic/
    requirements.txt
    .env.example
  frontend/
    src/
      api/
      components/
      layout/
      router/
      stores/
      styles/
      views/
        auth/
        dashboard/
        knowledge-base/
        documents/
        qa/
        history/
      App.vue
      main.ts
    index.html
    package.json
    tsconfig.json
    vite.config.ts
  storage/
    uploads/
```

## 2. 后端分层职责

## 2.1 `api/`

负责：

- 定义 HTTP 接口
- 参数接收
- 响应返回
- 依赖注入

## 2.2 `core/`

负责：

- 配置管理
- 安全认证
- 日志
- 全局异常处理

## 2.3 `db/`

负责：

- 数据库连接
- ORM 模型
- Base 定义

## 2.4 `schemas/`

负责：

- 请求体模型
- 响应体模型
- 序列化输出

## 2.5 `services/`

负责：

- 业务逻辑
- 调用数据库、任务、RAG 能力
- 组织跨模块流程

## 2.6 `rag/`

负责：

- 文档加载
- 文本切分
- Embedding 调用
- 向量检索
- Prompt 构造
- 回答生成

## 2.7 `tasks/`

负责：

- 文档入库任务
- 后续抽题任务

## 3. 前端分层职责

## 3.1 `api/`

负责：

- Axios 封装
- 各模块接口请求

## 3.2 `components/`

负责：

- 通用 UI 组件
- 文件上传卡片
- 任务状态标签
- 聊天气泡
- 引用来源展示组件

## 3.3 `stores/`

负责：

- 用户登录状态
- 当前知识库
- 问答会话
- 文档任务状态

## 3.4 `views/`

负责：

- 路由页面
- 业务页面组合

## 4. 存储结构说明

## 4.1 `storage/uploads/`

一期本地开发阶段用于保存上传的原始文件。后续如果切换到对象存储，优先只替换文件存储层实现，不改上层业务接口。

## 5. 建议开发顺序

建议按以下顺序开发：

1. `backend/app/core`
2. `backend/app/db`
3. `backend/app/schemas`
4. `backend/app/api/v1/auth.py`
5. `backend/app/api/v1/knowledge_bases.py`
6. `backend/app/api/v1/documents.py`
7. `backend/app/tasks/ingestion_tasks.py`
8. `backend/app/rag`
9. `backend/app/api/v1/qa.py`
10. `frontend/src/router`
11. `frontend/src/views`

## 6. 二期预留位置

提前预留如下文件或目录：

- `backend/app/services/interview_service.py`
- `backend/app/tasks/question_generation_tasks.py`
- `frontend/src/views/interview/`

这样可以保证一期完成后继续演进时，不需要大幅重构目录结构。
