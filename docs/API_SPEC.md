# 接口设计文档

## 1. 接口规范

- 接口风格：RESTful
- 数据格式：JSON
- 鉴权方式：JWT Bearer Token
- 基础前缀：`/api/v1`

统一响应建议：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

统一错误响应建议：

```json
{
  "code": 4001,
  "message": "参数校验失败",
  "data": null
}
```

## 2. 鉴权模块

## 2.1 注册

接口：

`POST /api/v1/auth/register`

请求体：

```json
{
  "username": "alice",
  "email": "alice@example.com",
  "password": "StrongPassword123"
}
```

响应体：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

## 2.2 登录

接口：

`POST /api/v1/auth/login`

请求体：

```json
{
  "email": "alice@example.com",
  "password": "StrongPassword123"
}
```

响应体：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt-token",
    "token_type": "bearer"
  }
}
```

## 2.3 获取当前用户

接口：

`GET /api/v1/auth/me`

响应体：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "username": "alice",
    "email": "alice@example.com"
  }
}
```

## 3. 知识库模块

## 3.1 获取知识库列表

接口：

`GET /api/v1/knowledge-bases`

## 3.2 创建知识库

接口：

`POST /api/v1/knowledge-bases`

请求体：

```json
{
  "name": "AI Agent",
  "description": "智能体面试资料",
  "job_role": "AI Agent 工程师"
}
```

## 3.3 更新知识库

接口：

`PUT /api/v1/knowledge-bases/{id}`

## 3.4 删除知识库

接口：

`DELETE /api/v1/knowledge-bases/{id}`

## 4. 文档模块

## 4.1 上传文档

接口：

`POST /api/v1/documents/upload`

请求类型：

- `multipart/form-data`

表单字段：

- `knowledge_base_id`
- `file`

响应体：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "document_id": 10,
    "task_id": 55,
    "status": "queued"
  }
}
```

## 4.2 获取文档列表

接口：

`GET /api/v1/documents`

查询参数：

- `knowledge_base_id`，可选
- `status`，可选

## 4.3 获取文档详情

接口：

`GET /api/v1/documents/{id}`

## 4.4 删除文档

接口：

`DELETE /api/v1/documents/{id}`

## 5. 任务模块

## 5.1 获取任务列表

接口：

`GET /api/v1/tasks`

## 5.2 获取任务详情

接口：

`GET /api/v1/tasks/{id}`

响应示例：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 55,
    "document_id": 10,
    "status": "running",
    "progress": 60,
    "message": "正在生成向量"
  }
}
```

## 6. 问答模块

## 6.1 提问

接口：

`POST /api/v1/qa/ask`

请求体：

```json
{
  "knowledge_base_id": 1,
  "question": "LangChain 和 LangGraph 的区别是什么？",
  "session_id": 123
}
```

说明：

- `session_id` 可选
- 如果不传，后端自动创建新会话

响应体：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "session_id": 123,
    "answer": "LangChain 更偏向 LLM 应用组件编排，而 LangGraph 更适合状态化工作流编排。",
    "references": [
      {
        "document_id": 10,
        "file_name": "agent_notes.md",
        "chunk_index": 3,
        "snippet": "LangGraph 在链式组合之外提供显式状态图能力。"
      }
    ]
  }
}
```

## 6.2 获取问答会话列表

接口：

`GET /api/v1/qa/sessions`

## 6.3 获取单个问答会话

接口：

`GET /api/v1/qa/sessions/{id}`

## 7. 题库模块

## 7.1 生成题目

接口：

`POST /api/v1/question-bank/generate`

请求体：

```json
{
  "knowledge_base_id": 1,
  "document_id": 10
}
```

## 7.2 获取题目列表

接口：

`GET /api/v1/question-bank`

查询参数：

- `knowledge_base_id`，可选
- `document_id`，可选

## 8. 状态码建议

业务状态码建议：

- `0`：成功
- `4001`：参数错误
- `4003`：认证失败
- `4004`：资源不存在
- `5001`：服务内部错误

## 9. 接口开发补充约束

- 所有受保护接口都必须校验 JWT
- 所有资源接口都必须校验当前用户是否拥有该资源
- 上传接口必须校验文件类型和大小
- 文档删除时要同时删除向量索引
- 问答接口必须按 `knowledge_base_id` 限制检索范围
