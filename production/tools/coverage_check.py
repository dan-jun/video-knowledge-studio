# -*- coding: utf-8 -*-
"""覆盖清单：核对「原片知识点」是否都进了重制版分镜。

用法：
    python tools/coverage_check.py <storyboard.json> --keys keys.txt [--out coverage.md]

keys.txt：每行一个知识点，格式 `知识点名 | 关键词1 关键词2 ...`
          （命中任一关键词即视为已覆盖；两个 `||` 表示必须同时命中）

重制流程里这是**交付前必跑的一步**：漏掉的知识点必须补页或明确标注「故意删」。
"""
import argparse
import json
import os
import re


def load_keys(path):
    rows = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            rows.append((line, [line]))
            continue
        name, kw = line.split("|", 1)
        if "||" in kw:
            rows.append((name.strip(), ["&&".join(k.strip() for k in kw.split("||"))]))
        else:
            rows.append((name.strip(), [k.strip() for k in kw.split() if k.strip()]))
    return rows


def covered(blob, keywords):
    for kw in keywords:
        if "&&" in kw:
            if all(k in blob for k in kw.split("&&")):
                return True
        elif kw in blob:
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("--keys", required=True, help="知识点清单文件")
    ap.add_argument("--out", default=None, help="输出 coverage.md 路径")
    a = ap.parse_args()

    sb = json.load(open(a.storyboard, encoding="utf-8"))
    pages = []
    for part in sb.get("parts", []):
        pages.extend(part.get("pages", []))
    blob = json.dumps(pages, ensure_ascii=False)

    rows, missing = [], []
    for name, kws in load_keys(a.keys):
        ok = covered(blob, kws)
        rows.append((name, ok))
        if not ok:
            missing.append(name)

    lines = ["# 覆盖清单", "", f"源分镜：{os.path.basename(a.storyboard)}　页数：{len(pages)}", "",
             "| 原片知识点 | 是否覆盖 |", "|---|---|"]
    for name, ok in rows:
        lines.append(f"| {name} | {'已覆盖' if ok else '**缺失**'} |")
    lines += ["", f"覆盖 {len(rows) - len(missing)}/{len(rows)}"
              + (f"；缺失 {len(missing)} 项，交付前必须补页或标注「故意删」" if missing else "")]

    text = "\n".join(lines)
    print(text)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text + "\n")
    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()
