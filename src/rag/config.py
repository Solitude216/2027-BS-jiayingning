# -*- coding: utf-8 -*-
"""配置加载：读取 configs/rag.yaml。"""
from __future__ import annotations
import os
import yaml


_DEFAULT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        "configs", "rag.yaml")


def load_config(path: str | None = None) -> dict:
    p = path or _DEFAULT
    if not os.path.exists(p):
        return {}
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}
