# experiments/

实验目录。

- `baseline/`：无 RAG 基线（直接 LLM 问答），含 `baseline_no_rag.py`、`config.yaml`、`command.txt`、`notes.md`、`metrics.csv`。
- `exp01/`：RAG（向量检索）。
- `exp02/`：RAG（BM25 / 混合检索 或 不同切分方案）。

每次实验的产出（命令、配置、指标、备注）保存在对应子目录。

