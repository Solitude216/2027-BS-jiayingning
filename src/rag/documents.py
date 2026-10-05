# -*- coding: utf-8 -*-
"""文档加载与分块：将 knowledge_base/角色数据csv 下的 CSV 转为带来源标签的文档块。"""
from __future__ import annotations
import csv, os
from typing import Iterator


class Doc:
    __slots__ = ("id", "text", "source", "role", "field")

    def __init__(self, id: str, text: str, source: str, role: str = "", field: str = ""):
        self.id = id
        self.text = text
        self.source = source      # 例如 角色基础信息.csv
        self.role = role          # 角色名
        self.field = field        # 字段/子类型

    def meta(self) -> dict:
        return {"source": self.source, "role": self.role, "field": self.field}


def _clean(v):
    if v is None:
        return ""
    return str(v).strip()


def load_rows(csv_dir: str) -> Iterator[dict]:
    """逐个读取目录下的所有 CSV 文件，产出原始行 dict（含 file 名）。"""
    for fn in sorted(os.listdir(csv_dir)):
        if not fn.lower().endswith(".csv"):
            continue
        path = os.path.join(csv_dir, fn)
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                yield {"file": fn, **row}


def build_documents(csv_dir: str, per_row: bool = True, with_header: bool = True,
                    mode: str = "row", dedup: bool = True) -> list[Doc]:
    """将 CSV 数据转为文档块。

    - mode="row"：每个 CSV 行独立成块（字段全量拼接）；
    - mode="field"：字段级切块，每个 (角色, 字段) 独立成短文档，利于字段类问题的精确召回。
    - with_header=True：把表头字段名拼进文本，增强字段语义（利于检索命中考题字段）。
    - dedup=True：按文本内容去重（相同文本只保留一条），避免重复行污染检索。
    """
    docs: list[Doc] = []
    seen = set()
    seen_text = set()
    for raw in load_rows(csv_dir):
        fn = raw["file"]
        role = _clean(raw.get("角色名", ""))
        if mode == "field":
            for k, v in raw.items():
                if k == "file" or k == "角色名":
                    continue
                v = _clean(v)
                if not v:
                    continue
                text = f"角色名：{role}；{k}：{v}"
                if dedup and text in seen_text:
                    continue
                seen_text.add(text)
                uid = f"{fn}|{role}|{k}"
                n = 1
                while f"{uid}#{n}" in seen:
                    n += 1
                uid = f"{uid}#{n}"
                seen.add(uid)
                docs.append(Doc(id=uid, text=text, source=fn, role=role, field=k))
            continue
        # mode="row"
        key_fields = [k for k in raw.keys() if k != "file" and k != "角色名" and _clean(raw.get(k))]
        if per_row:
            parts = [f"{_clean(raw.get(k))}" for k in raw if k != "file"]
            text = "、".join(p for p in parts if p)
            if with_header:
                labeled = []
                for k, v in raw.items():
                    if k == "file":
                        continue
                    v = _clean(v)
                    if v:
                        labeled.append(f"{k}：{v}")
                text = "；".join(labeled)
            if dedup and text in seen_text:
                continue
            seen_text.add(text)
            uid = f"{fn}|{role}|{key_fields[0] if key_fields else ''}"
            n = 1
            while f"{uid}#{n}" in seen:
                n += 1
            uid = f"{uid}#{n}"
            seen.add(uid)
            field = key_fields[0] if key_fields else ""
            docs.append(Doc(id=uid, text=text, source=fn, role=role, field=field))
    return docs


def chunk_stats(docs: list[Doc]) -> dict:
    from collections import Counter
    by_src = Counter(d.source for d in docs)
    total_chars = sum(len(d.text) for d in docs)
    return {
        "n_docs": len(docs),
        "by_source": dict(by_src),
        "avg_chars": round(total_chars / len(docs), 1) if docs else 0,
    }
