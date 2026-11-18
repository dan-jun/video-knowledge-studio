# -*- coding: utf-8 -*-
"""产出路径统一的落盘规则。"""

import os

from runtime import OUT_ROOT


def resolve_out(p):
    """把相对产出路径挂到 production/projects 下。"""
    if not p:
        return p
    if os.path.isabs(p):
        return p
    name = p.replace("\\", "/").rstrip("/").split("/")[-1]
    if not name:
        return OUT_ROOT
    return os.path.join(str(OUT_ROOT), name)


def ensure(p):
    os.makedirs(p, exist_ok=True)
    return p
