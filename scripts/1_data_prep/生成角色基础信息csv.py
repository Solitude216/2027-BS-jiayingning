# -*- coding: utf-8 -*-
"""
脚本 1/8：将《崩坏：星穹铁道》知识库中的所有角色 txt 解析为《角色基础信息.csv》。

CSV 列：角色名, 星级, 属性, 命途, 阵营, 实装日期, 神权, 角色定位, 个人简介, 常驻/限定
说明：
  - 「神权」只有翁法罗斯黄金裔等部分角色有，缺失时留空。
  - 输入目录、输出目录均可通过命令行参数覆盖，默认使用知识库目录与
    C:\毕业论文\角色数据csv\。

运行：python 生成角色基础信息csv.py
      python 生成角色基础信息csv.py [知识库目录] [输出目录]
"""
import csv
import os
import re
import sys

# ========== 通用解析函数（各脚本一致） ==========

KB_DIR = r"C:\毕业论文\knowledge_base\角色数据txt"
OUT_DIR = r"C:\毕业论文\knowledge_base\角色数据csv"


def list_txt_files(kb_dir: str) -> list:
    """返回知识库目录下所有 .txt 文件名（按名称排序）。"""
    names = [f for f in os.listdir(kb_dir) if f.lower().endswith(".txt")]
    return sorted(names)


def read_text(path: str) -> str:
    """读取 txt（源文件为 UTF-8 带 BOM，用 utf-8-sig 去掉 BOM）。"""
    with open(path, encoding="utf-8-sig") as f:
        return f.read()


def extract_name(text: str) -> str:
    """从文件首部「角色档案 —— XXX」行提取角色名。"""
    m = re.search(r"角色档案\s*——\s*(.+)", text)
    return m.group(1).strip() if m else ""


# 章节级标题白名单：只有这些标题才作为区块切分点，
# 区块内其余行首【…】（如晋阶子块、行迹技能名）原样保留在内容中。
SECTION_TITLES = {
    "星级", "属性", "命途", "阵营", "实装日期", "神权", "个人简介", "角色定位",
    "光锥推荐", "角色晋阶", "角色行迹", "行迹成长消耗材料", "角色星魂",
    "遗器推荐", "配队推荐", "角色立绘",
}


def split_sections(text: str) -> list:
    """
    按“行首【章节标题】”把全文切成 [(标题, 内容), ...]。
    标题与值同行时（如【星级】五星），值取同行剩余部分；
    标题独占一行时（如【个人简介】），值取后续所有行。
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
    """取某个【章节标题】对应的内容；不存在返回空串。"""
    for t, c in sections:
        if t == title:
            return c
    return ""


def extract_brief(text: str) -> str:
    """
    提取【个人简介】区内容。
    个人简介之后紧跟故事区（【角色故事·其一】或【你的「故事」•一】等），
    或直接进入【角色定位】，故以前三者标题的“前缀”（不要求闭合）为终点，
    避免把角色故事误并入个人简介。
    """
    m = re.search(r"【个人简介】\s*(.*?)(?=\s*【(?:角色定位|角色故事|你的「故事」))", text, re.S)
    return m.group(1).strip() if m else ""


# ========== 本脚本主逻辑 ==========

COLUMNS = ["角色名", "星级", "属性", "命途", "阵营", "实装日期",
           "神权", "角色定位", "个人简介"]


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        secs = split_sections(text)
        rows.append({
            "角色名": extract_name(text),
            "星级": field_value(secs, "星级"),
            "属性": field_value(secs, "属性"),
            "命途": field_value(secs, "命途"),
            "阵营": field_value(secs, "阵营"),
            "实装日期": field_value(secs, "实装日期"),
            "神权": field_value(secs, "神权"),
            "角色定位": field_value(secs, "角色定位"),
            "个人简介": extract_brief(text),
        })
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "角色基础信息.csv")

    rows = build_rows(kb_dir)
    # 首列角色名按文件序输出；其余字段按 COLUMNS 顺序
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"已生成 {out_file}，共 {len(rows)} 个角色。")
    # 自检：统计神权数量
    has_god = sum(1 for r in rows if r["神权"])
    print(f"含【神权】字段的角色数：{has_god}")


if __name__ == "__main__":
    main()
