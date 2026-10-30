# -*- coding: utf-8 -*-
"""评测运行器：在冻结测试集上运行 RAG（及无RAG基线），输出指标与明细。

用法：
    python evaluation/run_eval.py --method vector --topk 5
    python evaluation/run_eval.py --method hybrid --chunk field
    python evaluation/run_eval.py --method vector --chunk entity --match-role-only
    python evaluation/run_eval.py --no-rag
    python evaluation/run_eval.py --method vector --entity-constraint
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.rag import RAG
from src.rag.documents import load_rows
from evaluation.metrics import (answer_correct, is_refusal, hit_knowledge,
                                source_role_match, citation_accuracy, _norm_role)


def load_testset(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_KNOWN_ROLES_CACHE: list[str] | None = None


def known_roles() -> list[str]:
    """从知识库收集全部角色名（用于从问题中抽实体）。"""
    global _KNOWN_ROLES_CACHE
    if _KNOWN_ROLES_CACHE is not None:
        return _KNOWN_ROLES_CACHE
    kb = os.path.join(ROOT, "knowledge_base", "角色数据csv")
    roles = set()
    for raw in load_rows(kb):
        r = (raw.get("角色名", "") or "").strip()
        if r:
            roles.add(r)
    _KNOWN_ROLES_CACHE = sorted(roles, key=len, reverse=True)
    return _KNOWN_ROLES_CACHE


def extract_entity(question: str) -> str:
    """从问题文本中抽最长匹配的已知角色名（实体约束检索用）。"""
    q = question.replace("•", "·")
    for role in known_roles():
        if _norm_role(role) in q:
            return role
    return ""


def make_rag(method: str, chunk_mode: str, top_k: int = 5, entity_filter: str | None = None) -> RAG:
    from src.rag.retriever import Retriever
    rag = RAG(use_cache_index=False)
    rag.method = method
    rag.top_k = top_k
    rag.retriever = Retriever(method=method, top_k=top_k, entity_filter=entity_filter)
    rag.build_index(mode=chunk_mode)
    return rag


def run_one(rag, q, with_context=True):
    start = time.time()
    res = rag.answer(q["question"], with_context=with_context)
    res["elapsed"] = round(time.time() - start, 2)
    res["category"] = q["category"]
    res["expected"] = q.get("expected_answer")
    res["question"] = q["question"]
    return res


def evaluate(testset, method="vector", no_rag=False, max_q=None, out_name=None,
             chunk_mode="field", top_k=5, entity_constraint=False, match_role_only=False):
    rag = None
    qs = testset["questions"]
    if max_q:
        qs = qs[:max_q]
    results = []
    # 索引只建一次；实体约束只是查询时的过滤器属性，无需重建。
    if rag is None and not no_rag:
        rag = make_rag(method, chunk_mode, top_k=top_k, entity_filter=None)
    for q in qs:
        # 实体约束：按问题抽取实体，仅切换过滤器属性（事后过滤，不重嵌）
        ef = extract_entity(q["question"]) if entity_constraint else None
        if rag is not None:
            rag.retriever.entity_filter = ef
        r = run_one(rag, q, with_context=not no_rag)
        # 金标准
        gsrc = q.get("gold_source", "")
        grole = q.get("gold_role", "")
        gfield = q.get("gold_field", "")
        r["gold_role"] = grole
        r["gold_field"] = gfield
        r["extracted_entity"] = ef
        r["hit"] = hit_knowledge(r["retrieved"], gsrc, grole, gfield,
                                 match_field=not match_role_only,
                                 match_source=not match_role_only)
        r["source_role_match"] = source_role_match(r, grole)
        r["cite"] = citation_accuracy(r, grole, gsrc, match_source=not match_role_only)
        if q["category"] == "unanswerable":
            r["refused"] = is_refusal(r["answer"])
            r["correct"] = r["refused"]
        else:
            r["correct"] = answer_correct(r["answer"], q.get("expected_answer") or "")
        results.append(r)

    stats = {}
    for cat in ("answerable", "unanswerable", "confusable"):
        rs = [r for r in results if r["category"] == cat]
        if not rs:
            stats[cat] = {}
            continue
        n = len(rs)
        correct = sum(1 for r in rs if r.get("correct"))
        hit = sum(1 for r in rs if r.get("hit"))
        cite = sum(1 for r in rs if r.get("cite"))
        stats[cat] = {
            "n": n,
            "correct": correct,
            "answer_accuracy": round(correct / n, 4),
            "hit_rate": round(hit / n, 4),
            "citation_accuracy": round(cite / n, 4),
        }
    total = len(results)
    all_ok = sum(1 for r in results if r.get("correct"))
    all_hit = sum(1 for r in results if r.get("hit"))
    all_cite = sum(1 for r in results if r.get("cite"))
    stats["overall"] = {
        "n": total,
        "overall_accuracy": round(all_ok / total, 4) if total else 0,
        "hit_rate": round(all_hit / total, 4) if total else 0,
        "citation_accuracy": round(all_cite / total, 4) if total else 0,
    }

    out = {
        "testset": testset.get("testset_name"),
        "method": f"{'no-rag' if no_rag else method}",
        "chunk_mode": chunk_mode,
        "top_k": top_k,
        "entity_constraint": entity_constraint,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
        "results": results,
    }
    tag = "norag" if no_rag else method
    ec = "_ec" if entity_constraint else ""
    out_path = os.path.join(ROOT, "results", "tables",
                            out_name or f"eval_{tag}_{chunk_mode}_k{top_k}{ec}_{time.strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out, out_path


def main():
    args = sys.argv[1:]
    method = "vector"
    no_rag = "--no-rag" in args
    max_q = None
    chunk_mode = "field"
    top_k = 5
    entity_constraint = "--entity-constraint" in args
    match_role_only = "--match-role-only" in args
    for i, a in enumerate(args):
        if a == "--method" and i + 1 < len(args):
            method = args[i + 1]
        if a == "--chunk" and i + 1 < len(args):
            chunk_mode = args[i + 1]
        if a == "--max" and i + 1 < len(args):
            max_q = int(args[i + 1])
        if a == "--topk" and i + 1 < len(args):
            top_k = int(args[i + 1])
    ts_path = os.path.join(ROOT, "data", "samples", "testset_2027-BS_v1.json")
    testset = load_testset(ts_path)
    print(f"测试集: {testset['testset_name']} | 总题数: {testset['total']} | 方法: {method} | 切块: {chunk_mode} | top_k: {top_k}")
    out, out_path = evaluate(testset, method=method, no_rag=no_rag, max_q=max_q,
                            chunk_mode=chunk_mode, top_k=top_k,
                            entity_constraint=entity_constraint,
                            match_role_only=match_role_only)
    print("\n指标:", json.dumps(out["stats"], ensure_ascii=False, indent=2))
    print("\n明细已保存:", out_path)


if __name__ == "__main__":
    main()
