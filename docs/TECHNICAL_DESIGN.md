# 技术设计文档

## 1. 设计目标

本系统的一期技术方案需要同时满足以下要求：

- 支持多用户使用
- 支持知识库分类和用户隔离
- 支持异步文档入库
- 支持稳定、可解释的 RAG 问答
- 为二期 LangGraph + ReAct Agent 留好扩展能力
- 在两周时间内可落地交付

## 2. 总体架构

## 2.1 架构原则

- 后端先保持单体服务，不做微服务拆分
- 文档入库与问答查询分层组织
- 关系型数据与向量数据分开管理
- 所有模型调用通过统一 Provider 层封装
- 一期聚焦上传、建库、检索、问答主链路

## 2.2 技术栈

前端：

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus

后端：

- FastAPI
- Pydantic
- SQLAlchemy 2.x
- Alembic

基础设施：

- PostgreSQL
- Chroma
- Redis
- Celery

LLM 编排：

- LangChain

二期工作流：

- LangGraph

## 2.3 为什么一期只用 FastAPI

一期不引入 Django 或 Spring Boot，原因如下：

- FastAPI 足以承载用户、知识库、文档、任务和问答接口
- 引入多个后端框架会造成职责重复
- 两周周期内，单服务架构更适合快速落地
- 当前系统复杂度还不需要 Spring Cloud 级别的分布式治理

结论：

一期采用 `FastAPI + PostgreSQL + Chroma + Redis/Celery` 即可。

## 3. 系统模块设计

## 3.1 前端模块

页面模块建议如下：

- 登录页
- 注册页
- 控制台首页
- 知识库管理页
- 文档上传页
- 文档列表页
- 智能问答页
- 问答历史页

状态管理建议：

- `authStore`
- `kbStore`
- `qaStore`
- `taskStore`

当前状态：

- 主要页面已具备真实接口接入能力
- `documents`、`qa`、`history` 页已完成一轮中文文案与布局清理
- 下一步适合把会话列表、消息卡片、引用卡片抽成 `components`

## 3.2 后端模块

后端建议分层如下：

- `api`：HTTP 接口层
- `schemas`：请求和响应模型
- `models`：数据库模型
- `services`：业务逻辑
- `rag`：解析、切分、检索、Prompt、生成
- `tasks`：异步任务
- `core`：配置、安全、日志、异常

## 4. 文档入库设计

## 4.1 入库流程

标准流程如下：

1. 用户上传文件
2. 后端保存文件
3. 写入 `documents` 表
4. 创建 `ingestion_tasks` 任务
5. 异步执行解析
6. 文本清洗
7. 结构化切分
8. 调用 Embedding 模型
9. 写入 Chroma
10. 更新文档状态和任务状态

## 4.2 文档解析方案

不同文件类型解析策略：

- `txt`：直接读取文本
- `md`：尽量保留标题结构
- `pdf`：使用 `PyMuPDF` 或 `pdfplumber`

## 4.3 文本清洗

清洗目标：

- 去除明显无意义空白字符
- 规范换行
- 清理异常段落或无效噪声
- 保留尽可能多的结构信息

## 4.4 切分策略

一期建议：

- `txt`：递归字符切分
- `md`：优先按标题切分，再递归切分
- `pdf`：按页提取，再递归切分

参数建议：

- `chunk_size = 700`
- `chunk_overlap = 100`

这两个参数建议写入配置，便于后续调优。

## 4.5 Chunk 元数据

每个 Chunk 至少写入以下元数据：

- `user_id`
- `knowledge_base_id`
- `document_id`
- `file_name`
- `file_type`
- `chunk_index`
- `section_title`
- `page_no`

这些元数据对于用户隔离、引用展示和问题定位非常重要。

## 5. RAG 检索设计

## 5.1 一期检索流程

1. 接收用户问题
2. 选择知识库范围
3. 在 Chroma 中按 `user_id + knowledge_base_id` 过滤
4. 召回 TopK 相关 Chunk
5. 组装上下文
6. 调用聊天模型生成回答
7. 返回答案和引用片段

## 5.2 一期生成策略

Prompt 要求模型：

- 优先依据检索内容回答
- 如果上下文不足，明确指出依据不足
- 可以适当结合模型常识补充，但要标识为补充说明
- 返回引用来源编号

## 5.3 后续增强路线

二次优化可以逐步加入：

- Query Rewrite
- 混合检索
- Rerank
- 上下文压缩
- 回答置信度提示

## 6. 模型抽象设计

## 6.1 支持模型

聊天模型：

- 通义千问
- DeepSeek

Embedding 模型：

- 通义千问 `text-embedding-v4`

## 6.2 Provider 设计

建议抽象两个接口：

- `ChatProvider`
- `EmbeddingProvider`

业务逻辑层只依赖抽象，不直接绑定某一个厂商 SDK。

## 7. 异步任务设计

## 7.1 为什么异步

上传文档后，解析、切分、Embedding 和写入向量库可能耗时较长。如果同步处理，会影响用户体验，也不利于后续扩展。

## 7.2 任务状态字段

任务至少需要：

- `status`
- `progress`
- `message`
- `started_at`
- `finished_at`

## 7.3 实现方案

推荐：

- `Celery + Redis`

如果时间不够，短期降级方案：

- `FastAPI BackgroundTasks + ingestion_tasks` 表

## 8. 安全与隔离

- 所有受保护接口必须校验 JWT
- 所有数据库查询必须带 `user_id`
- 所有向量检索必须带 `user_id` 和 `knowledge_base_id` 过滤
- 上传文件必须校验格式和大小

## 9. 可观测性

一期建议实现：

- 结构化日志
- 任务状态日志
- 关键异常日志
- 可选请求 ID

## 10. 二期面试 Agent 扩展设计

二期采用 LangGraph 搭建面试状态流，建议节点如下：

1. `select_question`
2. `ask_question`
3. `receive_answer`
4. `retrieve_reference`
5. `score_answer`
6. `decide_followup`
7. `ask_followup`
8. `generate_summary`

ReAct Agent 适合用于：

- 调题库
- 补充检索
- 决策是否追问
- 生成本轮总结

## 11. 一期不做的内容

- 微服务
- 复杂权限体系
- 语音对话
- 完整 RAG 评测平台
- 运维级多租户治理
