# 2027 届本科毕业论文

## 基本信息

- 姓名：（待填写）
- 学号：（待填写）
- 专业：（待填写）
- 指导教师：曾维
- 毕业论文题目：基于大语言模型的游戏知识问答与辅助方法设计与实现
- 研究方向：大语言模型应用 / 检索增强生成（RAG）/ 游戏智能

## 一、研究问题

本项目以《崩坏：星穹铁道》游戏角色数据（角色基础信息、光锥、遗器、配队、行迹、星魂、晋阶、故事等）为领域知识库，研究如何让大语言模型（LLM）在专有游戏知识问答中给出准确、可溯源且不产生幻觉的回答。当前的问题是：通用 LLM 直接问答对专有游戏知识覆盖不足、易臆造答案（幻觉），且无法区分"库中确实没有"的不可回答问题。本论文拟解决的核心问题是：如何通过检索增强生成（RAG）把本地结构化知识库与 LLM 结合，实现"可回答问题准确作答、不可回答问题正确拒答、易混淆问题正确区分"三类能力，并通过冻结测试集量化各方案的增益。

## 二、最低完成要求

- [x] Baseline / 基础系统（无RAG直答基线 + 基础RAG系统）
- [x] 核心方法或关键机制（检索增强生成 RAG：切分→嵌入→检索→生成）
- [x] 对比实验（无RAG vs RAG-BM25 vs RAG-向量，120题冻结测试集）
- [ ] 消融/性能测试（切分粒度、top_k、去重、混合检索——下一步）
- [x] 错误或异常情况分析（已完成初版问题归因，见报告与 results/summary.md）
- [ ] 完整毕业论文（撰写中）

## 三、拓展目标

- [ ] 重排序（Rerank）：对 top-k 二次排序，修复字段类检索错位
- [ ] 实体消歧：区分黑塔/大黑塔、三月七/仙舟三月七等相似实体
- [ ] 混合检索（向量 + BM25）与参数消融
- [ ] 可演示的交互问答系统

## 四、技术路线

总体流程：整理游戏知识库（CSV）→ 构建冻结测试集（120题，三类）→ 实现基础 RAG（文档切分/嵌入/检索/生成）→ 实现无RAG基线 → 在冻结测试集上对比评测 → 错误归因与迭代改进 → 形成论文实验章节。

详见：[docs/01-topic/technical_route.md](docs/01-topic/technical_route.md)

## 五、当前进展

- **当前阶段**：已完成测试集与基础 RAG 系统，三方案完整评测通过。
- **最近完成**：120 题冻结测试集（可回答45/不能回答40/易混淆35）；基础 RAG（字段级切分、bge-small-zh-v1.5 嵌入、向量/BM25 检索、DeepSeek 生成）；无RAG基线；三方案对比评测与初步错误归因。
- **当前问题**：字段级切块下"属性类"问题系统性召回错位（核心瓶颈）；多值字段拆块导致回答不完整/矛盾；易混淆区分中 BM25 明显弱于向量；评测字符串比对口径过严。
- **下一步**：检索层查询改写与重排序、多值字段保留完整、实体消歧、放宽评测口径、补齐消融实验。

## 六、主要实验结果

评测于 120 题冻结测试集（`data/samples/testset_2027-BS_v1.json`，deepseek-flash 生成）：

| Experiment | Result | Status |
|---|---|---|
| 无RAG基线（总体准确率） | 0.333 | ✅ 完成 |
| RAG-BM25（总体准确率） | 0.750 | ✅ 完成 |
| RAG-向量（总体准确率） | **0.808** | ✅ 完成 |
| 无RAG 拒答率（不能回答类，40题） | 0.000 | ✅ 完成 |
| RAG-向量 拒答率 | 0.950 | ✅ 完成 |
| RAG-BM25 / RAG-向量 知识命中率 | 0.822 / 0.800 | ✅ 完成 |
| 消融实验（切分/top_k/去重/混合） | — | ⏳ 待做 |

要点：RAG 相对无RAG 显著提升总体准确率与拒答能力（防幻觉）；BM25 字面精确、向量语义区分更强。详见 `results/summary.md`。

## 七、仓库目录说明

```
configs/          RAG 与实验配置（rag.yaml）
data/             数据（metadata 元信息、samples 测试集）
docs/             文档（01选题 / 02文献 / 03设计 / 04会议）
evaluation/       评测代码与指标（run_eval.py / metrics.py / verify_testset.py）
experiments/      实验（baseline 无RAG基线、exp01/exp02）
knowledge_base/   游戏知识库（立绘 / 角色数据csv / 角色数据txt）
progress/         进度（issues / milestones / weekly_log）
results/          结果（checkpoints 索引 / figures / logs / tables / summary.md）
scripts/          脚本（1_data_prep / 2_build_index / 3_run）
src/rag/          基础 RAG 源码（documents/embed/retriever/generator/rag/config）
thesis/           论文（outline、drafts、figures、references、tables）
```

## 八、本人主要贡献

- **数据**：手工整理《崩坏：星穹铁道》官方开放 Wiki 角色数据为 8 个 CSV（角色基础信息/光锥/遗器/配队/行迹/星魂/晋阶/故事）；设计并冻结 120 题三类测试集（可回答/不能回答/易混淆），参考答案逐条对照知识库核验。
- **代码**：实现基础 RAG 全链路（`src/rag/`：CSV 字段级切分与去重、bge-small-zh-v1.5 本地嵌入、向量/BM25/混合检索、DeepSeek 生成、配置与提示词分离）；实现无RAG基线（`experiments/baseline/`）；编写建索引、交互问答、评测、测试集校验脚本。
- **实验**：完成无RAG、RAG-BM25、RAG-向量三方案在冻结测试集上的完整评测与初步错误归因，产出 `results/summary.md` 与明细表。
- **论文**：撰写实验设计文档（`docs/03-design/experiment_design.md`）与《Baseline 与问题分析报告》（`results/baseline_report.docx`）。

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
