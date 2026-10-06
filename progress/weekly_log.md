# progress / weekly_log

> 周志按图片模板（Week XX 代码练习与项目推进）填写。

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
