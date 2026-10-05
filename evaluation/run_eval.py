# -*- coding: utf-8 -*-
"""评测运行器：在冻结测试集上运行 RAG（及无RAG基线），输出指标与明细。

用法：
    python evaluation/run_eval.py --method vector
    python evaluation/run_eval.py --method bm25
    python evaluation/run_eval.py --method hybrid
    python evaluation/run_eval.py --no-rag
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.rag import RAG
from evaluation.metrics import answer_correct, is_refusal, hit_knowledge, citation_accuracy


def load_testset(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def make_rag(method: str, chunk_mode: str) -> RAG:
    """构造指定检索方法与分块方式的 RAG（强制重建索引，保证方法与索引一致）。"""
    from src.rag.retriever import Retriever
    rag = RAG(use_cache_index=False)
    rag.method = method
    rag.top_k = 5
    rag.retriever = Retriever(method=method, top_k=5)
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


def evaluate(testset, method="vector", no_rag=False, max_q=None, out_name=None, chunk_mode="field"):
    rag = make_rag(method, chunk_mode)
    qs = testset["questions"]
    if max_q:
        qs = qs[:max_q]
    results = []
    for q in qs:
        r = run_one(rag, q, with_context=not no_rag)
        r["hit"] = hit_knowledge(r["retrieved"], q.get("ground_truth_source", ""), q.get("expected_answer") or "")
        r["cite"] = citation_accuracy(r, q.get("ground_truth_source", ""))
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
        stats[cat] = {
            "n": n,
            "correct": correct,
            "answer_accuracy": round(correct / n, 4),
            "hit_rate": round(hit / n, 4),
        }
    total = len(results)
    all_ok = sum(1 for r in results if r.get("correct"))
    stats["overall"] = {"n": total, "overall_accuracy": round(all_ok / total, 4) if total else 0}

    out = {
        "testset": testset.get("testset_name"),
        "method": f"{'no-rag' if no_rag else method}",
        "chunk_mode": chunk_mode,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "stats": stats,
        "results": results,
    }
    tag = "norag" if no_rag else method
    out_path = os.path.join(ROOT, "results", "tables",
                            out_name or f"eval_{tag}_{chunk_mode}_{time.strftime('%Y%m%d_%H%M%S')}.json")
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
    for i, a in enumerate(args):
        if a == "--method" and i + 1 < len(args):
            method = args[i + 1]
        if a == "--chunk" and i + 1 < len(args):
            chunk_mode = args[i + 1]
        if a == "--max" and i + 1 < len(args):
            max_q = int(args[i + 1])
    ts_path = os.path.join(ROOT, "data", "samples", "testset_2027-BS_v1.json")
    testset = load_testset(ts_path)
    print(f"测试集: {testset['testset_name']} | 总题数: {testset['total']}")
    out, out_path = evaluate(testset, method=method, no_rag=no_rag, max_q=max_q, chunk_mode=chunk_mode)
    print("\n指标:", json.dumps(out["stats"], ensure_ascii=False, indent=2))
    print("\n明细已保存:", out_path)


if __name__ == "__main__":
    main()
