# -*- coding: utf-8 -*-
"""检索器：支持 向量(vector) / 词法BM25(bm25) / 混合(hybrid) 三种检索。"""
from __future__ import annotations
import json, math, os
from collections import Counter
import numpy as np
from .documents import Doc
from .embed import Embedder

# BGE 官方对查询侧推荐的指令前缀（中文检索）
_BGE_QUERY_INSTRUCTION = "为这个句子生成表示以用于检索相关文章："


class BM25:
    """基于 jieba 分词的 BM25（OKAPI），纯 Python 实现。"""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs: list[Doc] = []
        self._token_lists: list[list[str]] = []
        self._df: Counter = Counter()
        self._avgdl = 0.0
        self._idf: dict[str, float] = {}

    def fit(self, docs: list[Doc]):
        import jieba
        self.docs = docs
        self._token_lists = [jieba.lcut(d.text) for d in docs]
        lens = [len(t) for t in self._token_lists]
        self._avgdl = sum(lens) / len(lens) if lens else 0.0
        for tl in self._token_lists:
            for term in set(tl):
                self._df[term] += 1
        n = len(docs)
        self._idf = {
            term: math.log((n - df + 0.5) / (df + 0.5) + 1)
            for term, df in self._df.items()
        }

    def _score(self, query_terms: list[str], tl: list[str], dl: int) -> float:
        tf = Counter(tl)
        s = 0.0
        for t in set(query_terms):
            if t in self._idf:
                f = tf.get(t, 0)
                s += self._idf[t] * (f * (self.k1 + 1)) / (f + self.k1 * (1 - self.b + self.b * dl / self._avgdl))
        return s

    def retrieve(self, query: str, top_k: int) -> list[tuple[int, float]]:
        import jieba
        qt = jieba.lcut(query)
        scored = []
        for i, (tl, d) in enumerate(zip(self._token_lists, self.docs)):
            s = self._score(qt, tl, len(tl))
            if s > 0:
                scored.append((i, s))
        scored.sort(key=lambda x: -x[1])
        return scored[:top_k]


class Retriever:
    def __init__(self, method: str = "vector", top_k: int = 5, model_dir: str | None = None):
        self.method = method
        self.top_k = top_k
        self.docs: list[Doc] = []
        self._doc_vecs: np.ndarray | None = None
        self._embedder = Embedder(model_dir=model_dir) if method in ("vector", "hybrid") else None
        self._bm25: BM25 | None = None

    # ---------- 索引 ----------
    def build_index(self, docs: list[Doc]):
        self.docs = docs
        if self.method in ("vector", "hybrid"):
            texts = [d.text for d in docs]
            vecs = self._embedder.encode(texts)
            self._doc_vecs = np.asarray(vecs, dtype=np.float32)
        if self.method in ("bm25", "hybrid"):
            self._bm25 = BM25()
            self._bm25.fit(docs)

    def save_index(self, path: str):
        os.makedirs(path, exist_ok=True)
        doc_meta = [{"id": d.id, "source": d.source, "role": d.role, "field": d.field, "text": d.text} for d in self.docs]
        with open(os.path.join(path, "docs.json"), "w", encoding="utf-8") as f:
            json.dump(doc_meta, f, ensure_ascii=False)
        if self._doc_vecs is not None:
            np.save(os.path.join(path, "vectors.npy"), self._doc_vecs)

    def load_index(self, path: str):
        with open(os.path.join(path, "docs.json"), encoding="utf-8") as f:
            meta = json.load(f)
        self.docs = [Doc(**{k: m[k] for k in ("id", "text", "source", "role", "field")}) for m in meta]
        vp = os.path.join(path, "vectors.npy")
        if os.path.exists(vp):
            self._doc_vecs = np.load(vp)

    # ---------- 检索 ----------
    def retrieve(self, query: str, top_k: int | None = None) -> list[tuple[Doc, float]]:
        k = top_k or self.top_k
        if self.method == "vector":
            qv = np.asarray(self._embedder.encode([_BGE_QUERY_INSTRUCTION + query])[0], dtype=np.float32)
            sims = self._doc_vecs @ qv
            idxs = np.argsort(-sims)[:k]
            return [(self.docs[i], float(sims[i])) for i in idxs]
        if self.method == "bm25":
            hits = self._bm25.retrieve(query, k)
            return [(self.docs[i], s) for i, s in hits]
        if self.method == "hybrid":
            qv = np.asarray(self._embedder.encode([_BGE_QUERY_INSTRUCTION + query])[0], dtype=np.float32)
            sims = self._doc_vecs @ qv
            v_rank = {i: r for r, i in enumerate(np.argsort(-sims))}
            hits = self._bm25.retrieve(query, k * 3)
            bm = {i: s for i, s in hits}
            # 对交集做归一化加权
            best_bm = max(bm.values()) if bm else 1.0
            best_v = float(sims.max()) if len(sims) else 1.0
            scores = {}
            for i, s in bm.items():
                scores[i] = 0.5 * (s / best_bm) + 0.5 * (float(sims[i]) / best_v)
            # 补上仅向量命中
            for r, i in enumerate(np.argsort(-sims)[:k * 3]):
                if i not in scores:
                    scores[i] = 0.5 * (float(sims[i]) / best_v)
            ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
            return [(self.docs[i], s) for i, s in ranked]
        raise ValueError(self.method)
