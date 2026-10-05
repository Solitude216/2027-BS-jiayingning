# -*- coding: utf-8 -*-
"""
脚本 8/8：将知识库角色 txt 中的配队推荐解析为《配队推荐.csv》。

CSV 列：角色名, 位置, 推荐角色
说明：
  - 配队按“位置：角色A、角色B、角色C”一行一行给出，每个被推荐角色一行。
  - 位置常见有：主C、主c、双C、副C、辅助、拉条辅助、生存等，保留原文。

运行：python 生成配队推荐csv.py [知识库目录] [输出目录]
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
# 区块内其余行首【…】原样保留在内容中。
SECTION_TITLES = {
    "星级", "属性", "命途", "阵营", "实装日期", "神权", "个人简介", "角色定位",
    "光锥推荐", "角色晋阶", "角色行迹", "行迹成长消耗材料", "角色星魂",
    "遗器推荐", "配队推荐", "角色立绘",
}


def split_sections(text: str) -> list:
    """
    按“行首【章节标题】”把全文切成 [(标题, 内容), ...]。
    标题与值同行时（如【星级】五星），值取同行剩余部分；
    标题独占一行时（如【配队推荐】），值取后续所有行。
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

COLUMNS = ["角色名", "位置", "推荐角色"]

# 行：位置：角色们（中英文冒号均可）
LINE_RE = re.compile(r"^(.+?)[：:]\s*(.+)$")
# 角色列表分隔符：顿号、中文逗号、英文逗号
SEP_RE = re.compile("、|，|,")


def parse_teams(section_text: str) -> list:
    """解析【配队推荐】区文本，返回 [(位置, 角色), ...]"""
    teams = []
    for raw in section_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = LINE_RE.match(line)
        if not m:
            continue
        position = m.group(1).strip()
        char_list = [c.strip() for c in SEP_RE.split(m.group(2)) if c.strip()]
        for ch in char_list:
            teams.append((position, ch))
    return teams


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)
        team_text = field_value(secs, "配队推荐")
        for position, char in parse_teams(team_text or ""):
            rows.append({"角色名": name, "位置": position,
                         "推荐角色": char})
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "配队推荐.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    positions = sorted({r["位置"] for r in rows})
    print(f"已生成 {out_file}，共 {len(rows)} 条配队推荐，覆盖 {chars} 个角色；")
    print(f"位置类型：{'、'.join(positions)}")


if __name__ == "__main__":
    main()
