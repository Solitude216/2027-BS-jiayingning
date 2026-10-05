# -*- coding: utf-8 -*-
"""无 RAG 基线：直接用 DeepSeek LLM 回答（不检索知识库），对比 RAG 效果。"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
from src.rag.generator import Generator


def main():
    g = Generator()
    while True:
        try:
            q = input("\n问题（无RAG基线）: ").strip()
        except EOFError:
            break
        if not q or q.lower() == "exit":
            break
        ans = g.ask(q)
        print("答案:", ans)


if __name__ == "__main__":
    main()
