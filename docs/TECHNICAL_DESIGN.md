# 技术设计

## 1. 设计目标

当前系统的技术设计同时服务于两条主线：

- 面向用户资料的可追溯 RAG 问答
- 面向求职训练场景的题库、面试与训练分析闭环

设计上需要满足：

- 多用户、知识库隔离与权限控制
- 文档异步入库与稳定向量检索
- 可解释问答与引用溯源
- 为后续 RAG 质量工程化保留扩展空间

## 2. 当前技术栈

### 2.1 前端

- Vue 3
- Vite
- TypeScript
- Vue Router
- Element Plus

### 2.2 后端

- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic

### 2.3 基础设施

- PostgreSQL
- PGVector
- FastAPI BackgroundTasks

当前生成与 embedding 策略仍采用“在线能力优先，必要时本地 fallback”的思路，以保证开发环境和演示环境都能运行。

## 3. 模块分层

- `api`：HTTP 接口层
- `schemas`：请求与响应模型
- `db/models`：数据库模型
- `services`：核心业务逻辑
- `rag`：检索、切分、向量、生成相关逻辑
- `tasks`：异步任务
- `core`：配置、异常、日志、安全

## 4. 当前已落地的技术方案

### 4.1 文档入库

主流程：

1. 用户上传文档
2. 创建文档记录与入库任务
3. 异步解析文档
4. 清洗文本并按 section 构建 chunk
5. 生成 embedding
6. 写入 PostgreSQL `document_chunks` 表
7. 更新任务与文档状态

当前特点：

- 支持 `txt / md / pdf`
- Markdown 保留标题结构，并保留首个标题前的引言内容
- 为每个 chunk 写入 metadata，支持后续过滤与调试

### 4.2 RAG 问答

主流程：

1. 接收问题
2. 校验用户与知识库权限
3. 生成 query embedding
4. 按 query intent 执行多步检索计划
5. 对候选结果做轻量级 rerank
6. 构建结构化上下文
7. 生成答案并返回引用
8. 保存问答历史与 debug trace

当前回答策略：

- 优先依据检索到的知识库证据回答
- 返回引用片段、检索步骤、重排结果和结构化上下文
- 在无证据时支持受控 fallback，并显式提醒用户上传相关资料

### 4.3 当前 RAG 质量优化点

当前已经落地的优化包括：

- 基于 `document_kind` 与 `content_type_hint` 的 metadata 增强
- 基于问题意图的检索路由
- 启发式 rerank
- 针对定义类问题的定义型 chunk 优先级提升
- 引用片段按句子边界截断优化
- debug trace 与回归测试支持

### 4.4 当前限制

当前仍然存在以下工程化不足：

- chunk 仍以规则切分为主，尚未做到更强语义切分
- 仍未实现真正的 hybrid retrieval
- rerank 仍为规则打分，尚未引入模型级 reranker
- 评估集与离线评估还需要继续扩大

## 5. 测试设计现状

当前已覆盖的测试重点包括：

- 文档类型与 chunk 内容类型识别
- Markdown 前言保留
- 检索路由与重排
- local generator 与 fallback 行为
- PGVector 存储基础能力
- 面试服务核心流程

## 6. 后续技术演进建议

### 6.1 最优先：RAG 质量工程化

建议下一阶段重点投入：

- chunk 策略试验
- metadata 增强与过滤
- rerank / hybrid retrieval
- 检索日志
- 离线评估集

### 6.2 训练系统继续演进

- 弱点类别规范化
- 长期训练画像
- 更细粒度的 drill 生成逻辑
- 分析可视化增强

### 6.3 Agent / LangGraph 化保留方向

如果未来继续进入 Agent 或 LangGraph 编排，可将当前服务层逻辑拆成：

1. `select_question`
2. `retrieve_context`
3. `generate_answer`
4. `score_answer`
5. `decide_followup`
6. `generate_summary`
