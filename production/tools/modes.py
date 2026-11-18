#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""三个分区的单一真相源：科普 / 教学 / 涅槃。

每条规则都必须绑定一个可执行的检查（check 字段），否则它只是口号。
CLI:
    python tools/modes.py list                 # 三个分区各有什么规则
    python tools/modes.py check --mode scipop --project <目录>
"""
import json
import pathlib
import re
import sys

# 语速参考（字/分，含标点）——与实测 270–291 一致，取中位
CPS_PER_MIN = 280

MODES = {
    "scipop": {
        "label": "科普短片（精品手工路线）",
        # 科普不追求量，追求每一支都拿得出手：手写场景、逐页定制、密度更高。
        "target_min": [2.0, 6.0],
        "gap": 0.25, "mm_speed": 1.08, "quiz": False, "recap": True,
        "chapters": False, "fps_check": 3,
        "rules": [
            ("每页视觉都要专门设计：禁止用生成器模板页堆片", "handcrafted_only"),
            ("每 8–12 秒换一次视觉（比量产片更密）", "visual_switch"),
            ("开头 30 秒内用 2–3 个日常例子勾住观众", "opening_hook"),
            ("全片 2–6 分钟：短而密，不靠长度撑完播", "duration_range"),
            ("术语落地说人话", "manual"),
            ("片尾 2–4 条复盘，口播说「我们回顾一下」", "recap"),
        ],
    },
    "course": {
        "label": "长教学",
        "target_min": [15.0, 60.0],
        "gap": 0.25, "mm_speed": 1.08, "quiz": True, "recap": True,
        "chapters": True, "fps_check": 3,
        "rules": [
            ("必须由 ≥2 个 B站来源整合（多源涅槃，不是凭空生成）", "multi_source"),
            ("全片 15–60 分钟", "duration_range"),
            ("按章分 part，每章 90–210 秒", "chapter_len"),
            ("每 3–5 页插一次练习（题目页 → 答案页，绝不合并）", "quiz_density"),
            ("有效信息总量不变：覆盖清单漏一条不许交付", "coverage"),
            ("每条结论都要有严格出处 cites（S# pNN hh:mm:ss）", "cites_format"),
            ("练习与片尾复盘照旧要有", "quiz_recap"),
            ("成片必须真的存在（有分镜没成片算未交付）", "artifact"),
            ("多音字零高风险（TTS 念错即失败）", "polyphone"),
            ("专业术语读音已登记（防 TTS 念错缩写）", "term_reading"),
            ("知识点尽量用动画讲：动画页占比 ≥60%，纯文字不连排 >2 页", "animation"),
            ("每页声明知识点类型 kp + 所用手法，且手法出自两张表并匹配", "technique"),
            ("片尾复盘 2–4 条，覆盖要点/结论/易错点", "recap"),
            ("字幕与旁白逐段对齐，漂移 >0.1s 视为失败", "qa_sync"),
        ],
    },
    "remix": {
        "label": "视频涅槃",
        "target_min": [0.0, 999.0],          # 不按时长卡，按信息守恒卡
        "gap": 0.25, "mm_speed": 1.08, "quiz": True, "recap": True,
        "chapters": False, "fps_check": 3,
        "rules": [
            ("有效信息总量不变：覆盖清单漏一条不许交付", "coverage"),
            ("删的是废话不是知识点", "manual"),
            ("每页出处严格为 S# p## mm:ss（拒绝「风格参考」这类无时间戳写法）", "cites_format"),
            ("成片时长 ≥ 原片 55%（信息不能靠压缩丢）", "duration_ratio"),
            ("练习与片尾复盘照旧要有", "quiz_recap"),
            ("成片必须真的存在（有分镜没成片算未交付）", "artifact"),
            ("多音字零高风险（TTS 念错即失败）", "polyphone"),
            ("专业术语读音已登记（防 TTS 念错缩写）", "term_reading"),
            ("知识点尽量用动画讲：动画页占比 ≥60%，纯文字不连排 >2 页", "animation"),
            ("每页声明知识点类型 kp + 所用手法，且手法出自两张表并匹配", "technique"),
        ],
    },
}

# video_agent.py 需要「纯字符串规则」视图
for _m in MODES.values():
    _m["rules_text"] = [d for d, _k in _m["rules"]]

# 检查阈值（都是可调的显式数字，不是拍脑袋藏在代码里）
LIMITS = {
    "visual_switch_max_sec": 20.0,          # 量产片（涅槃/教学）的宽松线
    "visual_switch_max_sec_scipop": 12.0,   # 精品片要求更密
    "text_only_streak": 2,           # 连续 N 页纯文字即为违规
    "quiz_gap": [3, 5],              # 每 3–5 页一次练习
    "chapter_len": [90, 210],        # 每章秒数
    "duration_ratio": [0.55, 1.0],   # 涅槃时长 / 原片时长（至少保留 55%，不得超过原片）
    "narrative_ratio_min": 0.60,     # 非纯文字页（动画/图示）最低占比
    "recap_min_items": 2,
    "recap_max_items": 4,
}

SLIDE_ONLY = {"title", "bullets", "quiz", "answer", "recap", "code"}


def load_storyboard(project):
    p = pathlib.Path(project) / "storyboard.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def pages_of(sb):
    out = []
    for part in sb.get("parts", []):
        out.extend(part.get("pages", []))
    return out


def est_sec(page):
    """按口播字数估时长（有实测时长优先用实测）。"""
    if page.get("dur"):
        return float(page["dur"])
    n = len(re.sub(r"\s", "", page.get("narration", "")))
    return max(3.0, n / CPS_PER_MIN * 60.0)


def ptype(p):
    """页面类型：storyboard 把它放在 visual.type 里，spec 里是 type。"""
    return p.get("type") or (p.get("visual") or {}).get("type")


def pitems(p):
    return p.get("items") or (p.get("visual") or {}).get("items") or []


def is_anim_page(p):
    return p.get("renderer") == "manim"


# ───────────── 各项检查 ─────────────
def chk_duration_range(pages, mode):
    total = sum(est_sec(p) for p in pages) / 60.0
    lo, hi = MODES[mode]["target_min"]
    errs = []
    if total < lo:
        errs.append(f"总时长 {total:.2f} min 低于{mode}下限 {lo} min")
    if total > hi:
        errs.append(f"总时长 {total:.2f} min 超出上限 {hi} min（应砍页）")
    return errs, f"{total:.2f} min"


def chk_visual_switch(pages, mode):
    """科普的核心：不允许一页停太久、不允许连续纯文字。"""
    errs = []
    mx = LIMITS.get(f"visual_switch_max_sec_{mode}", LIMITS["visual_switch_max_sec"])
    long_pages = [(p.get("id"), est_sec(p)) for p in pages if est_sec(p) > mx]
    for pid, s in long_pages:
        errs.append(f"第 {pid} 页预计 {s:.1f}s > {mx}s，视觉太久没换")
    streak, streak_ids = 0, []
    def flush():
        nonlocal streak, streak_ids
        if streak >= LIMITS["text_only_streak"]:
            errs.append(f"连续 {streak} 页纯文字（{','.join(streak_ids)}）")
        streak, streak_ids = 0, []

    for p in pages:
        texty = (not is_anim_page(p)) and ptype(p) in SLIDE_ONLY and ptype(p) not in ("quiz", "answer")
        if texty:
            streak += 1
            streak_ids.append(p.get("id"))
        else:
            flush()
    flush()
    return errs, f"最长单页 {max((est_sec(p) for p in pages), default=0):.1f}s"


def chk_quiz_density(pages, mode):
    gaps = [3, 5]
    positions = [i for i, p in enumerate(pages) if ptype(p) == "quiz"]
    errs = []
    if not positions:
        return ["全片没有练习题"], "0 次"
    prev = -1
    for pos in positions:
        gap = pos - prev
        if gap > gaps[1]:
            errs.append(f"第 {pos+1} 页前有 {gap} 页没练习（上限 {gaps[1]}）")
        prev = pos
    tail = len(pages) - 1 - prev
    if tail > gaps[1]:
        errs.append(f"最后一次练习之后还有 {tail} 页")
    return errs, f"{len(positions)} 次"


def chk_quiz_recap(pages, mode):
    errs = []
    types = [ptype(p) for p in pages]
    if "quiz" not in types:
        errs.append("缺练习题")
    if "recap" not in types:
        errs.append("缺片尾复盘")
    return errs, f"quiz={types.count('quiz')} recap={types.count('recap')}"


def chk_recap(pages, mode):
    last = pages[-1] if pages else {}
    errs = []
    if ptype(last) != "recap":
        errs.append("最后一页不是复盘页")
    nar = last.get("narration", "")
    if "我们回顾一下" not in nar:
        errs.append("复盘页口播没有「我们回顾一下」")
    items = pitems(last)
    lo, hi = LIMITS["recap_min_items"], LIMITS["recap_max_items"]
    if items and not (lo <= len(items) <= hi):
        errs.append(f"复盘条目 {len(items)} 条，应在 {lo}–{hi}")
    return errs, f"{len(items)} 条"


PLACEHOLDERS = ("TODO", "【", "xx", "XX")

# 严格出处格式：S<来源号> p<分P或页> m:ss 或 h:mm:ss
CITE_RE = re.compile(r"^S\d+\s+p[0-9A-Za-z]+\s+\d{1,2}:\d{2}(:\d{2})?$")

# 知识点类型 → 可用手法（正向路径表 + 反向手法表的可执行投影）
KP_TECHNIQUE = {
    "概念":   {"morph_pair", "zoom_sequence", "curve_grow", "node_network",
               "stack_layers", "two_ends", "isomorphic_pair", "numline"},
    "流程":   {"timeline", "state_machine", "pipeline3", "ray_split", "stack_layers"},
    "状态":   {"state_machine", "timeline", "two_ends"},
    "对比":   {"two_columns", "two_ends", "bar_chart", "stacked_bar",
               "morph_pair", "isomorphic_pair"},
    "数值":   {"bar_chart", "stacked_bar", "curve_grow", "dual_axis_chart",
               "numline", "weighted_sum", "gradient_sequence", "utilization_grid"},
    "公式":   {"morph_pair", "split_formula_figure", "formula", "formula_lines", "curve_grow"},
    "结构":   {"zoom_sequence", "space_3d", "stack_layers", "cache_blocks",
               "token_strip", "qkv_colors", "isomorphic_pair", "node_network"},
    "空间":   {"space_3d", "vector_field_2d", "pixel_grid", "numline",
               "conv_slide", "spectrum_strip"},
    "因果":   {"ray_split", "timeline", "zoom_sequence", "pipeline3"},
    "时间线": {"timeline", "curve_grow", "gradient_sequence"},
}


def valid_techniques():
    """两张表里可执行的动画手法名（anim_kit 函数 ∪ 反向表键）。"""
    names = set()
    try:
        import inspect
        import anim_kit
        names |= {n for n, o in vars(anim_kit).items()
                  if inspect.isfunction(o) and o.__module__ == "anim_kit"
                  and not n.startswith("_")}
    except Exception:
        pass
    try:
        import anim_reverse
        names |= set(anim_reverse.REVERSE.keys())
    except Exception:
        pass
    return names


def _is_real_cite(c):
    """占位符不算真出处。"""
    if not c:
        return False
    t = str(c)
    return not any(ph in t for ph in PLACEHOLDERS)


def chk_cites(pages, mode):
    missing = [p.get("id") for p in pages
               if not p.get("cites") or not any(_is_real_cite(c) for c in p.get("cites"))]
    if missing:
        return [f"{len(missing)} 页缺 cites（{missing[:4]}…）"], f"{len(pages)-len(missing)}/{len(pages)} 有出处"
    return [], f"{len(pages)}/{len(pages)} 有出处"


def chk_multi_source(pages, mode, sb=None):
    """course 必须整合 ≥2 个 B 站来源；remix 至少 1 个。"""
    sb = sb or {}
    srcs = sb.get("sources") or []
    n = len([x for x in srcs if (x.get("bvid") or x.get("url"))])
    need = 2 if mode == "course" else 1
    if n < need:
        return ([f"来源只有 {n} 个，{mode} 至少需要 {need} 个（在 storyboard.sources 里登记）"],
                f"{n} 个来源")
    bvs = sorted({(x.get("bvid") or "") for x in srcs if x.get("bvid")})
    tail = f"{len(bvs)} 个不同 BV" if bvs else "无 BV 号"
    return [], f"{n} 个来源 / {tail}（{'、'.join(bvs[:3])}{'…' if len(bvs) > 3 else ''}）"



def chk_cites_format(pages, mode):
    """出处必须严格是 S# p## mm:ss —— 只写「风格参考」不算。"""
    bad = []
    for p in pages:
        cs = p.get("cites") or []
        good = [c for c in cs if _is_real_cite(c) and CITE_RE.match(str(c).strip())]
        if not good:
            bad.append(p.get("id"))
    if bad:
        return [f"{len(bad)} 页出处格式不合格（应形如 S1 p03 12:34）：{bad[:4]}"], \
               f"{len(pages)-len(bad)}/{len(pages)} 格式合规"
    return [], f"{len(pages)}/{len(pages)} 格式合规"


NOT_TEXT_TYPES = {"title", "text", "quote", "bullets", "recap", "quiz", "answer"}
STRUCT_TYPES = {"title", "recap", "quiz", "answer"}
# 这些是排版辅助，不算「用动画讲知识点」
HELPER_TECHS = {"text", "question", "legend", "bg_grid", "bottom_note",
                "corner_tag", "highlight_box", "chip", "annotation_board"}


def chk_animation_coverage(pages, mode):
    """知识点要尽量用动画讲：非纯文字页占比 + 不许长串纯文字页。"""
    errs = []
    types = []
    for p in pages:
        v = p.get("visual") or {}
        types.append((p.get("type") or v.get("type") or "text").lower())
    real = [t for t in types if t not in ("quiz", "answer")]
    if not real:
        return ["没有可统计的内容页"], "-"
    visual_n = sum(1 for t in real if t not in NOT_TEXT_TYPES)
    ratio = visual_n / len(real)
    lo = LIMITS["narrative_ratio_min"]
    if ratio < lo:
        errs.append(f"动画/图示页只占 {ratio:.0%}，低于 {lo:.0%}（纯文字页 {len(real)-visual_n} 个）")
    streak, mx = 0, 0
    for t in real:
        streak = streak + 1 if t in NOT_TEXT_TYPES else 0
        mx = max(mx, streak)
    if mx > LIMITS["text_only_streak"]:
        errs.append(f"连续纯文字页 {mx} 个，上限 {LIMITS['text_only_streak']}")
    return errs, f"动画页 {visual_n}/{len(real)}（{ratio:.0%}）· 最长纯文字连排 {mx}"


def chk_technique(project, mode):
    """每页要声明知识点类型与所用的动画手法，且手法必须来自那两张表。"""
    sb = load_storyboard(project) or {}
    pages = pages_of(sb)
    valid = valid_techniques()
    miss_kp, miss_tech, bad_tech, mismatch = [], [], [], []
    for p in pages:
        ptype = (p.get("type") or (p.get("visual") or {}).get("type") or "").lower()
        if ptype in STRUCT_TYPES:
            continue
        v = p.get("visual") or {}
        kp = p.get("kp") or v.get("kp")
        tech = p.get("technique") or v.get("technique") or v.get("path")
        if not kp:
            miss_kp.append(p.get("id"))
        if not tech:
            miss_tech.append(p.get("id"))
            continue
        if valid and tech not in valid:
            bad_tech.append(f"{p.get('id')}:{tech}")
        elif tech in HELPER_TECHS:
            mismatch.append(f"{p.get('id')}({kp}→{tech} 只是排版不是动画)")
        elif kp and kp in KP_TECHNIQUE and tech not in KP_TECHNIQUE[kp]:
            mismatch.append(f"{p.get('id')}({kp}→{tech})")
    errs = []
    if miss_kp:
        errs.append(f"{len(miss_kp)} 页没声明知识点类型 kp（{miss_kp[:3]}）")
    if miss_tech:
        errs.append(f"{len(miss_tech)} 页没声明动画手法 technique/path（{miss_tech[:3]}）")
    if bad_tech:
        errs.append(f"{len(bad_tech)} 页用了两张表里没有的手法：{bad_tech[:3]}")
    if mismatch:
        errs.append(f"{len(mismatch)} 页手法与知识点类型对不上：{mismatch[:3]}")
    if errs:
        return errs, "推导链不完整"
    return [], f"{len(pages)} 页均有 kp + 手法，且与表匹配"


def chk_artifact(project, mode):
    """分镜齐全但没成片 = 没交付。"""
    proj = pathlib.Path(project)
    mp4 = proj / "build" / "final_hardsub.mp4"
    if not mp4.exists():
        return ["没有 build/final_hardsub.mp4（还没渲染或渲染失败）"], "缺成片"
    size = mp4.stat().st_size
    if size < 100 * 1024:
        return [f"成片只有 {size/1024:.0f} KB，疑似损坏"], f"{size/1024:.0f} KB"
    sb = proj / "storyboard.json"
    stale = sb.exists() and sb.stat().st_mtime > mp4.stat().st_mtime + 5
    return [], f"{size/1048576:.1f} MB" + ("（分镜比成片新，建议重渲）" if stale else "")


def chk_polyphone(project, mode):
    """多音字高风险必须为 0。"""
    import subprocess
    proj = pathlib.Path(project)
    sb = proj / "storyboard.json"
    if not sb.exists():
        return ["找不到 storyboard.json"], "-"
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "polyphone.py"),
                        "check", str(sb)],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        d = json.loads(r.stdout or "{}")
    except Exception:
        return [f"多音字检查无法解析（退出码 {r.returncode}）"], "-"
    hi = d.get("high_risk", 0)
    if hi:
        words = sorted({i.get("word") for i in d.get("items", []) if i.get("risk") == "高"})
        return [f"多音字高风险 {hi} 处：{'、'.join([w for w in words if w][:5])}"], f"高风险 {hi}"
    return [], f"命中 {d.get('hits', 0)} 个词，高风险 0"


def chk_term_reading(project, mode):
    """专业术语读音：稿子里出现的术语必须在读音表里登记。"""
    proj = pathlib.Path(project)
    sb = load_storyboard(project)
    if sb is None:
        return [], "-"
    table = pathlib.Path(__file__).parent / "terms.txt"
    known = {}
    if table.exists():
        for ln in table.read_text(encoding="utf-8").splitlines():
            ln = ln.strip()
            if not ln or ln.startswith("#") or "|" not in ln:
                continue
            term, read = [x.strip() for x in ln.split("|", 1)]
            known[term] = read
    text = " ".join((p.get("narration") or "") for p in pages_of(sb))
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9_.\-]{1,}", text))
    # 科学计数法尾缀（6e-4 → e-4）不是术语，剔除
    tokens = {t for t in tokens if not re.fullmatch(r"[eE][-+]?\d+", t)}
    # 纯字母后缀、无意义的碎片也剔除
    tokens = {t for t in tokens if not re.fullmatch(r"[A-Za-z]{1,2}", t)}
    # 只有「全大写缩写」和「带数字的型号」才容易念错；普通英文单词不管
    risky = sorted(t for t in tokens
                   if ((len(t) >= 2 and t.isupper()) or re.search(r"\d", t))
                   and t not in known)
    if risky:
        return ([f"{len(risky)} 个专业术语没登记读音（可能被 TTS 念错）：{'、'.join(risky[:6])}"
                 f"｜在 tools/terms.txt 里加「术语 | 推荐口播写法」"], f"未登记 {len(risky)}")
    return [], f"术语 {len(tokens)} 个全部已登记"


def chk_chapter_len(pages, mode, sb=None):
    lo, hi = LIMITS["chapter_len"]
    errs = []
    for part in (sb or {}).get("parts", []):
        sec = sum(est_sec(p) for p in part.get("pages", []))
        if not (lo <= sec <= hi):
            errs.append(f"第 {part.get('part')} 章 {sec:.0f}s 超出 {lo}–{hi}s")
    return errs, f"{len((sb or {}).get('parts', []))} 章"


def chk_opening_hook(pages, mode):
    """科普开头：前 2 页至少出现一个问句或具体例子（自动粗判）。"""
    head = pages[:2]
    blob = " ".join(p.get("narration", "") for p in head)
    if "？" not in blob and not any(p.get("type") == "kit" or p.get("kit") == "question" for p in head):
        return ["开头两页既没有问句也没有具体例子"], "未命中"
    return [], "命中"


def chk_handcrafted_only(pages, mode):
    """科普精品路线：不允许用 anim_gen 生成的模板场景（scenes/gen_*.py）堆片。

    判定依据：kit 页的 scene 指向 scenes/gen_<topic>.py，那就是模板页；
    手写场景是 scenes/<自定义名>.py。
    """
    templated, handwritten = [], []
    for p in pages:
        sc = p.get("scene") or ""
        if not sc:
            continue
        if "/gen_" in sc or "/gen_" in sc.replace("\\", "/"):
            templated.append(p.get("id"))
        else:
            handwritten.append(p.get("id"))
    errs = []
    if templated:
        errs.append(f"{len(templated)} 页用的是生成器模板（{templated[:4]}…），"
                    f"科普要求逐页专门设计")
    return errs, f"手写 {len(handwritten)} 页 / 模板 {len(templated)} 页"


def chk_coverage(project, mode):
    proj = pathlib.Path(project)
    keys = proj / "keys.txt"
    sb = proj / "storyboard.json"
    if not keys.exists():
        return ["缺 keys.txt，无法核对覆盖"], "无清单"
    import subprocess
    r = subprocess.run([sys.executable, str(pathlib.Path(__file__).parent / "coverage_check.py"),
                        str(sb), "--keys", str(keys)], capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"覆盖\s*(\d+)\s*/\s*(\d+)", out)
    ratio = m.group(0).replace(" ", "") if m else None
    if ratio is None:
        return [f"覆盖率解析失败（coverage_check 退出码 {r.returncode}）"], "未知"
    cov, tot = int(m.group(1)), int(m.group(2))
    if r.returncode != 0 or cov < tot:
        miss = [ln for ln in out.splitlines() if "缺失" in ln and "**" in ln]
        return ([f"覆盖未满：{ratio}"] + miss[:3]), ratio
    return [], ratio


def chk_duration_ratio(project, mode):
    proj = pathlib.Path(project)
    agent = proj / "agent.json"
    if not agent.exists():
        return [], "无原片信息（跳过）"
    info = json.loads(agent.read_text(encoding="utf-8"))
    src = info.get("src_duration") or info.get("source_duration")
    if not src:
        return (["agent.json 里没有 src_duration，压缩比无法核对"
                 "（用 tools/backfill_remix.py --src-duration 回填）"], "缺原片时长")
    sb = load_storyboard(project)
    total = sum(est_sec(p) for p in pages_of(sb)) if sb else 0
    if not total:
        return [], "无成片时长（跳过）"
    ratio = total / float(src)
    lo, hi = LIMITS["duration_ratio"]
    if not (lo <= ratio <= hi):
        return [f"压缩比 {ratio:.2f} 超出 {lo}–{hi}（原片 {float(src)/60:.0f} min）"], f"{ratio:.2f}"
    return [], f"{ratio:.2f}"


CHECK_IMPL = {
    "duration_range": chk_duration_range,
    "visual_switch": chk_visual_switch,
    "quiz_density": chk_quiz_density,
    "quiz_recap": chk_quiz_recap,
    "recap": chk_recap,
    "cites": chk_cites,
    "chapter_len": chk_chapter_len,
    "multi_source": chk_multi_source,
    "cites_format": chk_cites_format,
    "animation": chk_animation_coverage,
    "technique": chk_technique,
    "artifact": chk_artifact,
    "polyphone": chk_polyphone,
    "term_reading": chk_term_reading,
    "opening_hook": chk_opening_hook,
    "handcrafted_only": chk_handcrafted_only,
    "coverage": chk_coverage,
    "duration_ratio": chk_duration_ratio,
    "qa_sync": None,          # 由 video_agent qa 负责
    "manual": None,           # 人工判断
}


def check(project, mode):
    sb = load_storyboard(project)
    if sb is None:
        return {"mode": mode, "ok": False, "error": f"找不到 {project}/storyboard.json"}
    pages = pages_of(sb)
    results = []
    for desc, key in MODES[mode]["rules"]:
        impl = CHECK_IMPL.get(key)
        if impl is None:
            results.append({"rule": desc, "key": key, "status": "manual",
                            "detail": "人工/引擎其余阶段负责"})
            continue
        try:
            if key in ("chapter_len", "multi_source"):
                errs, detail = impl(pages, mode, sb)
            elif key in ("coverage", "duration_ratio", "artifact",
                         "polyphone", "term_reading", "technique"):
                errs, detail = impl(project, mode)
            else:
                errs, detail = impl(pages, mode)
        except Exception as e:
            errs, detail = [f"检查异常：{type(e).__name__}: {e}"], "-"
        results.append({"rule": desc, "key": key,
                        "status": "fail" if errs else "pass",
                        "detail": detail, "errors": errs})
    bad = [r for r in results if r["status"] == "fail"]
    return {"mode": mode, "label": MODES[mode]["label"], "ok": not bad,
            "pages": len(pages), "results": results}


def main():
    if "--list" in sys.argv or "list" in sys.argv or len(sys.argv) == 1:
        for mid, m in MODES.items():
            lo, hi = m["target_min"]
            dur = f"{lo:g}–{hi:g} min" if mid != "remix" else "不按时长卡"
            print(f"\n【{mid}】{m['label']}（{dur}）")
            for desc, key in m["rules"]:
                tag = "" if CHECK_IMPL.get(key) else " ［人工/外部］"
                print(f"  · {desc}{tag}")
        return 0
    if "--check" in sys.argv or "check" in sys.argv:
        mode = None
        proj = None
        for i, a in enumerate(sys.argv):
            if a == "--mode" and i + 1 < len(sys.argv):
                mode = sys.argv[i + 1]
            if a == "--project" and i + 1 < len(sys.argv):
                proj = sys.argv[i + 1]
        if not mode or not proj:
            print("用法：python tools/modes.py check --mode scipop --project <目录>")
            return 2
        r = check(proj, mode)
        print(f"== {r.get('label', mode)} 检查：{proj}")
        print(f"   页数 {r.get('pages', 0)}｜结论：{'通过' if r.get('ok') else '有未通过项'}")
        for item in r["results"]:
            mark = {"pass": "[OK]", "fail": "[!!]", "manual": "[--]"}[item["status"]]
            print(f"   {mark} {item['rule']}")
            if item["status"] == "fail":
                for e in item["errors"]:
                    print(f"        - {e}")
            elif item["detail"]:
                print(f"        {item['detail']}")
        return 0 if r.get("ok") else 1
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
