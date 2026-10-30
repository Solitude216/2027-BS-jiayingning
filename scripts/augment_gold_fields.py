# -*- coding: utf-8 -*-
"""为冻结测试集补充金标准字段 gold_source/gold_role/gold_field。

只新增元数据字段，不改动题目、参考答案与分类。运行一次后写回原文件。
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from evaluation.metrics import parse_ground_truth

PATH = os.path.join(ROOT, "data", "samples", "testset_2027-BS_v1.json")


def main():
    with open(PATH, encoding="utf-8") as f:
        data = json.load(f)
    n_add = 0
    for q in data["questions"]:
        gts = q.get("ground_truth_source", "")
        g = parse_ground_truth(gts)
        # 只补空字段，不覆盖已有
        for k in ("gold_source", "gold_role", "gold_field"):
            if k not in q:
                q[k] = g.get(k, "")
        if g["gold_role"]:
            n_add += 1
    data["gold_fields_added"] = "gold_source, gold_role, gold_field (2026-10-29)"
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"已为 {n_add} 题补充金标准字段，写回 {PATH}")


if __name__ == "__main__":
    main()
