# -*- coding: utf-8 -*-
"""从已保存的 matrix_*.json 明细重算指标并汇总主结果表。

- field/row 切块：hit/cite 按 (source, role, field) 严格判定；
- entity 切块：role-only 判定（source/field 不可比，跳过）；
- 不重跑 LLM，只读明细 JSON。
"""
import os, sys, json, glob
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from evaluation.metrics import hit_knowledge, citation_accuracy

TABLES = os.path.join(ROOT, "results", "tables")

# 配置展示顺序与友好名
ORDER = [
    ("matrix_no_rag.json",            "no_rag",               "无RAG（纯LLM）",            "—"),
    ("matrix_vector_field_k5.json",    "vector_field_k5",      "向量·field·k5",            "field"),
    ("matrix_bm25_field_k5.json",      "bm25_field_k5",        "BM25·field·k5",            "field"),
    ("matrix_hybrid_field_k5.json",   "hybrid_field_k5_rrf",  "混合RRF·field·k5",         "field"),
    ("matrix_vector_row_k5.json",      "vector_row_k5",        "向量·row·k5",              "row"),
    ("matrix_vector_entity_k5.json",  "vector_entity_k5",      "向量·entity-grouped·k5",   "entity"),
    ("matrix_vector_field_k3.json",    "vector_field_k3",      "向量·field·k3",            "field"),
    ("matrix_vector_field_k10.json",   "vector_field_k10",      "向量·field·k10",           "field"),
]
# EC 单独文件（命名不是 matrix_ 前缀）
EC_FILE = os.path.join(TABLES, "eval_vector_field_k5_ec_20261030_131904.json")
EC_ENTRY = ("eval_vector_field_k5_ec_20261030_131904.json", "vector_field_k5_ec", "向量·field·k5·实体约束", "field")


def agg(rows):
    out = {}
    for cat in ("answerable", "unanswerable", "confusable"):
        rs = [r for r in rows if r["category"] == cat]
        n = len(rs)
        if not n:
            out[cat] = {}; continue
        out[cat] = {
            "n": n,
            "acc": round(sum(r["correct"] for r in rs) / n, 4),
            "hit_rate": round(sum(r["hit"] for r in rs) / n, 4),
            "cite": round(sum(r["cite"] for r in rs) / n, 4),
        }
    n = len(rows)
    out["overall"] = {
        "n": n,
        "acc": round(sum(r["correct"] for r in rows) / n, 4),
        "hit_rate": round(sum(r["hit"] for r in rows) / n, 4),
        "cite": round(sum(r["cite"] for r in rows) / n, 4),
    }
    return out


def load_and_recompute(fname, chunk_mode):
    path = os.path.join(TABLES, fname)
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    rows = data["results"]
    role_only = (chunk_mode == "entity")
    for r in rows:
        gsrc = r.get("gold_source", "")
        grole = r.get("gold_role", "")
        gfield = r.get("gold_field", "")
        r["hit"] = hit_knowledge(r["retrieved"], gsrc, grole, gfield,
                                 match_field=not role_only, match_source=not role_only)
        r["cite"] = citation_accuracy(r, grole, gsrc, match_source=not role_only)
    return agg(rows)


def main():
    entries = ORDER + [EC_ENTRY]
    summary = {}
    for fname, key, label, chunk_mode in entries:
        path = os.path.join(TABLES, fname)
        if not os.path.exists(path):
            print(f"[缺失] {fname}")
            continue
        stats = load_and_recompute(fname, chunk_mode)
        summary[key] = {"label": label, "chunk_mode": chunk_mode, "stats": stats}
        o = stats["overall"]
        a = stats.get("answerable", {}).get("acc", "-")
        u = stats.get("unanswerable", {}).get("acc", "-")
        c = stats.get("confusable", {}).get("acc", "-")
        print(f"{label:28s} 总体{o['acc']:.3f}  可答{a}  拒答{u}  易混{c}  命中{o['hit_rate']:.3f}  引用{o['cite']:.3f}")

    out = os.path.join(TABLES, "matrix_summary.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\n汇总已保存:", out)


if __name__ == "__main__":
    main()
