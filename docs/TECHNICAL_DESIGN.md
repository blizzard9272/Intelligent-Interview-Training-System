# 技术设计文档

## 1. 设计目标

当前一期系统的技术方案需要同时满足以下要求：

- 支持多用户使用
- 支持知识库隔离
- 支持异步文档入库
- 支持可解释的 RAG 问答
- 支持题目生成与模拟面试闭环
- 为后续 Agent 化和 LangGraph 工作流预留扩展能力

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
- Chroma

当前异步方案：

- FastAPI BackgroundTasks

当前 Embedding 方案：

- 本地开发优先使用本地 embedding fallback

当前生成方案：

- 在线模型优先
- 本地规则或本地合成作为 fallback

## 3. 当前模块结构

建议保持以下分层：

- `api`：HTTP 接口层
- `schemas`：请求与响应模型
- `db/models`：数据库模型
- `services`：核心业务逻辑
- `rag`：检索、生成、向量相关逻辑
- `tasks`：异步任务
- `core`：配置、异常、安全与日志

## 4. 当前已落地能力

### 4.1 文档入库

主流程：

1. 用户上传文件
2. 创建文档记录
3. 创建入库任务
4. 异步解析文档
5. 清洗文本
6. 切分 chunk
7. 生成 embedding
8. 写入 Chroma
9. 更新任务与文档状态

### 4.2 RAG 问答

主流程：

1. 接收问题
2. 校验知识库权限
3. 召回相关 chunk
4. 优先基于检索上下文生成回答
5. 返回引用片段
6. 保存问答会话

补充策略：

- 如果有有效检索内容，优先按上下文回答
- 如果没有有效参考内容，可允许模型自行补充
- 自行补充时统一以 `据我所知，` 开头

### 4.3 题目生成

当前题目生成模块采用“模型优先 + 本地规则回退”的方式。

主流程：

1. 选择知识库与可选文档
2. 读取已完成入库的文档 chunk
3. 生成结构化题目草稿
4. 保存到 `question_bank`

当前已落库字段包括：

- `question`
- `reference_answer`
- `tags`
- `difficulty`

当前题型标签约定：

- `concept`
- `scenario`
- `followup`
- `design`

### 4.4 面试模块

当前面试模块采用“服务层驱动 + 会话持久化”的方案，而不是先上 LangGraph。

当前会话核心对象：

- `InterviewSession`
- `InterviewTurn`

当前 turn 角色包括：

- `interviewer`
- `candidate`
- `interviewer_feedback`
- `interviewer_followup`
- `interview_summary`

主流程：

1. 发起面试
2. 从题库中选择题目
3. 保存首轮面试题
4. 提交候选人回答
5. 生成反馈
6. 决定是否继续追问
7. 保存追问或结束会话
8. 会话结束后自动生成总结

### 4.5 面试总结设计

面试总结当前没有单独加 session 表字段，而是作为一条特殊 turn 持久化：

- `role = interview_summary`

这样做的原因：

- 不需要新增迁移
- 与现有会话轨迹天然一致
- 前端展示简单
- 后续如果需要结构化报表，再考虑独立字段或独立表

总结生成策略：

- 优先复用 `prompt.yaml` 中的 `interview_summary`
- 优先调用在线模型生成结构化总结
- 如果模型失败，则回退到本地规则总结

总结输出内容当前包括：

- 总结正文
- 亮点
- 薄弱点
- 下一步训练建议

### 4.6 专项面试选题设计

当前面试发起时支持以下筛选条件：

- `knowledge_base_id`
- `difficulty`
- `question_type`

其中：

- `difficulty` 直接使用 `question_bank.difficulty`
- `question_type` 通过 `question_bank.tags` 匹配

当前方案的优点：

- 不新增表结构
- 与现有题目生成结果天然兼容
- 前后端实现成本低

当前限制：

- 还不支持按来源文档筛选
- 还不支持“优先最近题目”或“避开最近做过的题目”
- 还不支持一次训练多题编排

## 5. 异常处理与可观测性

当前已补充：

- 后端异常处理
- 请求日志
- 前端全局 API 报错弹窗

建议继续保持：

- 所有受保护接口都校验用户权限
- 所有数据库查询都带 `user_id`
- 所有知识库相关查询都带 `knowledge_base_id`

## 6. 前端设计现状

当前主要页面：

- 文档管理页
- QA 页
- 历史页
- 面试页

当前前端已完成：

- 中文文案整理
- 局部组件抽取
- 页面风格统一
- 面试总结区域展示
- 难度 / 题型筛选表单

## 7. 下一步技术建议

### 7.1 面试配置编排

建议作为下一阶段的第一优先级：

- 按文档来源筛题
- 配置训练模式
- 控制训练题数或轮次
- 控制题目新旧优先级

### 7.2 自动化测试

建议增加：

- 面试创建测试
- 题目筛选测试
- 总结生成 fallback 测试
- 面试完成状态测试
- 题目生成持久化测试

### 7.3 二期 Agent 化方向

如果后续进入 Agent / LangGraph 化，建议把现有服务层逻辑拆分为以下节点：

1. `select_question`
2. `ask_question`
3. `receive_answer`
4. `score_answer`
5. `decide_followup`
6. `generate_followup`
7. `generate_summary`
8. `update_training_profile`

当前已经具备较好的前置条件：

- 题目持久化已完成
- 面试轮次持久化已完成
- 总结持久化已完成
- 前端面试页面已可承载更复杂流程
