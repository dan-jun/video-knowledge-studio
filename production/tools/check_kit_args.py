#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""渲染前校验 spec 里每个 kit 页的参数能否被对应函数接受（省掉一轮轮渲染试错）。"""
import inspect
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import anim_kit

KIT = {n: o for n, o in vars(anim_kit).items()
       if inspect.isfunction(o) and o.__module__ == "anim_kit" and not n.startswith("_")}
try:
    import anim_gen as _AG
    RENDERABLE = set(_AG.KIT_FUNCS) if hasattr(_AG, "KIT_FUNCS") else set()
except Exception:
    RENDERABLE = set()

# 各函数的「元素形状」要求（踩过的坑）
COLOR_PARAMS = {"result"}

# 画面上放得下的说明文字上限（超了会互相重叠）
LABEL_MAX = {"pipeline3": ("steps", 2, 10), "two_columns": ("left_items", 1, 14),
             "stack_layers": ("names", 1, 18), "timeline": ("items", 1, 10)}

ELEM_SHAPE = {
    "zoom_sequence": ("levels", 4, "[(标签, 宽, 高, 颜色)]"),
    "pipeline3": ("steps", 2, "[(标签, 说明)]"),
    "numline": ("ticks", 2, "[(位置, 标签)]"),
    "weighted_sum": ("items", 3, "[(系数, 颜色, 标签)]"),
    "isomorphic_pair": ("rows", 1, "[字符串]"),
    "timeline": ("items", 1, "[字符串] 或 [[标签, 宽度比]]"),
    "stack_layers": ("names", 1, "[字符串]"),
    "two_columns": ("left_items", 1, "[字符串]"),
    "two_ends": ("left_items", 1, "[字符串]"),
    "bar_chart": ("data", 2, "[[标签, 数值]]"),
    "token_strip": ("tokens", 1, "[字符串]"),
    "formula_lines": ("lines", 2, "[(表达式, 是否公式)]"),
    "space_3d": ("vectors", 3, "[(x, y, z)]"),
}


def check(spec_path):
    spec = json.loads(pathlib.Path(spec_path).read_text(encoding="utf-8"))
    pages = spec.get("pages") or [p for pt in spec.get("parts", []) for p in pt.get("pages", [])]
    errs = []
    for pg in pages:
        if pg.get("type") != "kit":
            continue
        fn = pg.get("kit")
        f = KIT.get(fn)
        if not f:
            errs.append(f"{pg['id']}: 手法 {fn} 不存在")
            continue
        if RENDERABLE and fn not in RENDERABLE:
            errs.append(f"{pg['id']}: 手法 {fn} 不可渲染（anim_gen.KIT_FUNCS 里没有）")
            continue
        args = dict(pg.get("args") or {})
        sig = inspect.signature(f)
        params = {k: v for k, v in sig.parameters.items() if k != "scene"}
        for k in args:
            if k not in params:
                errs.append(f"{pg['id']}: {fn} 不认识参数 {k}（可用 {list(params)}）")
        req = [k for k, v in params.items() if v.default is inspect._empty]
        for k in req:
            if k not in args:
                errs.append(f"{pg['id']}: {fn} 缺必填参数 {k}")
        if fn == "conv_slide" and "grid" in args:
            errs.append(f"{pg['id']}: conv_slide 不能经 JSON 传 grid 对象，改用 values")
        for ck in COLOR_PARAMS & set(args):
            v = args[ck]
            if isinstance(v, str) and not v.startswith("#"):
                errs.append(f"{pg['id']}: {fn}.{ck} 要颜色(#rrggbb)，现在拿到 {v!r}")
        if fn == "formula_lines":
            for it in (args.get("lines") or []):
                if isinstance(it, (list, tuple)) and len(it) == 2 and it[1]:
                    t = str(it[0])
                    # 只认明确的代码标记；方括号在数学里也常见，不算
                    code_marks = ("self.", "for ", "def ", "import ", "torch.", "nn.", " = torch", "()")
                    if any(m in t for m in code_marks) and "\\" not in t:
                        errs.append(f"{pg['id']}: 代码行不要标公式（is_math=True 会渲染成斜体数学）：{t[:24]}")
                        break
        if fn == "numline":
            xr = args.get("x_range") or [-3.5, 3.5]
            tk = args.get("ticks") or []
            xs = list(xr) + [t[0] for t in tk if isinstance(t, (list, tuple)) and len(t) == 2]
            if xs and max(abs(x) for x in xs) > 7:
                errs.append(f"{pg['id']}: numline 数轴坐标超出 ±7（会跑出画面）：max={max(abs(x) for x in xs):.0f}")
        if fn in LABEL_MAX:
            key, idx, lim = LABEL_MAX[fn]
            vals = args.get(key)
            if isinstance(vals, list):
                for v in vals:
                    t = v[idx - 1] if isinstance(v, (list, tuple)) and len(v) >= idx else (v if isinstance(v, str) else "")
                    if isinstance(t, str) and len(t) > lim:
                        errs.append(f"{pg['id']}: {fn}.{key} 里有 {len(t)} 字的标签（上限 {lim}）：{t[:20]}")
                        break
        if fn in ELEM_SHAPE:
            key, nwant, hint = ELEM_SHAPE[fn]
            vals = args.get(key)
            if isinstance(vals, list) and vals:
                for v in vals:
                    if nwant == 1:
                        ok = isinstance(v, str)
                    else:
                        ok = isinstance(v, (list, tuple)) and len(v) == nwant
                    if not ok:
                        errs.append(f"{pg['id']}: {fn}.{key} 元素形状不对，应为 {hint}")
                        break
    return errs


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python tools/check_kit_args.py <spec.json> [...]")
        sys.exit(2)
    bad = 0
    for sp in sys.argv[1:]:
        errs = check(sp)
        name = pathlib.Path(sp).name
        if errs:
            bad += 1
            print(f"[FAIL] {name}")
            for e in errs:
                print("   -", e)
        else:
            print(f"[OK ] {name}")
    sys.exit(1 if bad else 0)
