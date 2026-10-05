# -*- coding: utf-8 -*-
"""
脚本 4/8：将知识库角色 txt 中的角色晋阶信息解析为《角色晋阶.csv》。

CSV 列：角色名, 晋阶阶段, 所需材料
说明：
  - 每个角色固定 8 个晋阶阶段（1级属性/晋阶所需材料、20级…70级晋阶），
    每个阶段一行。
  - 晋阶阶段保留源文件中的标题原文，所需材料为“所需材料：”后的全部文本。

运行：python 生成角色晋阶csv.py [知识库目录] [输出目录]
"""
import csv
import os
import re
import sys

# ========== 通用解析函数（各脚本一致） ==========

KB_DIR = r"C:\毕业论文\knowledge_base\角色数据txt"
OUT_DIR = r"C:\毕业论文\knowledge_base\角色数据csv"


def list_txt_files(kb_dir: str) -> list:
    names = [f for f in os.listdir(kb_dir) if f.lower().endswith(".txt")]
    return sorted(names)


def read_text(path: str) -> str:
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def extract_name(text: str) -> str:
    m = re.search(r"角色档案\s*——\s*(.+)", text)
    return m.group(1).strip() if m else ""


# 章节级标题白名单：只有这些标题才作为区块切分点，
# 区块内其余行首【…】（如“20级晋阶”子块）原样保留在内容中。
SECTION_TITLES = {
    "星级", "属性", "命途", "阵营", "实装日期", "神权", "个人简介", "角色定位",
    "光锥推荐", "角色晋阶", "角色行迹", "行迹成长消耗材料", "角色星魂",
    "遗器推荐", "配队推荐", "角色立绘",
}


def split_sections(text: str) -> list:
    """
    按“行首【章节标题】”把全文切成 [(标题, 内容), ...]。
    标题与值同行时（如【星级】五星），值取同行剩余部分；
    标题独占一行时（如【角色晋阶】），值取后续所有行（含子块标题）。
    """
    lines = text.splitlines()
    sections = []
    cur_title = None
    cur_lines = []

    def flush():
        if cur_title is not None:
            sections.append((cur_title, "\n".join(cur_lines).strip()))

    for line in lines:
        m = re.match(r"^[ \t]*【([^】]+)】", line)
        if m and m.group(1).strip() in SECTION_TITLES:
            flush()
            cur_title = m.group(1).strip()
            rest = line[m.end():].strip()
            cur_lines = [rest] if rest else []
        else:
            if cur_title is not None:
                cur_lines.append(line)
    flush()
    return sections


def field_value(sections: list, title: str) -> str:
    for t, c in sections:
        if t == title:
            return c
    return ""


# ========== 本脚本主逻辑 ==========

COLUMNS = ["角色名", "晋阶阶段", "所需材料"]

MAT_RE = re.compile(r"所需材料[:：]\s*(.+)")


def parse_promotion(section_text: str) -> list:
    """解析角色晋阶区文本，返回 [(阶段, 材料), ...]"""
    stages = []
    cur_title = ""
    for raw in section_text.splitlines():
        line = raw.strip()
        m = re.match(r"^【(.+?)】$", line)
        if m:                                # 子块标题：1级属性/晋阶所需材料、20级晋阶…
            cur_title = m.group(1).strip()
            continue
        mm = MAT_RE.match(line)
        if mm and cur_title:
            stages.append((cur_title, mm.group(1).strip()))
    return stages


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)
        prom_text = field_value(secs, "角色晋阶")
        for stage, mats in parse_promotion(prom_text or ""):
            rows.append({"角色名": name, "晋阶阶段": stage, "所需材料": mats})
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "角色晋阶.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    per_char = len(rows) / chars if chars else 0
    print(f"已生成 {out_file}，共 {len(rows)} 行晋阶记录，覆盖 {chars} 个角色；")
    print(f"平均每角色 {per_char:.1f} 个阶段（源文件固定为 7：1级 + 20/30/40/50/60/70级）。")


if __name__ == "__main__":
    main()
