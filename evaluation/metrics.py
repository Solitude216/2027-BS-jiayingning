# -*- coding: utf-8 -*-
"""评测指标：答案正确率、拒答率、易混淆区分率、知识命中率、引用准确率。"""
from __future__ import annotations
import re


def normalize(s: str) -> str:
    """归一化：去空白与常见标点，便于字符串比对。"""
    if not s:
        return ""
    s = re.sub(r"[\s、，,。；;：:（）()「」\"'“”‘’]", "", s)
    return s.lower()


def answer_correct(answer: str, expected: str) -> bool:
    """答案是否正确：期望答案归一化后作为子串出现在回答中。"""
    a = normalize(answer)
    e = normalize(expected)
    if not e:
        return False
    return e in a


def is_refusal(answer: str) -> bool:
    """是否拒答（用于不能回答类）：出现明确的无法回答信号。"""
    a = normalize(answer)
    signals = ["无法回答", "没有相关信息", "没有相关", "知识库中未", "未收录", "未找到", "无法确定",
               "不能回答", "查无", "不存在", "资料中没有", "未提供", "我没有相关信息", "知识库中没有"]
    return any(s in a for s in signals)


def ground_truth_role(question: dict) -> str:
    """从 ground_truth_source 中提取目标角色名（用于知识命中率判定）。"""
    import re as _re
    s = question.get("ground_truth_source", "")
    m = _re.search(r"角色名=([^,\s]+)", s)
    return m.group(1) if m else ""


def hit_knowledge(retrieved, ground_truth_source: str, expected: str) -> bool:
    """知识命中率：检索片段是否命中目标知识。

    - 若给定来源角色名：命中标准为某检索片段角色名一致且文本包含期望答案关键信息；
    - 否则：期望答案归一化后出现在某检索片段文本中。
    """
    role = ground_truth_role({"ground_truth_source": ground_truth_source}) if ground_truth_source else ""
    e = normalize(expected)
    for item in retrieved:
        doc_text = item.get("text", "") or ""
        doc_role = item.get("role", "")
        if role and doc_role == role and e and e in normalize(doc_text):
            return True
        if not role and e and e in normalize(doc_text):
            return True
    return False


def citation_accuracy(result, ground_truth_source: str) -> bool:
    """引用准确性：答案中提到的来源片段与目标来源角色一致。"""
    role = ground_truth_role({"ground_truth_source": ground_truth_source}) if ground_truth_source else ""
    answer = normalize(result.get("answer", ""))
    if not role:
        return False
    return role in answer
