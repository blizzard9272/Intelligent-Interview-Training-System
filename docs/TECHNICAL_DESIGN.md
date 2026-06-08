# 技术设计

## 1. 设计目标

当前系统的技术设计需要同时满足以下目标：

- 支持多用户、知识库隔离和权限约束
- 支持文档异步入库和向量检索
- 支持可解释的 RAG 问答
- 支持题目生成与模拟面试训练闭环
- 支持训练分析与专项 drill 推荐
- 为后续 RAG 优化、评估体系和 Agent 化演进保留空间

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
- FastAPI BackgroundTasks

当前生成和 embedding 策略仍采用“在线能力优先，必要时本地 fallback”的思路，保证开发环境和演示环境都能运行。

## 3. 模块分层

当前项目建议继续保持以下分层：

- `api`：HTTP 接口层
- `schemas`：请求与响应模型
- `db/models`：数据库模型
- `services`：核心业务逻辑
- `rag`：检索、向量、生成相关逻辑
- `tasks`：异步任务
- `core`：配置、异常、日志、安全

这种结构当前已经足以支撑后续两条主线：

- 继续强化 RAG 质量
- 继续演进训练系统

## 4. 当前已落地的技术方案

### 4.1 文档入库

主流程：

1. 用户上传文档
2. 创建文档记录
3. 创建入库任务
4. 异步解析文档
5. 文本清洗与切分
6. 生成 embedding
7. 写入 Chroma
8. 更新任务与文档状态

当前特点：

- 使用异步任务避免阻塞请求
- 支持知识库粒度的数据隔离
- 后续可继续扩展更细粒度的 metadata

### 4.2 RAG 问答

主流程：

1. 接收问题
2. 校验用户与知识库权限
3. 从向量库召回相关 chunk
4. 基于检索上下文生成回答
5. 返回答案与引用片段
6. 保存问答历史

当前回答策略：

- 优先基于检索到的上下文回答
- 如果没有足够的参考内容，允许做受控补充
- 补充回答使用统一话术前缀，降低“伪装成确定事实”的风险

当前限制：

- 召回质量、chunk 策略、重排、评估体系还未系统优化
- 目前更偏“基本可用”，尚未形成成熟的检索质量闭环

### 4.3 题库生成

主流程：

1. 选择知识库和可选来源文档
2. 读取已入库内容
3. 生成结构化题目草稿
4. 持久化到 `question_bank`

当前题目字段至少包括：

- `question`
- `reference_answer`
- `tags`
- `difficulty`
- `source_document_id`

当前常用题型标签包括：

- `concept`
- `scenario`
- `followup`
- `design`

### 4.4 面试训练模块

当前面试模块采用“服务层编排 + 会话持久化”的实现方式，而不是直接上 LangGraph。

当前核心对象：

- `InterviewSession`
- `InterviewTurn`

当前 turn 角色包括：

- `interviewer`
- `candidate`
- `interviewer_feedback`
- `interviewer_followup`
- `interview_summary`

主流程：

1. 发起训练会话
2. 根据训练参数选题
3. 写入首题和会话计划
4. 用户提交回答
5. 生成反馈
6. 判断是否继续追问或切换到下一题
7. 会话结束后自动生成总结

### 4.5 多题训练与 session plan

为了避免频繁新增数据库结构，当前多题训练计划没有独立建表，而是保存在首个 `InterviewTurn.meta_json["session_plan"]` 中。

当前已存储的计划信息包括：

- `drill_mode`
- `question_count`
- `question_strategy`
- `focus_topic`
- `selected_question_ids`
- `current_question_index`

这个方案的优点：

- 无需新增迁移即可快速演进训练编排
- 会话逻辑与实际题目序列天然绑定
- 前后端改动成本较低

### 4.6 训练分析

当前已经提供独立训练分析接口：`GET /interview/analysis`

分析聚合内容包括：

- 总训练次数
- 完成次数
- 分数统计
- 高频弱点
- 高频亮点
- 题型分布
- 来源文档分布
- 最近成绩走势
- 推荐 focus
- focus drill 推荐
- focus drill 效果统计

当前 focused drill 的实现特点：

- 不是纯前端文案，而是后端真实选题逻辑
- 支持 `focus_topic` 参与题目优先级排序
- 匹配范围包括：
  - question 文本
  - reference answer
  - tags
  - source document name

### 4.7 前端训练页面与分析页面

当前前端已经完成两块关键页面：

- `InterviewView`
- `TrainingAnalysisView`

当前交互链路：

1. 用户在分析页查看推荐 drill
2. 点击 `Start Drill`
3. 路由携带训练参数跳转到 Interview 页
4. Interview 页读取 query 参数并自动预填
5. 在 `autoStart=1` 时直接发起专项训练

## 5. 测试设计现状

当前已经补齐 interview service 的核心单元测试，重点覆盖：

- 按策略选题
- 多题训练
- focus topic 优先匹配
- training analysis 聚合
- focus drill 效果计算

当前仍可继续补充：

- RAG 检索与回答质量评估测试
- API 层集成测试
- 前端关键训练流程测试

## 6. 后续技术演进建议

### 6.1 最优先：RAG 质量工程化

建议下一阶段重点投入：

- chunk 策略试验
- metadata filtering
- rerank / hybrid retrieval
- 检索日志
- 离线评估集

### 6.2 训练系统继续演进的保留方向

如果后面继续强化训练系统，建议沿以下方向演进：

- 弱点类别规范化
- 长期训练画像
- 更细的专项 drill 生成逻辑
- 训练分析可视化增强

### 6.3 Agent / LangGraph 化的未来拆分

如果未来要进入 Agent 或 LangGraph 编排，当前服务层逻辑可拆为这些节点：

1. `select_question`
2. `ask_question`
3. `receive_answer`
4. `score_answer`
5. `decide_followup`
6. `generate_followup`
7. `generate_summary`
8. `update_training_profile`

当前之所以还没有直接上图编排，是因为：

- 现在的服务层逻辑已经能稳定承载主流程
- 先优化业务效果，比先升级编排框架更有价值
- 等 RAG 质量和训练画像更成熟后，再引入图编排会更自然
