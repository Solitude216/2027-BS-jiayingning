# progress / weekly_log

---

# Week 01 项目推进

## 1. 本周任务
- 明确毕业论文课题（基于大语言模型的游戏知识问答与辅助）
- 搭建 GitHub 仓库（2027-BS-game）并确定目录结构
- 构建游戏知识库（整理《崩坏：星穹铁道》角色数据为 CSV）
- 构建并冻结初步测试集

## 2. 如何运行
```bash
git clone https://github.com/Solitude216/2027-BS-game
# 知识库生成脚本
python scripts/1_data_prep/生成角色基础信息csv.py
```

## 3. 输入
- 数据源：角色数据原始 txt 与官方开放 Wiki
- knowledge_base/角色数据txt

## 4. 输出
- knowledge_base/角色数据csv（8 个 CSV：基础信息/光锥/遗器/配队/行迹/星魂/晋阶/故事）
- data/samples/testset_2027-BS_v1.json（初步测试集）
- 仓库结构与 README 初稿

## 5. 本周完成情况
- 完成 8 个角色数据 CSV 的整理与生成，共 93 名角色、4723 行
- 完成测试集初步构建，确定"可回答/不能回答/易混淆"三类框架
- 完成 GitHub 仓库初步搭建，确立 configs/docs/experiments/results/src 等目录结构

## 6. 未解决问题
- 测试集题目口径与参考答案对照知识库的核验待完成
- 嵌入模型选型：huggingface 不可达，需改用 ModelScope 下载 bge-small-zh-v1.5

---

# Week 02 项目推进

## 1. 本周任务
- 确认课题与研究问题，阅读并确认参考文献
- 实现无RAG基线（Baseline）
- 实现基础 RAG 并开展主实验（检索方法对比：向量 / BM25）
- 冻结测试集并完成三方案评测

## 2. 如何运行
```bash
set DEEPSEEK_API_KEY=sk-xxx
python scripts/2_build_index/build_index.py
python evaluation/run_eval.py --no-rag
python evaluation/run_eval.py --method bm25
python evaluation/run_eval.py --method vector
```

## 3. 输入
- 冻结测试集 data/samples/testset_2027-BS_v1.json（120 题，三类）
- 知识库 8 个 CSV、docs/02-literature 参考文献

## 4. 输出
- results/checkpoints/index（检索索引）
- results/tables/eval_norag_field_*.json、eval_bm25_field_*.json、eval_vector_field_*.json
- results/summary.md（三方案对比结论）

## 5. 本周完成情况
- 完成课题与研究问题确认，阅读并整理参考文献列表与阅读笔记
- 跑通无RAG基线：总体准确率 0.333、拒答率 0.000（从不拒答，暴露幻觉问题）
- 跑通主实验：RAG-BM25 总体 0.750、RAG-向量总体 0.808；向量语义区分更强、BM25 字面略优
- 完成冻结测试集（v1.0，2026-10-05）与逐题参考答案核验（80/80 一致）

## 6. 未解决问题
- 字段级切块下"属性类"问题系统性检索错位（噪声块压制目标字段）
- 多值/长文本字段拆块导致回答不完整或自相矛盾
- 易混淆区分中 BM25 明显弱于向量；评测字符串比对口径过严

---

# Week 03 项目推进

## 1. 本周任务
- 按 2027-BS-game 仓库结构补充本地 C:\毕业论文 目录
- 撰写实验设计文档（docs/03-design/experiment_design.md）
- 撰写《Baseline 与问题分析报告》（results/baseline_report.docx）
- 补充实验记录（experiments/baseline、exp01-retrieval-method）与 README

## 2. 如何运行
```bash
python scripts/2_build_index/build_index.py
python scripts/3_run/run_rag.py -q "三月七的属性是什么？"
python evaluation/run_eval.py --method vector
```

## 3. 输入
- results/summary.md、eval_*.json（真实实验结果）
- 仓库结构参考（2027-BS-game main 分支）

## 4. 输出
- 目录重构后的 C:\毕业论文（configs/data/docs/evaluation/experiments/knowledge_base/progress/results/scripts/src/thesis）
- docs/03-design/experiment_design.md、README.md
- results/baseline_report.docx（5-7 页，含目录与三线表）

## 5. 本周完成情况
- 完成仓库目录补充与 README 按毕业论文模板重写
- 完成实验设计文档与《Baseline 与问题分析报告》（含三方案结果、问题归因、下一步）
- 完成 baseline 备注结论、exp01 主实验记录（EXP-001）与测试集校验脚本

## 6. 未解决问题
- 消融/性能测试（切分粒度、top_k、去重、混合检索）待开展
- 属性类检索错位、多值字段、实体消歧等改进待落地
- 嵌入模型（models/）约 200MB，建议 .gitignore 不入库

---

# Week 04 项目推进

## 1. 本周任务
- 修正评测体系四个问题：citation_accuracy 名不副实、answer_correct 逐字子串过严、hit_knowledge 依赖答案字符串、无RAG仍执行检索
- 补金标准字段 gold_role / gold_field / gold_source，重写可解释引用指标

## 2. 如何运行
```bash
python evaluation/run_eval.py --no-rag
python evaluation/run_eval.py --method vector
```

## 3. 输入
- 冻结测试集 data/samples/testset_2027-BS_v1.json（120 题）
- 早期三方案评测结果（旧口径偏松/偏严）

## 4. 输出
- evaluation/metrics.py：旧指标改名 source_role_match；新写真 citation_accuracy（解析"片段N"编号校验来源）
- answer_correct 改深度归一化（去标点+同义词归并+剥离修饰词）+ 多答案拆分 + 双向子串
- hit_knowledge 改按金标准三元组 gold_source/gold_role/gold_field 判定
- src/rag/rag.py：无RAG 完全跳过 retrieve
- scripts/augment_gold_fields.py 为 80 道可答/易混题补 gold 字段

## 5. 本周完成情况
- 问题1（citation 名不副实）：弱指标改名，真引用指标按"片段N"指向片段校验角色+来源
- 问题2（answer_correct 过严）：规则+同义词+多答案已实现
- 问题3（hit_knowledge 靠答案猜）：改为金标准三元组直接判定
- 问题4（无RAG 仍检索）：answer() 改为 with_context 为假时不 retrieve

## 6. 未解决问题
- 三种切块对比（row / field / entity-grouped）
- top-k=3/5/10、混合 RRF
- 实体约束检索
- 9 配置实验矩阵

---

# Week 05 项目推进

## 1. 本周任务
- 实现三种切块对比（row / field / entity-grouped）、top-k=3/5/10、混合 RRF、实体约束检索
- 在 120 题冻结测试集上跑完 9 配置实验矩阵，产出主结果表

## 2. 如何运行
```bash
$env:DEEPSEEK_API_KEY="sk-xxx"
python scripts/run_experiment_matrix.py    # 9 配置
python scripts/summarize_matrix.py          # 汇总主结果表
```

## 3. 输入
- 补好 gold 三元组的冻结测试集、8 个角色 CSV
- Week 04 修正后的评测口径

## 4. 输出
- src/rag/retriever.py（RRF 混合 k=60、entity_filter 事后过滤）、documents.py（entity-grouped 切块）
- results/tables/matrix_*.json（8 配置明细）、eval_vector_field_k5_ec_*.json、matrix_summary.json
- experiments/exp01-retrieval-method/EXP-001、experiments/exp02-entity-constraint/EXP-002 及 answer_correct 双检表

## 5. 本周完成情况
- 跑完 9 配置矩阵：最佳 entity-grouped 总体 0.958、混合 RRF 0.933；知识组织方式影响最大
- top-k 扫描：k3<k5<k10，但引用精度随 k 下降，k5 为平衡点
- 实体约束检索验证：易混淆类仍 27/35=0.771，与不加约束相同——实体消歧无增益（负面结论）
- answer_correct 人工双检：25 题分层抽样，人审与规则判定一致率 100%

## 6. 未解决问题
- 易混淆剩余 8 道错题在字段级生成（命途/属性），需生成端改进
- 完整毕业论文撰写待启动
