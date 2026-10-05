# -*- coding: utf-8 -*-
"""
脚本 6/8：将知识库角色 txt 中的角色星魂解析为《角色星魂.csv》。

CSV 列：角色名, 星魂序号, 星魂名称, 星魂效果
说明：
  - 每个角色 6 个星魂（序号 1~6），一个星魂一行。
  - 部分角色的星魂带【加强前】/【加强后】两段描述，完整保留在“星魂效果”中，
    以换行分隔，便于论文对照分析。

运行：python 生成角色星魂csv.py [知识库目录] [输出目录]
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
# 区块内其余行首【…】（如【1】斩尽）原样保留在内容中。
SECTION_TITLES = {
    "星级", "属性", "命途", "阵营", "实装日期", "神权", "个人简介", "角色定位",
    "光锥推荐", "角色晋阶", "角色行迹", "行迹成长消耗材料", "角色星魂",
    "遗器推荐", "配队推荐", "角色立绘",
}


def split_sections(text: str) -> list:
    """
    按“行首【章节标题】”把全文切成 [(标题, 内容), ...]。
    标题与值同行时（如【星级】五星），值取同行剩余部分；
    标题独占一行时（如【角色星魂】），值取后续所有行。
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

COLUMNS = ["角色名", "星魂序号", "星魂名称", "星魂效果"]

EID_PATTERN = re.compile("^【\\s*([1-6])\\s*】\\s*(.*)$")


def parse_eidolons(section_text: str) -> list:
    """解析【角色星魂】区文本，返回 [(序号, 名称, 效果), ...]"""
    eidolons = []
    cur_no = None
    cur_name = ""
    buf = []
    for raw in section_text.splitlines():
        m = EID_PATTERN.match(raw.strip())
        if m:
            if cur_no is not None:
                eidolons.append((cur_no, cur_name, "\n".join(buf).strip()))
            cur_no = int(m.group(1))
            cur_name = m.group(2).strip()
            buf = []
        else:
            if cur_no is not None:
                buf.append(raw)
    if cur_no is not None:
        eidolons.append((cur_no, cur_name, "\n".join(buf).strip()))
    return eidolons


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)
        eid_text = field_value(secs, "角色星魂")
        for no, eid_name, effect in parse_eidolons(eid_text or ""):
            rows.append({"角色名": name, "星魂序号": str(no),
                         "星魂名称": eid_name, "星魂效果": effect})
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "角色星魂.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    no_name = sum(1 for r in rows if not r["星魂名称"])
    no_effect = sum(1 for r in rows if not r["星魂效果"])
    print(f"已生成 {out_file}，共 {len(rows)} 条星魂，覆盖 {chars} 个角色；")
    print(f"缺星魂名称 {no_name} 条，缺效果 {no_effect} 条。")


if __name__ == "__main__":
    main()
