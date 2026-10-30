# -*- coding: utf-8 -*-
"""跑完整实验矩阵，输出固定文件名的明细 JSON 到 results/tables/。

配置：
  no_rag                无检索基线
  vector_field_k5      向量+字段级+top5（主）
  bm25_field_k5         BM25+字段级+top5
  hybrid_field_k5       RRF混合+字段级+top5
  vector_row_k5         向量+整行+top5（切块对比）
  vector_entity_k5      向量+实体聚合+top5（切块对比，命中按角色）
  vector_field_k3       向量+字段级+top3（top-k扫描）
  vector_field_k10      向量+字段级+top10（top-k扫描）
  vector_field_k5_ec    向量+字段级+top5+实体约束（消歧）
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from evaluation.run_eval import evaluate, load_testset

TS = os.path.join(ROOT, "data", "samples", "testset_2027-BS_v1.json")

CONFIGS = [
    dict(tag="no_rag",               method="vector", no_rag=True,  chunk_mode="field",  top_k=5,  entity_constraint=False, match_role_only=False),
    dict(tag="vector_field_k5",      method="vector", no_rag=False, chunk_mode="field",  top_k=5,  entity_constraint=False, match_role_only=False),
    dict(tag="bm25_field_k5",        method="bm25",   no_rag=False, chunk_mode="field",  top_k=5,  entity_constraint=False, match_role_only=False),
    dict(tag="hybrid_field_k5",      method="hybrid", no_rag=False, chunk_mode="field",  top_k=5,  entity_constraint=False, match_role_only=False),
    dict(tag="vector_row_k5",        method="vector", no_rag=False, chunk_mode="row",    top_k=5,  entity_constraint=False, match_role_only=False),
    dict(tag="vector_entity_k5",     method="vector", no_rag=False, chunk_mode="entity", top_k=5,  entity_constraint=False, match_role_only=True),
    dict(tag="vector_field_k3",      method="vector", no_rag=False, chunk_mode="field",  top_k=3,  entity_constraint=False, match_role_only=False),
    dict(tag="vector_field_k10",     method="vector", no_rag=False, chunk_mode="field",  top_k=10, entity_constraint=False, match_role_only=False),
    dict(tag="vector_field_k5_ec",   method="vector", no_rag=False, chunk_mode="field",  top_k=5,  entity_constraint=True,  match_role_only=False),
]


def main():
    testset = load_testset(TS)
    summary = {}
    for cfg in CONFIGS:
        tag = cfg.pop("tag")
        print(f"\n===== {tag} =====", flush=True)
        t0 = time.time()
        try:
            out, _ = evaluate(testset, out_name=f"matrix_{tag}.json", **cfg)
            s = out["stats"]
            summary[tag] = {
                "overall_acc": s["overall"]["overall_accuracy"],
                "answerable": s["answerable"].get("answer_accuracy"),
                "unanswerable": s["unanswerable"].get("answer_accuracy"),
                "confusable": s["confusable"].get("answer_accuracy"),
                "hit_rate": s["overall"].get("hit_rate"),
                "citation_acc": s["overall"].get("citation_accuracy"),
            }
            print(json.dumps(summary[tag], ensure_ascii=False), flush=True)
        except Exception as e:
            import traceback
            traceback.print_exc()
            summary[tag] = {"error": str(e)}
        print(f"  耗时 {time.time()-t0:.0f}s", flush=True)
    out_path = os.path.join(ROOT, "results", "tables", "matrix_summary.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print("\n汇总:", out_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
