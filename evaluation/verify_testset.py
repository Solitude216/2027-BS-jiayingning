# -*- coding: utf-8 -*-
"""测试集质量核查：校验 JSON 结构、类别数量，并把可回答/易混淆题参考答案对照知识库 CSV 核实。

用法：
    python evaluation/verify_testset.py
"""
import json, csv, os, re, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TS = os.path.join(ROOT, "data", "samples", "testset_2027-BS_v1.json")
KB = os.path.join(ROOT, "knowledge_base", "角色数据csv")


def load(name):
    with open(os.path.join(KB, name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def norm(s):
    return re.sub(r"[\s、，,。；;：:（）()「」\"'“”‘’]", "", s or "")


def main():
    d = json.load(open(TS, encoding="utf-8"))
    qs = d["questions"]
    cnt = Counter(q["category"] for q in qs)
    print("total:", len(qs), "| by category:", dict(cnt))
    print("frozen:", d["frozen"], "| frozen_date:", d["frozen_date"])

    tables = {fn: load(fn) for fn in os.listdir(KB) if fn.endswith(".csv")}
    basic = {r["角色名"]: r for r in tables["角色基础信息.csv"]}

    def lookup(fname, key, field, pos=""):
        if fname == "角色基础信息.csv":
            return basic.get(key, {}).get(field, "<missing>")
        if fname == "遗器推荐.csv":
            rows = [r for r in tables[fname] if r["角色名"] == key]
            return rows[0].get(field, "<missing>") if rows else "<missing>"
        if fname == "光锥推荐.csv":
            rows = [r for r in tables[fname] if r["角色名"] == key]
            return "；".join(r["光锥名称"] for r in rows) if rows else "<missing>"
        if fname == "配队推荐.csv":
            rows = [r for r in tables[fname] if r["角色名"] == key and r["位置"] == pos]
            return "；".join(r["推荐角色"] for r in rows) if rows else "<missing>"
        return "<check-manual>"

    errs = []
    for q in qs:
        if q["category"] not in ("answerable", "confusable"):
            continue
        s = q["ground_truth_source"]
        fname = s.split(",")[0].strip()
        m_key = re.search(r"角色名=([^,\s]+)", s)
        m_field = re.search(r"字段=([^\s]+)", s)
        m_pos = re.search(r"位置=([^\s]+)", s)
        key = m_key.group(1) if m_key else ""
        field = m_field.group(1) if m_field else ""
        pos = m_pos.group(1) if m_pos else ""
        if not field:
            for label in ("光锥名称", "隧洞遗器", "位面饰品"):
                if label in s:
                    field = label
                    break
        val = lookup(fname, key, field, pos)
        ok = norm(q["expected_answer"]) in norm(val)
        # 组合字段（如 属性/命途）：拆分后逐字段核对是否都出现在期望答案中
        if not ok and "/" in field:
            parts = [f for f in field.split("/") if f]
            vals = [lookup(fname, key, f, pos) for f in parts]
            ok = bool(vals) and all(norm(v) and norm(v) in norm(q["expected_answer"]) for v in vals)
        if not ok:
            errs.append((q["id"], key, field, q["expected_answer"], val))

    print(f"\ngrounded check (answerable+confusable): {len(qs)-cnt['unanswerable']} 题, 不一致 {len(errs)} 处")
    for e in errs:
        print("  MISMATCH:", e)
    ids = [q["id"] for q in qs]
    print("duplicate ids:", len(ids) - len(set(ids)))


if __name__ == "__main__":
    main()
