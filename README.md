# 2027 届本科毕业论文

## 基本信息

- 姓名：贾滢宁
- 学号：202321020211
- 专业：人工智能
- 指导教师：曾维
- 毕业论文题目：基于大语言模型的游戏知识问答与辅助方法设计与实现
- 研究方向：大语言模型应用 / 检索增强生成（RAG）/ 游戏智能

## 一、研究问题

本项目以《崩坏：星穹铁道》游戏角色数据（角色基础信息、光锥、遗器、配队、行迹、星魂、晋阶、故事等）为领域知识库，研究如何让大语言模型（LLM）在专有游戏知识问答中给出准确、可溯源且不产生幻觉的回答。当前的问题是：通用 LLM 直接问答对专有游戏知识覆盖不足、易臆造答案（幻觉），且无法区分"库中确实没有"的不可回答问题。本论文拟解决的核心问题是：如何通过检索增强生成（RAG）把本地结构化知识库与 LLM 结合，实现"可回答问题准确作答、不可回答问题正确拒答、易混淆问题正确区分"三类能力，并通过冻结测试集量化各方案的增益。

## 二、最低完成要求

- [x] Baseline / 基础系统（无RAG直答基线 + 基础RAG系统）
- [x] 核心方法或关键机制（检索增强生成 RAG：切分→嵌入→检索→生成）
- [x] 对比实验（无RAG / BM25 / 向量 / 混合 RRF，120题冻结测试集）
- [x] 消融/性能测试（切块 row/field/entity-grouped、top-k=3/5/10、混合 RRF）
- [x] 错误或异常情况分析（含实体消歧负面结论、字段级错题归因）
- [ ] 完整毕业论文（撰写中）

## 三、拓展目标

- [x] 混合检索（向量 + BM25，RRF）与参数消融（top-k、切块）
- [x] 实体约束检索：验证后判定实体消歧非当前瓶颈（负面结论）
- [ ] 重排序（Rerank）/ 生成端字段化改进：修复命途/属性字段级答错
- [ ] 可演示的交互问答系统

## 四、技术路线

总体流程：整理游戏知识库（CSV）→ 构建冻结测试集（120题，三类）→ 实现基础 RAG（文档切分/嵌入/检索/生成）→ 实现无RAG基线 → 在冻结测试集上对比评测 → 错误归因与迭代改进 → 形成论文实验章节。

详见：[docs/01-topic/technical_route.md](docs/01-topic/technical_route.md)

## 五、当前进展

- **当前阶段**：9 配置实验矩阵已跑完，主结果表与实体消歧结论已产出，进入论文撰写阶段。
- **最近完成**：评测体系四项修正（真 citation、金标准 hit、answer_correct 归一化、无RAG跳过检索）；row/field/entity-grouped 切块对比、top-k=3/5/10、混合 RRF、实体约束检索；最佳 entity-grouped 总体 0.958。
- **当前问题**：易混淆剩余 8 道错题在字段级生成（命途/属性答错），非检索到错误实体。
- **下一步**：生成端字段化改进、交互演示系统、撰写论文实验章节。

## 六、主要实验结果

评测于 120 题冻结测试集（`data/samples/testset_2027-BS_v1.json`，deepseek-flash 生成）：

| Experiment | 可回答(45) | 不能回答(40) | 易混淆(35) | 总体(120) | Status |
|---|---|---|---|---|---|
| 无RAG基线 | 0.400 | 0.050 | 0.686 | 0.367 | ✅ 完成 |
| RAG-BM25·field·k5 | 0.800 | 0.925 | 0.600 | 0.783 | ✅ 完成 |
| RAG-向量·field·k5 | 0.778 | 1.000 | 0.771 | 0.850 | ✅ 完成 |
| 混合 RRF·field·k5 | 0.911 | 0.950 | 0.943 | 0.933 | ✅ 完成 |
| RAG-向量·row·k5 | 0.422 | 0.975 | 0.314 | 0.575 | ✅ 完成 |
| RAG-向量·entity·k5 | 0.956 | 0.950 | 0.971 | **0.958** | ✅ 完成 |
| RAG-向量·field·k3 | 0.711 | 0.975 | 0.714 | 0.800 | ✅ 完成 |
| RAG-向量·field·k10 | 0.800 | 1.000 | 0.857 | 0.883 | ✅ 完成 |
| RAG-向量·field·k5·实体约束 | 0.778 | 0.975 | 0.771 | 0.842 | ✅ 完成 |

要点：知识组织方式影响最大（entity-grouped 最优）；混合 RRF 优于单路；k5 为准确率与引用精度平衡点；**实体约束未提升易混淆（27/35 不变），瓶颈在字段级生成而非检索到错误实体**。详见 `results/summary.md` 与 `experiments/exp02/EXP-002-entity-constraint.md`。

## 七、仓库目录说明

```
configs/          RAG 与实验配置（rag.yaml）
data/             数据（metadata 元信息、samples 测试集）
docs/             文档（01选题 / 02文献 / 03设计 / 04会议）
evaluation/       评测代码与指标（run_eval.py / metrics.py / verify_testset.py）
experiments/      实验（baseline 无RAG基线、exp01-retrieval-method 检索主实验、exp02 实体约束）
knowledge_base/   游戏知识库（角色数据csv / 角色数据txt）
progress/         进度（issues / milestones / weekly_log）
results/          结果（checkpoints 索引 / figures / logs / tables / summary.md）
scripts/          脚本（1_data_prep / 2_build_index / 3_run）
src/rag/          基础 RAG 源码（documents/embed/retriever/generator/rag/config）
thesis/           论文（outline、drafts、figures、references、tables）
```

## 八、本人主要贡献

- **数据**：手工整理《崩坏：星穹铁道》官方开放 Wiki 角色数据为 8 个 CSV（角色基础信息/光锥/遗器/配队/行迹/星魂/晋阶/故事）；设计并冻结 120 题三类测试集（可回答/不能回答/易混淆），参考答案逐条对照知识库核验。
- **代码**：实现基础 RAG 全链路（`src/rag/`：CSV 字段级切分与去重、bge-small-zh-v1.5 本地嵌入、向量/BM25/混合检索、DeepSeek 生成、配置与提示词分离）；实现无RAG基线（`experiments/baseline/`）；编写建索引、交互问答、评测、测试集校验脚本。
- **实验**：完成无RAG、BM25、向量、混合 RRF 及三种切块（row/field/entity-grouped）、top-k=3/5/10、实体约束共 9 配置在冻结测试集上的评测，产出主结果表（最佳 entity-grouped 总体 0.958）与实体消歧负面结论。
- **论文**：撰写实验设计文档（`docs/03-design/experiment_design.md`）、《Baseline 与问题分析报告》（`results/baseline_report.docx`）及 EXP-001/EXP-002 实验记录。

## 九、参考项目与第三方代码

- 项目：bge-small-zh-v1.5（中文文本嵌入模型）
  - URL：https://modelscope.cn/models/BAAI/bge-small-zh-v1.5
  - License：MIT
  - 本项目修改内容：本地离线部署使用，未修改模型权重；用于知识库与查询的向量编码。
- 项目：DeepSeek 大语言模型（deepseek-flash，生成模型，OpenAI 兼容接口）
  - URL：https://api.deepseek.com
  - License：按 DeepSeek 服务条款
  - 本项目修改内容：仅作为问答生成模型调用，未做微调。
- 数据来源：《崩坏：星穹铁道》官方开放 Wiki，本人手工整理标注，仅用于学术研究，不涉及商业用途。

## 十、环境与复现

- **平台**：Windows（本地主机），Python 3.14.7
- **依赖**：openai、numpy、pandas、jieba、torch、transformers、sentence-transformers、modelscope、pyyaml 等（见各脚本 import）
- **嵌入模型**：bge-small-zh-v1.5，下载至 `models/` 本地离线加载（需设 `TRANSFORMERS_OFFLINE=1`、`HF_HUB_OFFLINE=1`；`models/` 不入库）
- **生成模型**：DeepSeek deepseek-flash，通过环境变量 `DEEPSEEK_API_KEY` 配置
- **复现步骤**：
  ```bash
  # 1. 配置 API Key
  set DEEPSEEK_API_KEY=sk-xxx
  # 2. 构建索引
  python scripts/2_build_index/build_index.py
  # 3. 交互问答
  python scripts/3_run/run_rag.py -q "三月七的属性是什么？"
  python scripts/3_run/run_rag.py --no-rag        # 无RAG基线
  # 4. 冻结测试集评测
  python evaluation/run_eval.py --method vector
  python evaluation/run_eval.py --method bm25
  python evaluation/run_eval.py --no-rag
  # 5. 测试集校验
  python evaluation/verify_testset.py
  ```
