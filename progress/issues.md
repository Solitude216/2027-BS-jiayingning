# progress / issues

> 跟踪项目中的问题与待办，已完成项打勾并附日期。

## 已完成
- [x] 构建知识库（8 CSV，93 角色，Week 01）
- [x] 构建并冻结测试集（120 题，三类，2026-10-05）
- [x] 跑通云端 API 基线（DeepSeek deepseek-flash）
- [x] 搭建本地 RAG 链路（bge-small-zh 嵌入 + 向量/BM25/混合检索 + 生成）
- [x] 无RAG vs RAG、检索方法对比（BM25 / 向量 / 混合 RRF）
- [x] 评测体系修正：真 citation_accuracy（解析"片段N"）、answer_correct 深度归一化+多答案、hit_knowledge 金标准三元组、无RAG跳过检索（Week 04）
- [x] 切块对比 row / field / entity-grouped、top-k=3/5/10、混合 RRF、实体约束检索（Week 04-05）
- [x] answer_correct 人工双检抽审：25 题分层抽样，人审与规则判定一致率 100%（Week 05）
- [x] 撰写 Baseline 与问题分析报告（results/baseline_report.docx）

## 待办
- [ ] 生成端改进：字段化 prompt / 结构化答案约束，解决命途/属性字段级答错（8 道易混错题）
- [ ] 搭建可演示交互系统
- [ ] 完成完整毕业论文

## 已知结论（实验中确认）
- 知识组织方式影响最大：entity-grouped(0.958) ≫ field(0.850) ≫ row(0.575)
- 混合 RRF 优于单路向量/BM25；k5 为准确率与引用精度平衡点
- 实体消歧无效：加实体约束后易混淆仍 27/35=0.771，瓶颈在字段级生成而非检索到错误实体
- RAG 核心收益在防幻觉：无 RAG 拒答率 0.05，RAG 达 0.925~1.000
