# PGVector 迁移说明与 RAG 下一步优化重点

## 1. 本次迁移完成了什么

本次改造已经把项目中的向量存储实现从独立的 Chroma 方案切换到了基于 PostgreSQL 的 `PGVector` 方案，代码层面的主要变化包括：

- 新增 `document_chunks` 表模型，用于统一存储 chunk 文本、embedding 向量和检索 metadata
- 新增 `PGVectorStore`，替代原先的 `ChromaVectorStore`
- 保留原有 service 层调用方式，尽量不改动入库、检索、问答主流程
- 为 SQLite 测试环境保留兼容回退逻辑，避免单元测试依赖真实 PostgreSQL + pgvector 才能运行
- 新增对应 Alembic 迁移和向量存储单元测试

本次迁移后，业务数据和向量数据的目标架构变为：

- `PostgreSQL`：用户、知识库、文档、任务、问答历史、chunk 向量
- `PGVector`：在 PostgreSQL 内部提供向量列和向量相似度检索能力

## 2. 当前状态

### 2.1 代码状态

代码已完成接入，且后端测试已经通过。

本地已验证：

- 新增向量存储单测通过
- 检索路由相关测试通过
- 后端全量单测通过

### 2.2 环境状态

当前本地 PostgreSQL 实例**尚未安装 `pgvector` 扩展**，因此 Alembic 迁移在执行到：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

时失败。

报错核心信息：

```text
extension "vector" is not available
The extension must first be installed on the system where PostgreSQL is running.
```

这说明：

- 代码迁移方案本身没有明显逻辑错误
- 真正阻塞上线的是数据库实例缺少 `pgvector` 扩展

## 3. 要让 PGVector 真正可用，还需要什么

下一步必须先在 PostgreSQL 所在机器安装 `pgvector` 扩展。

### 3.1 安装完成后的动作

1. 在 PostgreSQL 所在环境安装 `pgvector`
2. 确认数据库支持 `CREATE EXTENSION vector`
3. 执行迁移：

```powershell
cd backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

4. 重新上传文档，触发新的 chunk 入库
5. 运行问答接口验证检索与回答链路

### 3.2 验证建议

至少验证以下场景：

- 上传 `md/txt/pdf` 文档后，`document_chunks` 表中能写入 chunk
- 删除文档时，相关 chunk 能同步删除
- `GET /documents/{id}/chunks` 能返回 chunk 内容与 metadata
- `POST /qa/ask` 能正常检索并生成回答
- 概念题、设计题、实现题三类问题都能返回合理引用

## 4. PGVector 替换 Chroma 的价值

这次替换最主要的收益不是“模型立刻答得更准”，而是：

- 向量数据与业务数据统一到同一个 PostgreSQL 中，部署和备份更统一
- 更容易做 SQL 级过滤和联表分析
- 更适合向生产化、工程化方向演进
- 更方便后续扩展 hybrid retrieval、审计、统计分析和权限隔离

需要明确的是：

- **PGVector 不会自动提升 RAG 质量**
- 检索效果的核心仍然取决于 chunk、metadata、检索策略、rerank 和评估体系

## 5. 下一步提升 RAG 质量的关键步骤

下面这些是后续最值得优先投入的方向，建议按顺序推进。

### 5.1 先建立稳定的评估闭环

目标：避免“感觉优化了”，而是能量化比较。

优先做法：

- 扩充离线评估集，至少补到 20 到 50 条真实问题
- 按问题类型分类：概念题、对比题、设计题、实现题、长尾定位题
- 固定评估指标：
  - `document_hit_rate`
  - `file_hit_rate`
  - `keyword_hit_rate`
  - `top_k hit rate`
  - `MRR`

### 5.2 优化 chunk 策略

当前系统仍以固定窗口字符切分为主，后续最可能带来收益的是：

- 按标题、段落、列表、问答对进一步结构化切分
- 控制 chunk 不要过长，减少主题混杂
- 对问答材料保留问答边界
- 对概念型文档保留标题与段落上下文
- 对设计文档尽量保持“问题-方案-权衡”结构

优先实验参数：

- `chunk_size`
- `chunk_overlap`
- 标题感知切分
- Q&A 感知切分

### 5.3 强化 metadata 设计

当前项目已经有一个不错的起点，后续可以继续增强：

- `document_kind`
- `content_type_hint`
- `section_title`
- `page_no`
- `starts_with_question`

建议继续补充的方向：

- 主题标签
- 技术栈标签
- 文档来源类型
- 难度或重要性分级

metadata 越稳定，后续 query routing 和 rerank 的收益越明显。

### 5.4 升级检索策略

当前已经有：

- 向量召回
- metadata 路由召回
- 启发式 rerank

后续建议继续做：

- hybrid retrieval：向量召回 + 关键词/BM25 召回
- 多路召回结果合并去重
- query rewrite / query expansion
- 标题命中和正文命中的差异化加权

### 5.5 升级 rerank

当前 rerank 仍是规则打分逻辑，适合第一阶段，但天花板有限。

下一阶段可考虑：

- 引入更细的特征打分
- 对问题类型使用不同 rerank 权重
- 引入模型级 reranker 或 cross-encoder
- 对引用片段做去噪和截断优化

### 5.6 优化生成阶段的 grounded answer

仅靠“召回正确”还不够，生成阶段也会影响最终观感。

建议继续优化：

- 控制上下文长度，减少无关片段干扰
- 让 prompt 更明确地区分“知识库证据”和“通用补充”
- 优化引用格式，增强可读性
- 在证据不足时更明确拒答或降级说明

### 5.7 增强可观测性

后续建议把以下数据沉淀得更完整：

- query route
- query plan
- 每轮召回结果
- rerank 前后顺序变化
- 最终引用片段
- 失败问题样本

这样后面才能高效定位：

- 是切分问题
- 是 embedding 问题
- 是召回问题
- 还是生成问题

## 6. 推荐的推进顺序

建议按下面顺序推进，而不是同时发散：

1. 安装 `pgvector` 扩展并完成数据库迁移
2. 用真实文档重新入库，确认 PGVector 检索链路可用
3. 补齐离线评估集，记录当前基线
4. 做 chunk 策略实验
5. 做 metadata 与 query routing 优化
6. 做 hybrid retrieval / rerank 升级
7. 最后再继续优化 prompt 和回答组织方式

## 7. 当前结论

本次改造已经完成了**代码层面的 PGVector 接入**，并通过了测试验证；  
但要让项目在你当前本地 PostgreSQL 环境中真正跑起来，还需要先补齐 `pgvector` 扩展这一环境前提。

因此当前最准确的状态描述是：

- **代码已完成迁移**
- **测试已通过**
- **数据库环境尚未满足 PGVector 运行条件**

