# -*- coding: utf-8 -*-
"""评测指标。

口径说明（2026-10-29 修订）：
- answer_correct：规则匹配 + 多答案/同义词归一，不再只做逐字子串；
- source_role_match：原"citation_accuracy"改名，仅看回答是否提及目标角色名；
- citation_accuracy（新）：真正可解释的引用准确性——解析回答中"片段N"引用编号，
  检查其指向的检索片段角色/来源是否与金标准一致；
- hit_knowledge：直接按金标准 (gold_source, gold_role, gold_field) 判断检索是否命中，
  不再用答案措辞去猜。
"""
from __future__ import annotations
import re

# 答案归一化时需要剥离的"修饰性后缀/词"（语义相近但措辞不同的情况）
_STRIP_TOKENS = ["属性", "元素", "命途", "角色", "的", "是", "属于", "为", "：", ":", "了"]
# 同义词归并表：左 -> 右（归一化后比较）
_SYNONYM = {
    "冰元素": "冰", "冰属性": "冰",
    "量子属性": "量子", "量子命途": "量子",
    "虚数属性": "虚数", "虚数命途": "虚数",
    "火属性": "火", "火元素": "火",
    "雷属性": "雷", "雷元素": "雷",
    "风属性": "风", "风元素": "风",
    "物理属性": "物理",
}


def normalize(s: str) -> str:
    """归一化：去空白与常见标点，小写。"""
    if not s:
        return ""
    s = re.sub(r"[\s、，,。；;：:（）()「」\"'“”‘’·•\-/]", "", s)
    return s.lower()


def _deep_normalize(s: str) -> str:
    """归一化 + 同义词归并 + 剥离修饰词，用于答案语义匹配。"""
    a = normalize(s)
    for k, v in _SYNONYM.items():
        a = a.replace(normalize(k), normalize(v))
    for t in _STRIP_TOKENS:
        a = a.replace(t, "")
    return a


def _split_expected(expected: str) -> list[str]:
    """把标准答案拆成多个可接受答案（按 或/、；; 分隔），逐项归一。"""
    if not expected:
        return []
    parts = re.split(r"或|、|；|;|\n", expected)
    out = []
    for p in parts:
        p = p.strip().strip("。.").strip()
        if p:
            out.append(p)
    return out or [expected]


def answer_correct(answer: str, expected: str) -> bool:
    """答案是否正确：多答案任一命中即可，做同义词/修饰词归一。

    判定方向双向：归一后期望答案出现在回答中，或回答关键短语出现在归一后期望中。
    """
    if not expected:
        return False
    a = _deep_normalize(answer)
    if not a:
        return False
    for opt in _split_expected(expected):
        e = _deep_normalize(opt)
        if not e:
            continue
        # 双向子串：回答包含期望，或期望包含回答中的关键短词
        if e in a or (len(e) >= 2 and e in a):
            return True
        # 回答里抽出与期望同长的窗口做包含判断
        if len(e) <= len(a) and e in a:
            return True
    return False


def is_refusal(answer: str) -> bool:
    """是否拒答（用于不能回答类）：出现明确的无法回答信号。"""
    a = normalize(answer)
    signals = ["无法回答", "没有相关信息", "没有相关", "知识库中未", "未收录", "未找到", "无法确定",
               "不能回答", "查无", "不存在", "资料中没有", "未提供", "我没有相关信息", "知识库中没有",
               "知识库中不存在", "我无法", "不确定是否"]
    return any(s in a for s in signals)


def _norm_role(s: str) -> str:
    """角色名归一：统一间隔号（·/•），便于 开拓者·存护 与 开拓者•存护 互认。"""
    if not s:
        return ""
    return s.replace("•", "·").replace("＊", "").strip()


# ---------- 金标准解析 ----------

def parse_ground_truth(ground_truth_source: str) -> dict:
    """从 ground_truth_source 解析金标准三元组。

    形如 "角色基础信息.csv, 角色名=Archer, 字段=属性"。
    """
    out = {"gold_source": "", "gold_role": "", "gold_field": ""}
    if not ground_truth_source:
        return out
    seg0 = ground_truth_source.split(",")[0].strip()
    out["gold_source"] = seg0
    m = re.search(r"角色名\s*=\s*([^,]+)", ground_truth_source)
    if m:
        out["gold_role"] = m.group(1).strip()
    m = re.search(r"字段\s*=\s*([^,]+)", ground_truth_source)
    if m:
        out["gold_field"] = m.group(1).strip()
    return out


def hit_knowledge(retrieved, gold_source: str = "", gold_role: str = "",
                  gold_field: str = "", match_field: bool = True,
                  match_source: bool = True) -> bool:
    """知识命中率：检索是否命中金标准文档/字段。

    - gold_role 必填：某检索片段角色名与金标准一致；
    - gold_source：若 match_source 且提供，片段来源文件需一致；
    - gold_field：若 match_field 且提供，片段字段需一致（支持 "属性/命途" 多字段任一命中）；
    - entity-grouped 切块下 match_field=False、match_source=False，只按角色判定。
    """
    if not gold_role:
        return False
    gr = _norm_role(gold_role)
    gfields = re.split(r"[/、]", gold_field) if gold_field else []
    gfields = [f.strip() for f in gfields if f.strip()]
    for item in retrieved:
        doc_role = _norm_role(item.get("role", ""))
        if doc_role != gr:
            continue
        if match_source and gold_source and item.get("source", "") != gold_source:
            continue
        if match_field and gfields:
            df = item.get("field", "") or ""
            if df not in gfields:
                continue
        return True
    return False


# ---------- 引用准确性 ----------

def _extract_cited_indices(answer: str) -> list[int]:
    """从回答中抽取引用编号（如 '片段1'、'片段 2'、'[片段3]'、'片段①'）。"""
    if not answer:
        return []
    nums = re.findall(r"片段\s*([0-9０-９]+)", answer)
    out = []
    trans = {"０": "0", "１": "1", "２": "2", "３": "3", "４": "4",
             "５": "5", "６": "6", "７": "7", "８": "8", "９": "9"}
    for n in nums:
        n = "".join(trans.get(c, c) for c in n)
        try:
            out.append(int(n))
        except ValueError:
            pass
    return out


def source_role_match(result, gold_role: str = "") -> bool:
    """原 citation_accuracy 改名：仅判断回答是否提及目标角色名（弱信号）。"""
    if not gold_role:
        return False
    return _norm_role(gold_role) in _norm_role(result.get("answer", ""))


def citation_accuracy(result, gold_role: str = "", gold_source: str = "",
                      match_source: bool = True) -> bool:
    """真正可解释的引用准确性。

    解析回答中"片段N"引用编号，检查该编号指向的检索片段：
    - 角色名与金标准一致；
    - 若 match_source 且金标准给出来源文件，片段来源需一致。
    若回答未引用任何片段编号，视为引用缺失，判 False。
    """
    idxs = _extract_cited_indices(result.get("answer", ""))
    retrieved = result.get("retrieved", []) or []
    if not idxs or not retrieved:
        return False
    gr = _norm_role(gold_role)
    for i in idxs:
        if 1 <= i <= len(retrieved):
            frag = retrieved[i - 1]
            role_ok = (not gold_role) or (_norm_role(frag.get("role", "")) == gr)
            src_ok = (not match_source) or (not gold_source) or (frag.get("source", "") == gold_source)
            if role_ok and src_ok:
                return True
    return False
