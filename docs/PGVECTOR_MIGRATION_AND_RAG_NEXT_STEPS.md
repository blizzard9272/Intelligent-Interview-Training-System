# PGVector 迁移说明与 RAG 下一步优化重点

## 1. 已完成内容

本次改造已经完成以下工作：

- 将项目向量存储实现从 Chroma 切换为 PostgreSQL + PGVector
- 新增 `document_chunks` 表模型，统一存储 chunk 文本、embedding 与检索 metadata
- 新增 `PGVectorStore` 并接入现有入库、删除、查询、问答链路
- 为 SQLite 测试环境保留兼容回退逻辑
- 增加向量存储、Markdown 前言保留、检索重排等回归测试

## 2. 当前状态

当前代码与测试已经覆盖：

- 文档解析与 chunk 入库
- PGVector 向量查询
- 检索路由
- rerank
- fallback
- 引用片段优化

如果本地 PostgreSQL 已成功安装 `pgvector` 扩展并执行迁移，则当前向量链路已经具备可用条件。

## 3. 当前已落地的 RAG 质量优化

### 3.1 文档解析层

- 保留 Markdown 首标题前的定义型引言内容
- 提升概念型资料的 `document_kind` 判定稳定性
- 强化 `content_type_hint` 规则

### 3.2 检索与重排层

- 基于问题意图做 query routing
- 启发式 rerank
- 定义型问题优先提升定义 chunk

### 3.3 生成与展示层

- 收紧 QA prompt，减少无关扩写
- 无证据时使用受控 fallback
- 引用片段按句子边界截断并延长展示长度

## 4. 下一步最值得继续做的事情

建议按下面顺序推进：

1. 继续优化 chunk 策略
2. 增强 metadata 设计
3. 引入 hybrid retrieval
4. 升级 rerank
5. 扩充离线评估集
6. 继续改进引用展示与可解释性

## 5. 对外讲述建议

如果用于 GitHub、简历或面试展示，可以将本阶段总结为：

- 完成 PGVector 向量化存储迁移
- 跑通可解释 RAG 问答主链路
- 具备 metadata 增强检索、检索路由、rerank、引用溯源、fallback 与 debug trace
- 已开始围绕真实问题持续优化 RAG 质量
