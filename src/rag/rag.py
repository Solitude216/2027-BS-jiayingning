# -*- coding: utf-8 -*-
"""基础 RAG 主管线：检索 + 组装提示词 + 生成答案。"""
from __future__ import annotations
import os
from .documents import build_documents, Doc
from .retriever import Retriever
from .generator import Generator
from .config import load_config

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RAG:
    def __init__(self, config: dict | None = None, use_cache_index: bool = True):
        self.config = config or load_config()
        self.rag_cfg = self.config.get("rag", {})
        ret = self.config.get("retrieval", {})
        self.method = ret.get("method", "vector")
        self.top_k = ret.get("top_k", 5)
        self.model_dir = ret.get("model_dir")
        paths = self.config.get("paths", {})
        def _abs(p, default):
            p = p or default
            return p if os.path.isabs(p) else os.path.join(_ROOT, p)
        self.kb_dir = _abs(paths.get("knowledge_base"),
                           os.path.join(_ROOT, "knowledge_base", "角色数据csv"))
        self.index_dir = _abs(paths.get("index_dir"),
                              os.path.join(_ROOT, "results", "checkpoints", "index"))
        self.test_set = _abs(paths.get("test_set"),
                             os.path.join(_ROOT, "data", "samples", "testset_2027-BS_v1.json"))
        self.out_dir = _abs(paths.get("out_dir"), os.path.join(_ROOT, "results"))
        self.retriever = Retriever(method=self.method, top_k=self.top_k, model_dir=self.model_dir)
        self._llm_cfg = self.config.get("llm", {})
        self.generator = None  # 惰性创建，build_index 不需要 LLM
        if use_cache_index and os.path.exists(os.path.join(self.index_dir, "docs.json")):
            self.retriever.load_index(self.index_dir)
            self._index_loaded = True
        else:
            self._index_loaded = False

    # ---------- 索引 ----------
    def build_index(self, force: bool = False, mode: str | None = None):
        if self._index_loaded and not force:
            return
        mode = mode or self.config.get("chunking", {}).get("mode", "row")
        docs = build_documents(self.kb_dir, mode=mode)
        self.retriever.build_index(docs)
        self.retriever.save_index(self.index_dir)
        self._index_loaded = True
        return docs

    # ---------- 检索 ----------
    def retrieve(self, question: str, top_k: int | None = None):
        if not self._index_loaded:
            self.build_index()
        return self.retriever.retrieve(question, top_k)

    # ---------- 生成 ----------
    def _get_generator(self) -> Generator:
        if self.generator is None:
            llm = self._llm_cfg
            self.generator = Generator(
                model=llm.get("model", "deepseek-flash"),
                base_url=llm.get("base_url", "https://api.deepseek.com"),
                temperature=llm.get("temperature", 0.2),
                max_tokens=llm.get("max_tokens", 512),
                timeout=llm.get("timeout", 60),
            )
        return self.generator

    def answer(self, question: str, with_context: bool = True) -> dict:
        hits = self.retrieve(question)
        if with_context and hits:
            context = "\n\n".join(f"[片段{i+1}](来源:{d.source}, 角色:{d.role or '-'}) {d.text}" for i, (d, s) in enumerate(hits))
        else:
            context = ""
        template = self.rag_cfg.get("prompt_template",
                                    "依据检索片段回答问题：\n{context}\n\n问题：{question}")
        if not with_context:
            template = self.rag_cfg.get("no_rag_prompt_template",
                                        "直接回答下面的问题：\n{question}")
            user_prompt = template.format(question=question)
        else:
            user_prompt = template.format(context=context or "（无检索片段）", question=question)
        answer = self._get_generator().ask(user_prompt)
        return {
            "question": question,
            "answer": answer,
            "retrieved": [
                {"doc_id": d.id, "source": d.source, "role": d.role, "field": d.field,
                 "score": round(s, 4), "text": d.text}
                for d, s in hits
            ],
            "n_retrieved": len(hits),
        }
