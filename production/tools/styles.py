# -*- coding: utf-8 -*-
"""风格令牌：把「代码动画风格库」里的风格，翻译成我们渲染器能直接吃的外观参数。

用法：
    from styles import tokens_for
    t = tokens_for("Z1")      # -> {"bg": "#f7f4ec", "fg": ..., "motion": "slow", ...}

渲染器怎么消费：
    manim 页：page["style"]="Z1" → manim_page 把 tokens 塞进 PAGE_SPEC → 场景用它们上色
    幻灯片：page["style"]="K10" → build_video 用它们覆盖主题色
"""

from runtime import FONT_CJK, FONT_CJK_BOLD, FONT_HAND

# 只收「知识讲解类视频用得上」的风格；配色按各自的外观描述定，字数与节奏按讲解场景调。
REGISTRY = {
    # ── 蒸馏自 B 站 UP（第二批）──────────────────────────
    "AVGUSTA": {
        "name": "AvgusTa 黑底节点网络", "fit": ["manim"],
        "bg": "#000000", "fg": "#E8E8E8", "accent": "#5CD0E8",
        "accent2": "#F5B942", "dim": "#3A4650",
        "font": FONT_CJK, "motion": "medium",
        "note": "纯黑 + 青色节点 + 金色字幕；机制类讲解首选",
    },
    "RETHINKFUN": {
        "name": "RethinkFun 白底系统图", "fit": ["manim", "幻灯片"],
        "bg": "#FFFFFF", "fg": "#1F2328", "accent": "#2F6FB5",
        "accent2": "#E8B23A", "dim": "#8A9099",
        "font": FONT_CJK, "motion": "slow",
        "note": "白底灰框 + 表格 + 双曲线；AI Infra 系统图专用",
    },
    "XIAOBAI": {
        "name": "小白debug 浅蓝流程", "fit": ["manim", "幻灯片"],
        "bg": "#EEF3F8", "fg": "#22303C", "accent": "#2E86DE",
        "accent2": "#E0574A", "dim": "#8FA3B5",
        "font": FONT_CJK, "motion": "medium",
        "note": "浅蓝底 + 圆角标签 + 三框流程；红绿语义对照",
    },
    # ── 蒸馏自 B 站 UP（2026-11 采集）──────────────────────
    "SOLARA": {
        "name": "Solara 深色数学", "fit": ["manim"],
        "bg": "#000000", "fg": "#EDEDED", "accent": "#E8C547",
        "accent2": "#8B3A3A", "dim": "#5A6570",
        "font": FONT_CJK, "motion": "slow",
        "note": "纯黑 + LaTeX + 暗红/深青大圆；关键结论绿框高亮",
    },
    "GHOST": {
        "name": "过拟合青年 手写板书", "fit": ["manim", "幻灯片"],
        "bg": "#000000", "fg": "#F2F2F2", "accent": "#B58CE0",
        "accent2": "#7FDB8C", "dim": "#9AA0A6",
        "font": FONT_HAND, "motion": "medium",
        "note": "黑底手写楷体 + 彩色粉笔标记；一屏一个问句",
    },
    # ── 3b1b 风格 ────────────────────────────────────────────
    "3B1B": {
        "name": "3b1b 深色数学", "fit": ["manim"],
        "bg": "#0D1117", "fg": "#EAF2F8", "accent": "#58C4DD",
        "accent2": "#F08A24", "dim": "#4E6B7A",
        "font": FONT_CJK, "motion": "medium",
        "note": "深色底 + 青橙配色；数学动画讲解用，对比度高、箭头醒目",
    },
    # ── 中国风 ────────────────────────────────────────────────
    "Z1": {
        "name": "水墨", "fit": ["manim", "手绘白板"],
        "bg": "#F7F4EC", "fg": "#1D1D1F", "accent": "#2F3A4A",
        "accent2": "#8C6B45", "dim": "#8A8F98",
        "font": FONT_HAND, "motion": "slow",
        "note": "留白多、墨色浓；文字用楷体，动画慢起慢收",
    },
    "Z13": {
        "name": "水墨漫画", "fit": ["手绘白板"],
        "bg": "#FBF7EE", "fg": "#20201F", "accent": "#B23A2E",
        "accent2": "#3D5A6C", "dim": "#8C8C88",
        "font": FONT_HAND, "motion": "medium",
        "note": "毛笔线 + 晕染；适合叙事型讲解",
    },
    # ── 卡通 / 手绘 ───────────────────────────────────────────
    "K10": {
        "name": "粉笔黑板", "fit": ["手绘白板", "manim"],
        "bg": "#14181C", "fg": "#F2F2F2", "accent": "#7EE0A8",
        "accent2": "#FFB454", "dim": "#9AA4AE",
        "font": FONT_HAND, "motion": "medium",
        "note": "黑底彩色粉笔；适合讲道理、科普",
    },
    "M1": {
        "name": "白板手绘讲解", "fit": ["手绘白板"],
        "bg": "#FFFFFF", "fg": "#222222", "accent": "#3B7DD8",
        "accent2": "#FF7043", "dim": "#8C8C8C",
        "font": FONT_HAND, "motion": "medium",
        "note": "线条先画再上色；最贴我们 frametell 引擎",
    },
    # ── 科技 / 界面 ───────────────────────────────────────────
    "V8": {
        "name": "赛博朋克 HUD", "fit": ["Remotion", "manim"],
        "bg": "#071018", "fg": "#D8F7FF", "accent": "#00E5FF",
        "accent2": "#FF6A00", "dim": "#4E6B7A",
        "font": FONT_CJK_BOLD, "motion": "fast",
        "note": "青线 + 橙色告警；数据流、架构图很出效果",
    },
    "R6": {
        "name": "东方赛博", "fit": ["Remotion", "manim"],
        "bg": "#F2E6D0", "fg": "#3A1F1A", "accent": "#E0402A",
        "accent2": "#19B3B0", "dim": "#9C8A78",
        "font": FONT_CJK_BOLD, "motion": "fast",
        "note": "纸色底 + 大红 + 霓虹；适合做片头卡",
    },
    # ── 版式 ─────────────────────────────────────────────────
    "H1": {
        "name": "Biennale 羊皮纸", "fit": ["幻灯片", "Remotion"],
        "bg": "#EFE3C8", "fg": "#1D2A4A", "accent": "#D9A21B",
        "accent2": "#8C6B45", "dim": "#7A6E58",
        "font": FONT_CJK, "motion": "slow",
        "note": "暖纸底 + 太阳黄 + 靛蓝墨；做章节封面最稳",
    },
    # ── 线墨 ─────────────────────────────────────────────────
    "C1": {
        "name": "水墨晕开", "fit": ["manim"],
        "bg": "#F5EFE4", "fg": "#2A2A2A", "accent": "#5B6B7A",
        "accent2": "#A98B62", "dim": "#8F8B84",
        "font": FONT_HAND, "motion": "slow",
        "note": "宣纸底、墨团晕开；适合情绪与回忆段落",
    },
}


# 没有精调令牌的风格，按所属系列派生一套「调性近似」的配色。
# derived=True 表示只是系列级近似，不是逐条试过。
SERIES_DEFAULT = {
    "A-G": {"bg": "#0D1014", "fg": "#EEF2F7", "accent": "#5AA9FF", "accent2": "#7EE0A8",
            "dim": "#8B96A3", "motion": "medium", "note": "代码样片通用深色"},
    "H":   {"bg": "#F2EAD8", "fg": "#1D2A4A", "accent": "#C8922B", "accent2": "#8C6B45",
            "dim": "#7A6E58", "motion": "slow", "note": "纸底油墨版式"},
    "K":   {"bg": "#FFF8EF", "fg": "#2A2A2A", "accent": "#FF7A45", "accent2": "#4C9AFF",
            "dim": "#8C8C88", "motion": "medium", "note": "卡通画风暖底"},
    "L":   {"bg": "#11151B", "fg": "#F0F3F8", "accent": "#7C5CFF", "accent2": "#35D6C0",
            "dim": "#7E8897", "motion": "medium", "note": "Lemo 系列中性深色"},
    "M":   {"bg": "#FFFFFF", "fg": "#222222", "accent": "#3B7DD8", "accent2": "#FF7043",
            "dim": "#8C8C8C", "motion": "medium", "note": "讲解白板"},
    "O":   {"bg": "#0B0D12", "fg": "#F5E9D6", "accent": "#C9A227", "accent2": "#8E6C4A",
            "dim": "#7C7468", "motion": "slow", "note": "电影感深色"},
    "R":   {"bg": "#0A0F16", "fg": "#E8F6FF", "accent": "#FF4D6D", "accent2": "#19B3B0",
            "dim": "#6B7C8C", "motion": "fast", "note": "赛博参考风"},
    "V":   {"bg": "#071018", "fg": "#D8F7FF", "accent": "#00E5FF", "accent2": "#FF6A00",
            "dim": "#4E6B7A", "motion": "fast", "note": "HUD 界面风"},
    "X":   {"bg": "#0E1116", "fg": "#E6EDF3", "accent": "#7EE787", "accent2": "#79C0FF",
            "dim": "#8B949E", "motion": "medium", "note": "代码视频风"},
    "Z":   {"bg": "#F7F4EC", "fg": "#1D1D1F", "accent": "#8C6B45", "accent2": "#B23A2E",
            "dim": "#8A8F98", "motion": "slow", "note": "中国风纸墨"},
}
SERIES_OF = {}
for _k in list("ABCDEFG"):
    SERIES_OF[_k] = "A-G"
for _k in "HKLMORVXZ":
    SERIES_OF[_k] = _k


def _derived(style_id):
    fam = SERIES_OF.get(style_id[:1].upper())
    if not fam:
        return None
    base = dict(SERIES_DEFAULT[fam])
    base.update({
        "id": style_id,
        "name": f"{style_id}（{fam} 系列派生）",
        "series": fam,
        "derived": True,
        "font": FONT_CJK,
        "step": MOTION_STEP.get(base.get("motion", "medium"), 1.2),
    })
    return base

# 节奏 → 单步动画上限（秒）
MOTION_STEP = {"slow": 1.6, "medium": 1.2, "fast": 0.9}


def tokens_for(style_id):
    s = (style_id or "").strip()
    if not s:
        return None
    key = s.upper()
    for k in (key, key.split("_")[0]):
        if k in REGISTRY:
            t = dict(REGISTRY[k])
            t["id"] = k
            t["step"] = MOTION_STEP.get(t.get("motion", "medium"), 1.2)
            t["derived"] = False
            return t
    return _derived(s)


def list_styles():
    return [{"id": k, **v} for k, v in REGISTRY.items()]


def apply_to_storyboard(storyboard, style_id, only_missing=False):
    """把风格写到 storyboard 的每页（only_missing=True 时只补没写 style 的页）。"""
    import json
    sb = json.load(open(storyboard, encoding="utf-8"))
    n = 0
    for part in sb.get("parts", []):
        for pg in part.get("pages", []):
            if only_missing and pg.get("style"):
                continue
            pg["style"] = style_id
            n += 1
    json.dump(sb, open(storyboard, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return n


if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "apply":
        # 用法: python tools/styles.py apply <storyboard.json> <风格ID>
        n = apply_to_storyboard(sys.argv[2], sys.argv[3])
        print(f"已给 {n} 页打上 {sys.argv[3]}")
        sys.exit(0)
    if len(sys.argv) > 1:
        print(json.dumps(tokens_for(sys.argv[1]), ensure_ascii=False, indent=2))
    else:
        print(json.dumps(list_styles(), ensure_ascii=False, indent=2))
