# -*- coding: utf-8 -*-
"""构建检索索引：加载知识库 CSV -> 分块 -> 向量化 -> 保存到 results/checkpoints/index。"""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from src.rag import RAG
from src.rag.documents import build_documents, chunk_stats

def main():
    rag = RAG()
    print("知识库目录:", rag.kb_dir)
    mode = rag.config.get("chunking", {}).get("mode", "row")
    print("分块模式:", mode)
    docs = build_documents(rag.kb_dir, mode=mode)
    print("文档块统计:", chunk_stats(docs))
    print("正在构建索引（向量化...）")
    rag.retriever.build_index(docs)
    rag.retriever.save_index(rag.index_dir)
    print("索引已保存到:", rag.index_dir)
    # 冒烟测试：检索两个问题
    for q in ["三月七的属性是什么？", "万敌的神权是什么？", "开拓者·毁灭的属性是什么？"]:
        hits = rag.retriever.retrieve(q, top_k=3)
        print(f"\nQ: {q}")
        for d, s in hits[:3]:
            print(f"  [{s:.4f}] ({d.source}|{d.role}|{d.field}) {d.text[:80]}")

if __name__ == "__main__":
    main()
