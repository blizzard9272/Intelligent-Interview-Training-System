# RAG 评估基线

## 1. 目标

这份文档对应项目当前的第一阶段 RAG 优化动作：先建立一个最小可运行的离线评估基线。

第一版不追求复杂，而是先回答三个最关键的问题：

1. 检索有没有命中预期文档
2. 检索结果里有没有出现预期文件
3. 检索片段里有没有包含预期关键词

## 2. 当前已提供的工具

项目中已经新增：

- 评估脚本：[backend/scripts/evaluate_rag.py](/f:/pythonProjects/ai_project/backend/scripts/evaluate_rag.py)
- 样例数据集：[backend/evals/rag_eval_dataset.sample.json](/f:/pythonProjects/ai_project/backend/evals/rag_eval_dataset.sample.json)

脚本会复用当前 `QAService` 的检索逻辑，因此它评估的是“现在系统真实使用的召回行为”，而不是一套脱离业务代码的伪流程。

## 3. 数据集格式

每条样例支持以下字段：

- `id`：样例 id，便于追踪
- `knowledge_base_id`：所属知识库
- `question`：测试问题
- `expected_document_ids`：期望命中的文档 id，可选
- `expected_file_names`：期望命中的文件名，可选
- `expected_keywords`：期望在召回片段中出现的关键词，可选

建议一开始先积累 20 到 50 条真实问题，不要只写“教科书问题”，尽量覆盖：

- 概念解释题
- 对比题
- 总结题
- 细节定位题
- 容易检索失败的长尾问题
- 基于概念型技术文档的解释题
- 基于设计说明文档的 trade-off 题
- 基于项目复盘文档的场景题

## 4. 运行方式

在项目根目录下执行：

```powershell
.\.venv\Scripts\python.exe backend\scripts\evaluate_rag.py --dataset backend\evals\rag_eval_dataset.sample.json --user-id 1
```

如果想把结果保存出来：

```powershell
.\.venv\Scripts\python.exe backend\scripts\evaluate_rag.py --dataset backend\evals\rag_eval_dataset.sample.json --user-id 1 --output backend\evals\reports\baseline.json
```

如果不传 `--user-id`，脚本会默认取数据库中的第一个用户。

## 5. 当前输出指标

脚本当前会输出这些摘要指标：

- `document_hit_rate`
- `file_hit_rate`
- `keyword_hit_rate`
- `average_reference_count`

这足够作为第一版基线，后续可以继续扩展：

- top-1 / top-k 命中率
- MRR
- 不同题型分组表现
- 不同 chunk 策略的 A/B 对比
- 重排前后对比

## 6. 推荐的下一步

在这份基线之上，最推荐立刻做的事情是：

1. 把样例数据集补到至少 20 条
2. 为每条问题确认“理想命中文档”或“理想命中关键词”
3. 记录当前基线结果
4. 再开始做 `chunk_size`、`chunk_overlap` 和切分策略实验

这样你后面每次做 RAG 优化，都能明确回答一个面试里很重要的问题：

“这次改动到底让检索效果提高了多少，而不是只是感觉更好了。”

## 7. 当前新增的概念文档支持

为了让评估集更贴近真实用户资料，样例数据已经从单纯的面试题场景扩展到了：

- 概念说明文档
- 系统设计文档
- 项目复盘文档
- 实现步骤文档

这能帮助后续验证一个更关键的问题：

“系统是否不仅能吃标准问答资料，也能从概念性技术材料中检索并组织出有价值的答案与题目。”
