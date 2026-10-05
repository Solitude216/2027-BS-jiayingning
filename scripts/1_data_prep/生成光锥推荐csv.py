# -*- coding: utf-8 -*-
"""
脚本 3/8：将知识库角色 txt 中的光锥推荐解析为《光锥推荐.csv》。

CSV 列：角色名, 光锥名称, 推荐度, 基础属性, 光锥效果
说明：
  - 每个角色一般推荐 3 个光锥，一个光锥一行。
  - 基础属性形如“生1058 攻582 防463”。
  - 少数光锥缺少推荐度/基础属性时留空。

运行：python 生成光锥推荐csv.py [知识库目录] [输出目录]
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
    标题独占一行时（如【光锥推荐】），值取后续所有行。
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

COLUMNS = ["角色名", "光锥名称", "推荐度", "基础属性", "光锥效果"]

# 属性行：生XXX 攻XXX 防XXX；个别文件“生”与“攻”之间无空格（如“生952攻476 防350”），故用 \s*
ATTR_RE = re.compile(r"^生\d+\s*攻\d+\s*防\d+$")        # 生1058 攻582 防463 / 生952攻476 防350
RANK_RE = re.compile(r"^推荐度[★☆]+$")                   # 推荐度★★★★★
NUMERIC_RE = re.compile(r"^[\d./%\-、（）()·×\s]+$")      # 纯数值（倍率占位）


def parse_light_cones(section_text: str) -> list:
    """
    解析光锥推荐区文本，返回条目列表。

    判定规则：普通文本行若其后的第一个非空行是“基础属性行”或“推荐度行”，
    则它是光锥名称行；否则它是上一光锥的效果文本行。这样可兼容：
      - 效果跨多行（万敌等）
      - 光锥名称以【名称】形式出现（椒丘等）
    """
    # 预处理：过滤空行。
    # 对整行【名称】去方括号（如椒丘的【那无数个春天】）；
    # 但若整行【X】且其后的第一个非空行恰好等于 X（源文件的光锥名“声明”格式），
    # 则视为重复声明并丢弃，避免它被误并入上一光锥的效果。
    # 纯数值的【50%/100%】属于效果文本，保持原样。
    raw_lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]
    cleaned = []
    for i, line in enumerate(raw_lines):
        m = re.fullmatch(r"【(.+?)】", line)
        if m and not NUMERIC_RE.match(m.group(1)):
            x = m.group(1).strip()
            nxt = raw_lines[i + 1] if i + 1 < len(raw_lines) else ""
            if nxt == x:
                continue          # 光锥名重复声明行，丢弃
            line = x
        cleaned.append(line)

    rows = []
    for line in cleaned:
        if ATTR_RE.match(line):
            rows.append(("attr", line))
        elif RANK_RE.match(line):
            rows.append(("rank", line))
        else:
            rows.append(("plain", line))

    items = []
    cur = None
    for i, (kind, line) in enumerate(rows):
        if kind == "attr":
            if cur is not None:
                cur["基础属性"] = line
            continue
        if kind == "rank":
            if cur is not None:
                cur["推荐度"] = line.replace("推荐度", "")
            continue
        # plain：名称 or 效果
        nxt_kind = rows[i + 1][0] if i + 1 < len(rows) else None
        if nxt_kind in ("attr", "rank"):
            if cur is not None:
                items.append(cur)
            cur = {"光锥名称": line, "推荐度": "", "基础属性": "", "光锥效果": []}
        else:
            if cur is not None:
                cur["光锥效果"].append(line)
            # 若区块以无名称的效果行开始（异常），忽略
    if cur is not None:
        items.append(cur)

    for it in items:
        # 部分文件光锥名出现两次（【名称】行 + 名称行），去掉效果首行的重复名称
        if it["光锥效果"] and it["光锥效果"][0] == it["光锥名称"]:
            it["光锥效果"] = it["光锥效果"][1:]
        it["光锥效果"] = "\n".join(it["光锥效果"])
    return items


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)
        lc_text = field_value(secs, "光锥推荐")
        for it in parse_light_cones(lc_text or ""):
            rows.append({
                "角色名": name,
                "光锥名称": it["光锥名称"],
                "推荐度": it["推荐度"],
                "基础属性": it["基础属性"],
                "光锥效果": it["光锥效果"],
            })
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "光锥推荐.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    no_rank = sum(1 for r in rows if not r["推荐度"])
    no_effect = sum(1 for r in rows if not r["光锥效果"])
    print(f"已生成 {out_file}，共 {len(rows)} 条光锥推荐，覆盖 {chars} 个角色；")
    print(f"其中缺推荐度 {no_rank} 条，缺效果 {no_effect} 条。")


if __name__ == "__main__":
    main()
