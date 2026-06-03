# 数据库设计文档

## 1. 数据库选型

一期推荐数据库：

- PostgreSQL

原因：

- 关系建模能力成熟
- 适合用户、知识库、文档、任务、问答历史等业务
- 比 SQLite 更适合多用户场景
- 与 FastAPI、SQLAlchemy、Alembic 配合成熟

## 2. 核心表设计

## 2.1 `users`

用途：

- 存储用户账号信息

建议字段：

```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 2.2 `knowledge_bases`

用途：

- 存储用户的知识库分类

建议字段：

```sql
CREATE TABLE knowledge_bases (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    job_role VARCHAR(100),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

建议索引：

```sql
CREATE INDEX idx_knowledge_bases_user_id ON knowledge_bases(user_id);
```

## 2.3 `documents`

用途：

- 存储上传文档及其处理状态

建议字段：

```sql
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    knowledge_base_id BIGINT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(20) NOT NULL,
    file_path TEXT NOT NULL,
    file_size BIGINT,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    parse_error TEXT,
    chunk_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

建议索引：

```sql
CREATE INDEX idx_documents_user_kb ON documents(user_id, knowledge_base_id);
```

## 2.4 `ingestion_tasks`

用途：

- 跟踪文档入库任务状态

建议字段：

```sql
CREATE TABLE ingestion_tasks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(30) NOT NULL DEFAULT 'queued',
    progress INT NOT NULL DEFAULT 0,
    message TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

建议索引：

```sql
CREATE INDEX idx_ingestion_tasks_document_id ON ingestion_tasks(document_id);
```

## 2.5 `qa_sessions`

用途：

- 存储一次问答会话

建议字段：

```sql
CREATE TABLE qa_sessions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    knowledge_base_id BIGINT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 2.6 `qa_messages`

用途：

- 存储问答消息内容

建议字段：

```sql
CREATE TABLE qa_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES qa_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    references_json JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

建议索引：

```sql
CREATE INDEX idx_qa_messages_session_id ON qa_messages(session_id);
```

## 2.7 `question_bank`

用途：

- 存储用户整理或系统自动抽取的面试题与参考答案
- 一期可选实现，二期模拟面试核心依赖表

建议字段：

```sql
CREATE TABLE question_bank (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    knowledge_base_id BIGINT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    source_document_id BIGINT REFERENCES documents(id) ON DELETE SET NULL,
    question TEXT NOT NULL,
    reference_answer TEXT,
    tags JSONB,
    difficulty VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## 3. 向量数据设计

一期建议：

- 向量 Chunk 存储在 Chroma
- 文档主数据存储在 PostgreSQL

每个 Chunk 在 Chroma 中建议存储如下元数据：

- `user_id`
- `knowledge_base_id`
- `document_id`
- `file_name`
- `file_type`
- `chunk_index`
- `section_title`
- `page_no`

## 4. 状态枚举建议

## 4.1 文档状态

- `pending`
- `processing`
- `completed`
- `failed`

## 4.2 入库任务状态

- `queued`
- `running`
- `completed`
- `failed`

## 5. 数据隔离规则

所有涉及业务数据的查询必须强制加上用户隔离：

- SQL 查询按 `user_id` 限制
- 向量检索按 `user_id + knowledge_base_id` 限制

这是多用户场景下的基础安全要求。

## 6. ER 关系说明

核心关系如下：

- 一个 `user` 可以拥有多个 `knowledge_base`
- 一个 `knowledge_base` 可以拥有多个 `document`
- 一个 `document` 对应多个 `ingestion_task` 记录，通常至少有一个
- 一个 `user` 可以拥有多个 `qa_session`
- 一个 `qa_session` 对应多个 `qa_message`
- 一个 `knowledge_base` 可以拥有多个 `question_bank` 题目

## 7. 二期扩展表

后续建议增加：

- `interview_sessions`
- `interview_questions`
- `interview_answers`
- `interview_followups`
- `interview_reports`
- `user_model_settings`
