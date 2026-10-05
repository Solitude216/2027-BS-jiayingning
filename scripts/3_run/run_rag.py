# -*- coding: utf-8 -*-
"""基础 RAG 交互问答：python scripts/3_run/run_rag.py [-q "问题"] [--no-rag]"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from src.rag import RAG


def main():
    args = sys.argv[1:]
    question = None
    no_rag = "--no-rag" in args
    for i, a in enumerate(args):
        if a == "-q" and i + 1 < len(args):
            question = args[i + 1]
    rag = RAG()
    rag.build_index()
    if question:
        res = rag.answer(question, with_context=not no_rag)
        print("问题:", res["question"])
        print("答案:", res["answer"])
        print("检索片段:", res["n_retrieved"])
        for r in res["retrieved"]:
            print("   -", r)
        return
    print("进入交互问答（输入 exit 退出）。")
    while True:
        try:
            q = input("\n问题: ").strip()
        except EOFError:
            break
        if not q or q.lower() == "exit":
            break
        res = rag.answer(q, with_context=not no_rag)
        print("答案:", res["answer"])
        print("命中片段数:", res["n_retrieved"])


if __name__ == "__main__":
    main()
