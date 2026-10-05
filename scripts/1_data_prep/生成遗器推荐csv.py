# -*- coding: utf-8 -*-
"""
脚本 7/8：将知识库角色 txt 中的遗器推荐解析为《遗器推荐.csv》。

CSV 列：角色名, 方案序号, 隧洞遗器, 位面饰品, 推荐指数, 主词条, 副词条
说明：
  - 一个角色通常给出 1~2 套遗器方案，每套方案一行。
  - 源文件中每套方案由“隧洞遗器 | …”开头，方案内字段为“键 | 值”形式；
    个别文件缺少推荐指数（如艾丝妲）时留空。

运行：python 生成遗器推荐csv.py [知识库目录] [输出目录]
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
    标题独占一行时（如【遗器推荐】），值取后续所有行。
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

COLUMNS = ["角色名", "方案序号", "隧洞遗器", "位面饰品", "推荐指数",
           "主词条", "副词条"]

# 方案内字段行：键 | 值（键可能带【】或※前缀，如【隧洞遗器】、※主词条推荐）
KV_RE = re.compile(r"^[※]?\s*(.+?)\s*\|\s*(.+)$")
# 键名兼容：不同文件写法略有差异（如“隧洞遗器”与“【隧洞遗器】”、“主词条”与“※主词条推荐”）
KEY_RULES = [
    ("隧洞遗器", "隧洞遗器"),
    ("位面饰品", "位面饰品"),
    ("推荐指数", "推荐指数"),
    ("主词条", "主词条"),
    ("副词条", "副词条"),
]


def parse_relics(section_text: str) -> list:
    """解析【遗器推荐】区文本，返回 [(方案字段 dict), ...]"""
    plans = []
    cur = None
    for raw in section_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = KV_RE.match(line)
        if not m:
            continue
        key = m.group(1).strip().strip("【】")
        val = m.group(2).strip()
        # 新方案：以“隧洞遗器”行为起点
        if "隧洞遗器" in key:
            if cur is not None:
                plans.append(cur)
            cur = {"隧洞遗器": "", "位面饰品": "", "推荐指数": "",
                   "主词条": "", "副词条": ""}
        if cur is None:
            continue
        for needle, field in KEY_RULES:
            if needle in key:
                cur[field] = val
                break
    if cur is not None:
        plans.append(cur)

    return plans


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)
        relic_text = field_value(secs, "遗器推荐")
        for idx, p in enumerate(parse_relics(relic_text or ""), start=1):
            rows.append({
                "角色名": name,
                "方案序号": str(idx),
                "隧洞遗器": p["隧洞遗器"],
                "位面饰品": p["位面饰品"],
                "推荐指数": p["推荐指数"],
                "主词条": p["主词条"],
                "副词条": p["副词条"],
            })
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "遗器推荐.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    no_relic = sum(1 for r in rows if not r["隧洞遗器"])
    no_rank = sum(1 for r in rows if not r["推荐指数"])
    print(f"已生成 {out_file}，共 {len(rows)} 套遗器方案，覆盖 {chars} 个角色；")
    print(f"其中缺隧洞遗器 {no_relic} 条，缺推荐指数 {no_rank} 条。")


if __name__ == "__main__":
    main()
