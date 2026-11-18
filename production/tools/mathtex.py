#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""mathtex —— 用 matplotlib mathtext 把公式渲染成 PNG（本机无可用 LaTeX 的替代方案）。

为什么不用真 LaTeX：
  本机 MiKTeX 在中文路径下按需装包会挂死；TinyTeX 的 kpsewhich 在中文路径下失效且不带 dvisvgm。
  实测 mathtext（fontset=cm）排版质量足够，且纯离线、无外部进程。

用法：
    from mathtex import render_formula
    p = render_formula(r"\\frac{a}{b}", color="#EDEDED", fontsize=40)
    # 返回 PNG 路径（透明背景，dpi=400）
"""
import hashlib
import pathlib

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

matplotlib.rcParams["mathtext.fontset"] = "cm"
matplotlib.rcParams["svg.fonttype"] = "path"

CACHE = pathlib.Path(__file__).resolve().parent.parent / ".mathtex_cache"


def render_formula(tex, color="#EDEDED", fontsize=40, dpi=400):
    """把 $tex$ 渲染成透明 PNG，返回路径。带内容哈希缓存。"""
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.md5(f"{tex}|{color}|{fontsize}|{dpi}".encode("utf-8")).hexdigest()[:16]
    out = CACHE / f"{key}.png"
    if out.exists():
        return str(out)
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${tex}$", fontsize=fontsize, color=color)
    fig.savefig(out, dpi=dpi, transparent=True, bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)
    return str(out)


if __name__ == "__main__":
    import sys
    print(render_formula(sys.argv[1] if len(sys.argv) > 1 else r"e^{i\pi}+1=0"))
