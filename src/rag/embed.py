# -*- coding: utf-8 -*-
"""嵌入封装：加载本地 BGE 中文模型（sentence-transformers），对文本向量化。"""
from __future__ import annotations
import os


class Embedder:
    def __init__(self, model_dir: str | None = None):
        self.model_dir = model_dir or os.environ.get(
            "EMBED_MODEL_DIR", r"C:\毕业论文\models\bge-small-zh-v1.5"
        )
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        from sentence_transformers import SentenceTransformer
        # 使用本地模型目录，离线加载，避免联网
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        self._model = SentenceTransformer(self.model_dir)
        return self._model

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        model = self._load()
        vecs = model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
        return [v.tolist() for v in vecs]
