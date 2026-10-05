# -*- coding: utf-8 -*-
"""
脚本 2/8：将知识库角色 txt 中的角色故事解析为《角色故事.csv》。

CSV 列：角色名, 故事编号, 故事标题, 故事内容
说明：
  - 故事标题在源文件中有多种写法，本脚本统一兼容：
      【角色故事·其一】/【其二】…（主流）
      【角色故事·一】（知更鸟•晴歌）
      【角色故事·仙舟】（仙舟三月七）
      【你的「故事」•一】…（开拓者各命途）
  - 故事编号为 1、2、3…（按出现顺序）。
  - 极个别文件存在无序号裸标记【角色故事】（如椒丘），仅作分节符，不单独成行。

运行：python 生成角色故事csv.py [知识库目录] [输出目录]
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


# ========== 本脚本主逻辑 ==========

COLUMNS = ["角色名", "故事编号", "故事标题", "故事内容"]

# 故事标题：匹配“角色故事·其一 / 你的「故事」•一 / 角色故事·仙舟 / 角色故事·一”等
STORY_RE = re.compile(r"【(角色故事|你的「故事」)([^】]*)】")
# 任意独立成行的【标题】，用于划定故事区终点（如【角色定位】【角色晋阶】）
SECTION_RE = re.compile(r"^[ \t]*【[^】]+】[ \t]*$", re.M)


def build_rows(kb_dir: str):
    """返回 (rows, 产出故事行的文件名集合)。"""
    rows = []
    files_with_stories = set()
    for fn in list_txt_files(kb_dir):
        text = read_text(os.path.join(kb_dir, fn))
        name = extract_name(text)

        # 找出所有故事标题的位置（不要求独立成行，兼容椒丘等文件的排版瑕疵）
        story_marks = list(STORY_RE.finditer(text))
        # 找出所有独立成行的【标题】位置，作为故事内容的截止边界
        sec_marks = list(SECTION_RE.finditer(text))

        # 只保留“带序号”的故事标记（裸【角色故事】或【你的「故事」】不产出故事行）
        numbered = [m for m in story_marks if m.group(2).strip()]

        for idx, m in enumerate(numbered):
            start = m.end()
            # 终点：下一个故事标题，或下一个独立成行的【标题】，或全文结尾
            end = len(text)
            for nxt in numbered[idx + 1:]:
                if nxt.start() >= start:
                    end = nxt.start()
                    break
            for s in sec_marks:
                if s.start() >= start:
                    end = min(end, s.start())
                    break
            content = text[start:end].strip()
            if not content:
                continue
            files_with_stories.add(fn)
            rows.append({
                "角色名": name,
                "故事编号": str(idx + 1),
                "故事标题": m.group(2).strip().strip("·•"),
                "故事内容": content,
            })
    return rows, files_with_stories


def main():
    kb_dir = sys.argv[1] if len(sys.argv) > 1 else KB_DIR
    out_dir = sys.argv[2] if len(sys.argv) > 2 else OUT_DIR
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "角色故事.csv")

    rows, files_with_stories = build_rows(kb_dir)
    with open(out_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    # 自检
    char_count = len({r["角色名"] for r in rows})
    print(f"已生成 {out_file}，共 {len(rows)} 条故事，覆盖 {char_count} 个角色。")
    missing = [fn for fn in list_txt_files(kb_dir) if fn not in files_with_stories]
    if missing:
        print("提示：下列文件未解析出故事行（多为格式特殊）：", missing)
    else:
        print("全部角色文件均解析出故事行。")


if __name__ == "__main__":
    main()
