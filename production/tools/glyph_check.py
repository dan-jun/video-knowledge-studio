#!/usr/bin/env python
"""缺字检查：扫 storyboard 里所有要上屏的文字，找出目标字体里没有字形的字符（会渲染成方框）。
用法：python tools/glyph_check.py <storyboard.json> [更多…]
"""
import json
import sys
from fontTools.ttLib import TTFont, TTCollection

FONT_FILES = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simkai.ttf",
              r"C:\Windows\Fonts\consola.ttf", r"C:\Windows\Fonts\msyhbd.ttc"]

_cmaps = None


def load_cmaps():
    global _cmaps
    if _cmaps is not None:
        return _cmaps
    union = set()
    for path in FONT_FILES:
        try:
            if path.lower().endswith(".ttc"):
                for f in TTCollection(path).fonts:
                    for t in f["cmap"].tables:
                        union |= set(t.cmap.keys())
            else:
                f = TTFont(path)
                for t in f["cmap"].tables:
                    union |= set(t.cmap.keys())
        except Exception:
            continue
    _cmaps = union
    return union


def texts_of(page):
    out = [page.get("title", ""), page.get("narration", "")]
    v = page.get("visual") or {}
    out += list(v.get("items") or [])
    out += list(v.get("steps") or [])
    out += list(v.get("question") or [])
    if v.get("code"):
        out.append(v["code"])
    return "".join(str(x) for x in out)


def main(paths):
    cmap = load_cmaps()
    bad = {}
    for p in paths:
        d = json.load(open(p, encoding="utf-8"))
        for part in d.get("parts", []):
            for pg in part.get("pages", []):
                txt = texts_of(pg)
                missing = sorted({ch for ch in txt if ord(ch) > 127 and ord(ch) not in cmap})
                if missing:
                    bad.setdefault(p, []).append((pg.get("id"), "".join(missing)))
    if not bad:
        print("[OK] 没有缺字")
        return 0
    for p, rows in bad.items():
        print(f"== {p}")
        for pid, chars in rows:
            print(f"   {pid}: 缺 {chars!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
