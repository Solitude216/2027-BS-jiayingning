# 实验结果汇总

测试集：`data/samples/testset_2027-BS_v1.json`（共 120 条：可回答 45 / 不能回答 40 / 易混淆 35，v1.0 冻结）
生成模型：DeepSeek `deepseek-flash`（temperature=0.2）；嵌入：`bge-small-zh-v1.5`（本地离线）；BM25 用 jieba 分词；混合检索用 RRF（k=60）。
评测：知识命中/引用按金标准三元组 `gold_source/gold_role/gold_field` 判定。

## 主结果表（9 配置）

| 方案 | 可回答(45) | 不能回答(40) | 易混淆(35) | 总体(120) | 知识命中率 | 引用准确率 |
|---|---|---|---|---|---|---|
| 无 RAG | 0.400 | 0.050 | 0.686 | 0.367 | 0.000 | 0.000 |
| BM25·field·k5 | 0.800 | 0.925 | 0.600 | 0.783 | 0.483 | 0.775 |
| 向量·field·k5 | 0.778 | 1.000 | 0.771 | 0.850 | 0.542 | 0.833 |
| 混合 RRF·field·k5 | 0.911 | 0.950 | 0.943 | 0.933 | 0.650 | 0.808 |
| 向量·row·k5 | 0.422 | 0.975 | 0.314 | 0.575 | 0.075 | 0.575 |
| 向量·entity·k5 | 0.956 | 0.950 | 0.971 | 0.958 | 0.650 | 0.908 |
| 向量·field·k3 | 0.711 | 0.975 | 0.714 | 0.800 | 0.500 | 0.917 |
| 向量·field·k10 | 0.800 | 1.000 | 0.857 | 0.883 | 0.583 | 0.783 |
| 向量·field·k5·实体约束 | 0.778 | 0.975 | 0.771 | 0.842 | 0.542 | 0.775 |

## 结论要点

1. **RAG 显著优于无 RAG**：总体 0.367 → 0.85+；最关键差距在"不能回答"类——无 RAG 拒答率仅 0.05（逢问必答、幻觉严重），RAG 达 0.925~1.000。这是引入检索增强的核心收益。
2. **知识组织方式影响最大**：entity-grouped(0.958) ≫ field(0.850) ≫ row(0.575)。row 整行切块把多字段混在一段，可答/易混暴跌；按角色聚合后易混淆类升至 0.971。
3. **混合 RRF 优于单路**：field-k5 下 RRF 0.933 > 向量 0.850 > BM25 0.783；易混淆类 0.771→0.943，词法与语义互补。
4. **top-k**：总体 k3<k5<k10，但引用准确率随 k 下降（0.917→0.833→0.783），k5 为准确率与引用精度的平衡点。
5. **实体消歧未带来增益（诚实负面结论）**：加实体约束后易混淆类仍为 27/35=0.771，与不加约束完全相同；35 题全部成功抽到实体、过滤器确实生效，但错误集中在"命中正确角色后模型在命途/属性字段上答错"，瓶颈在字段级生成而非检索到错误实体。

## 明细文件

- `results/tables/matrix_no_rag.json`、`matrix_bm25_field_k5.json`、`matrix_vector_field_k5.json`、`matrix_hybrid_field_k5.json`、`matrix_vector_row_k5.json`、`matrix_vector_entity_k5.json`、`matrix_vector_field_k3.json`、`matrix_vector_field_k10.json`：各配置逐题结果
- `results/tables/eval_vector_field_k5_ec_*.json`：实体约束逐题结果
- `results/tables/matrix_summary.json`：机器可读汇总

## 复现命令

```bash
python scripts/run_experiment_matrix.py    # 跑 9 配置
python scripts/summarize_matrix.py         # 汇总主结果表
# 单配置示例：
python evaluation/run_eval.py --method vector --chunk entity --topk 5 --match-role-only
python evaluation/run_eval.py --method vector --chunk field --topk 5 --entity-constraint
```
