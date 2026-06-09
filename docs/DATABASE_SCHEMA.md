# 数据库结构说明

## 1. 业务表

当前核心业务表包括：

- `users`
- `knowledge_bases`
- `documents`
- `ingestion_tasks`
- `qa_sessions`
- `qa_messages`
- `question_bank`
- `interview_sessions`
- `interview_turns`

其中：

- `documents` 记录用户上传文档及入库状态
- `ingestion_tasks` 记录异步入库进度
- `qa_sessions / qa_messages` 记录问答历史与引用调试信息

## 2. 向量表

当前向量 chunk 已迁移到 PostgreSQL 内部，通过 `PGVector` 存储。

核心表：

- `document_chunks`

建议字段如下：

- `id`
- `user_id`
- `knowledge_base_id`
- `document_id`
- `chunk_index`
- `content`
- `embedding`
- `file_name`
- `file_type`
- `document_kind`
- `section_title`
- `page_no`
- `section_index`
- `content_type_hint`
- `starts_with_question`
- `created_at`
- `updated_at`

## 3. 元数据设计

`document_chunks` 中的 metadata 主要用于：

- 检索范围隔离
- 检索路由
- rerank
- debug trace 展示

当前已使用的关键 metadata：

- `user_id`
- `knowledge_base_id`
- `document_id`
- `chunk_index`
- `file_name`
- `file_type`
- `document_kind`
- `section_title`
- `page_no`
- `section_index`
- `content_type_hint`
- `starts_with_question`

## 4. 约束与索引建议

- 向量检索至少按 `user_id + knowledge_base_id` 做范围限制
- `document_id + chunk_index` 应保持唯一
- `document_id`、`knowledge_base_id`、`user_id` 应有普通索引
- `embedding` 应建立 PGVector 对应的向量索引

## 5. 当前状态说明

当前项目已经从“业务表在 PostgreSQL、向量在 Chroma”迁移到：

- 业务数据：PostgreSQL
- 向量数据：PostgreSQL + PGVector

这样做的好处包括：

- 统一存储
- 更方便做联表与过滤
- 更利于工程化部署与备份
