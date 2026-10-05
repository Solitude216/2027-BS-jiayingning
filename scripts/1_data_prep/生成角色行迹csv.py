# -*- coding: utf-8 -*-
"""
脚本 5/8：将知识库角色 txt 中的角色行迹解析为《角色行迹.csv》。

CSV 列：角色名, 行迹类型, 行迹名称, 行迹描述, 成长消耗材料
说明：
  - 行迹包括：普攻、战技、终结技、天赋、秘技、额外能力、属性加成，
    以及忆灵技/忆灵天赋/欢愉技等新命途技能；部分联动角色（Saber、Archer 等）
    还有“炉心共鸣”“魔力放出”等特殊技能，统一归为“特殊技能”类型。
  - 行迹描述中夹带的数值占位（如【50%/100%】）会被自动跳过，不作为行迹。
  - 成长消耗材料取自【行迹成长消耗材料】段，按名称与行迹一一对应；
    同名称多次出现（如多个属性加成）按出现顺序配对，匹配不到时留空。

运行：python 生成角色行迹csv.py [知识库目录] [输出目录]
"""
import csv
import os
import re
import sys
from collections import defaultdict, deque

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
# 区块内其余行首【…】（如“普攻·强袭”等行迹名）原样保留在内容中。
SECTION_TITLES = {
    "星级", "属性", "命途", "阵营", "实装日期", "神权", "个人简介", "角色定位",
    "光锥推荐", "角色晋阶", "角色行迹", "行迹成长消耗材料", "角色星魂",
    "遗器推荐", "配队推荐", "角色立绘",
}


def split_sections(text: str) -> list:
    """
    按“行首【章节标题】”把全文切成 [(标题, 内容), ...]。
    标题与值同行时（如【星级】五星），值取同行剩余部分；
    标题独占一行时（如【角色行迹】），值取后续所有行（含行迹技能名）。
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

COLUMNS = ["角色名", "行迹类型", "行迹名称", "行迹描述", "成长消耗材料"]

# 已知的行迹类型前缀（标题以“前缀·名称”或“前缀 名称”形式给出）
KNOWN_TYPES = {"普攻", "战技", "终结技", "天赋", "秘技", "额外能力",
               "属性加成", "属性强化", "忆灵技", "忆灵天赋", "欢愉技",
               "技能", "特性"}
OTHER_TYPE = "特殊技能"

# 纯数值/符号标题（如【50%/100%】），是描述中的倍率占位，不是行迹
NUMERIC_TITLE = re.compile(r"^[\d./%\-、（）()·×\s]+$")
# 独立成行的【标题】
HEAD_RE = re.compile(r"^[ \t]*【([^】]+)】[ \t]*$")
# 标签行：（标签：…）
# 材料行：名称（共X级）：材料
MAT_RE = re.compile(r"^(.+?)[（(]\s*共\d+级\s*[)）]\s*[：:]\s*(.+)$")


def norm(s: str) -> str:
    """归一化名称（去所有空白并去掉首尾分隔符），用于材料名称匹配。

    兼容源文件笔误/差异，如块标题【普攻·】（尾随点）对应材料段“普攻”，
    【·暴击率强化】（前导点）对应材料段“暴击率强化”。
    """
    return re.sub(r"\s+", "", s).strip("·•/")


def clean_title(s: str) -> str:
    """清洗行迹块标题：去掉首尾空白与分隔符（保留内部空格，如“普攻 仁火攻心”）。"""
    return s.strip("·• \t/")


def core_name(s: str) -> str:
    """
    提取名称核心：剥掉已知类型的前缀或后缀（兼容开拓者-毁灭材料段的
    “再见安打·普攻”“攻击强化·属性加成”等反转写法），只保留技能名。
    """
    s = norm(s)
    for pre in sorted(KNOWN_TYPES, key=len, reverse=True):
        if s.startswith(pre) and len(s) > len(pre):
            s = s[len(pre):].lstrip("·•/")
            break
    for pre in sorted(KNOWN_TYPES, key=len, reverse=True):
        if s.endswith(pre) and len(s) > len(pre):
            s = s[:-len(pre)].rstrip("·•/")
            break
    return s


def reverse_key(s: str):
    """若 s 形如“技能名·类型”（类型在末尾，如“再见安打·普攻”），
    返回反转写法“类型·技能名”供与材料段匹配；否则返回 None。
    仅处理真正反转，避免“秘技·防御强化”等跨类型误配。"""
    s = norm(s)
    for t in sorted(KNOWN_TYPES, key=len, reverse=True):
        suffix = "·" + t
        if s.endswith(suffix) and len(s) > len(suffix):
            return t + "·" + s[: -len(suffix)]
    return None


def parse_traces(section_text: str) -> list:
    """解析【角色行迹】区文本，返回行迹块 [(标题, 描述, 标签), ...]。"""
    blocks = []
    cur_title = None
    buf = []
    for raw in section_text.splitlines():
        m = HEAD_RE.match(raw)
        if m:
            if cur_title is not None:
                blocks.append((cur_title, "\n".join(buf).strip()))
            cur_title = m.group(1).strip()
            buf = []
        else:
            if cur_title is not None:
                buf.append(raw)
    if cur_title is not None:
        blocks.append((cur_title, "\n".join(buf).strip()))

    traces = []
    for title, body in blocks:
        if NUMERIC_TITLE.match(title):      # 跳过倍率占位
            continue
        # 行迹标签并入描述：保留块内全部非空行（含每段“（标签：…）”），各段描述与标签完整
        desc = "\n".join(ln for ln in body.split("\n") if ln.strip())
        # 清洗标题后拆分类型与名称
        title_c = clean_title(title)
        head = re.split(r"[·•/]", title_c, maxsplit=1)[0]
        if head in KNOWN_TYPES:
            trace_type = head
            rest = re.sub(r"^[·•/]+", "", title_c[len(head):]).strip()
            trace_name = rest or head
        else:
            trace_type = OTHER_TYPE
            trace_name = title_c
        traces.append({"类型": trace_type, "名称": trace_name,
                       "标题": title_c, "描述": desc})
    return traces


def parse_materials(material_text: str) -> dict:
    """解析【行迹成长消耗材料】段，返回 名称归一 -> deque[材料文本]。"""
    mat = defaultdict(deque)
    for raw in material_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("（数据来源") or line.startswith("全部行迹"):
            continue
        m = MAT_RE.match(line)
        if m:
            mat[norm(m.group(1))].append(m.group(2).strip())
    return mat


def build_rows(kb_dir: str) -> list:
    rows = []
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)
        secs = split_sections(text)

        trace_text = field_value(secs, "角色行迹")
        material_text = field_value(secs, "行迹成长消耗材料")
        traces = parse_traces(trace_text or "")
        mats = parse_materials(material_text or "")

        def find_material(title_norm: str) -> str:
            # 1) 精确匹配（绝大多数）
            if title_norm in mats and mats[title_norm]:
                return mats[title_norm].popleft()
            # 2) 反转匹配：块标题“技能名·类型” ↔ 材料键“类型·技能名”
            rk = reverse_key(title_norm)
            if rk in mats and mats[rk]:
                return mats[rk].popleft()
            # 3) 匹配不到则视为源文件未提供，留空（不跨类型抢用）
            return ""

        for tr in traces:
            mat_str = find_material(norm(tr["标题"]))
            rows.append({
                "角色名": name,
                "行迹类型": tr["类型"],
                "行迹名称": tr["名称"],
                "行迹描述": tr["描述"],
                "成长消耗材料": mat_str,
            })
    return rows


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "角色行迹.csv")

    rows = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    chars = len({r["角色名"] for r in rows})
    no_mat = sum(1 for r in rows if not r["成长消耗材料"])
    print(f"已生成 {out_file}，共 {len(rows)} 条行迹，覆盖 {chars} 个角色；")
    print(f"未匹配到成长消耗材料的行迹 {no_mat} 条。")


if __name__ == "__main__":
    main()
