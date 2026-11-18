# -*- coding: utf-8 -*-
"""Per-page TTS + slide render + concat + subtitle burn.

Implements the instruction book's hard rules (§四 音画同步):
  - one audio file per page, never merged
  - page video length = real audio length + fixed gap (default 0.25s)
  - no duration/count or duration/char heuristics
  - concat via ffmpeg concat demuxer, verify total == sum(<0.3s)
  - subtitle timeline derived from page bounds + word marks, not ASR

Usage:
  python build_video.py storyboard.json out_dir [--voice NAME] [--gap 0.25]
"""
import argparse
import asyncio
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time

import edge_tts

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runtime import (
    FFMPEG,
    FFPROBE,
    FONT_CJK,
    FONT_CJK_BOLD,
    FONT_HAND,
    FONT_MONO,
    require_fonts,
)
from paths import resolve_out  # noqa: E402
from styles import tokens_for  # noqa: E402
from PIL import Image, ImageDraw, ImageFont


# 分辨率可用环境变量覆盖：VF_H=1440 → 2560x1440（2K）
H = int(os.environ.get("VF_H", "1080"))
W = int(round(H * 16 / 9))
FPS = int(os.environ.get("VF_FPS", "30"))
BG = (22, 26, 32)
FG = (232, 236, 241)
ACCENT = (86, 156, 214)
CODE_BG = (30, 36, 44)
DIM = (140, 150, 162)

import random

THEMES = {
    "dark": {
        "bg": (22, 26, 32), "fg": (232, 236, 241), "accent": (86, 156, 214),
        "code_bg": (30, 36, 44), "dim": (140, 150, 162), "card": (28, 34, 42),
        "font_title": FONT_CJK_BOLD, "font_body": FONT_CJK, "font_small": FONT_CJK,
        "rough": False,
    },
    "rough": {   # 手绘白板：纸底墨字、楷体、笔画带抖动
        "bg": (250, 248, 242), "fg": (38, 38, 44), "accent": (31, 111, 178),
        "code_bg": (238, 235, 226), "dim": (112, 112, 120), "card": (255, 255, 255),
        "font_title": FONT_HAND,
        "font_body": FONT_HAND,
        "font_small": FONT_HAND,
        "rough": True,
    },
}
T = dict(THEMES["dark"])


def _rnd(seed):
    return random.Random(seed)


def rough_line(d, p1, p2, color, width=3, seed=0, passes=2, jitter=2.2):
    """一条线画两遍、每遍轻微抖动，逼近手绘笔触。"""
    for k in range(passes):
        r = _rnd(seed * 97 + k)
        x1, y1 = p1
        x2, y2 = p2
        steps = max(2, int(max(abs(x2 - x1), abs(y2 - y1)) // 26))
        pts = []
        for i in range(steps + 1):
            t = i / steps
            x = x1 + (x2 - x1) * t + r.uniform(-jitter, jitter)
            y = y1 + (y2 - y1) * t + r.uniform(-jitter, jitter)
            pts.append((x, y))
        d.line(pts, fill=color, width=width + (0 if k == 0 else -1), joint="curve")


def rough_rect(d, box, color, width=3, seed=0, fill=None):
    x1, y1, x2, y2 = box
    if fill:
        d.rounded_rectangle(box, radius=10, fill=fill)
    rough_line(d, (x1, y1), (x2, y1), color, width, seed + 1)
    rough_line(d, (x2, y1), (x2, y2), color, width, seed + 2)
    rough_line(d, (x2, y2), (x1, y2), color, width, seed + 3)
    rough_line(d, (x1, y2), (x1, y1), color, width, seed + 4)


def rough_arrow(d, p1, p2, color, width=3, seed=0):
    rough_line(d, p1, p2, color, width, seed)
    r = _rnd(seed + 11)
    ang = 0.45
    import math
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    L = math.hypot(dx, dy) or 1
    ux, uy = dx / L, dy / L
    for sgn in (-1, 1):
        ax = p2[0] - 16 * (ux * math.cos(ang) - sgn * uy * math.sin(ang))
        ay = p2[1] - 16 * (uy * math.cos(ang) + sgn * ux * math.sin(ang))
        rough_line(d, (ax + r.uniform(-1, 1), ay + r.uniform(-1, 1)), p2, color, width, seed + 20 + sgn)


def _ass_color(h, alpha="00"):
    """#RRGGBB → ASS 的 &HAABBGGRR"""
    h = h.lstrip("#")
    if len(h) != 6:
        return "&H00FFFFFF"
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H{alpha}{b}{g}{r}"


def _is_light(h):
    h = h.lstrip("#")
    if len(h) != 6:
        return False
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) > 140


def _bmark():
    """项目符号：楷体类字体没有 •，退回中文间隔号，避免方框。"""
    f = str(T.get("font_body", "")).lower()
    return "· " if f.endswith(("simkai.ttf", "stxingka.ttf")) else "• "


def _hex(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def set_theme(name):
    global T
    T = dict(THEMES[name])



def run(cmd, **kw):
    # stdin=DEVNULL 是必须的：ffmpeg 默认会读 stdin，若父进程 stdin 是管道/终端，
    # 它会进交互模式（日志里出现 "Enter command: <target>|all ..."）然后一直挂住。
    kw.setdefault("stdin", subprocess.DEVNULL)
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-800:]}")
    return r.stdout


def probe_duration(path):
    out = run([FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out.strip())


def wrap_cjk(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur)
            cur = ""
            continue
        trial = cur + ch
        if draw.textlength(trial, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


_CODEX = {}



def _has_cjk(s):
    return any("\u4e00" <= ch <= "\u9fff" or "\u3000" <= ch <= "\u303f" for ch in s)


def _font_for(s, font_latin, font_cjk):
    """含中文就用中文字体，纯拉丁/数学用风格字体（SOLARA 的 times.ttf 没有中文字形）。"""
    return font_cjk if _has_cjk(s) else font_latin


def _mixed_line(d, x, y, text, f_ascii, f_cjk, fill):
    """Consolas has no CJK glyphs -> draw CJK with the YaHei font, ASCII with the mono font."""
    cx = x
    for ch in text:
        f = f_ascii if ord(ch) < 128 else f_cjk
        d.text((cx, y), ch, font=f, fill=fill)
        cx += d.textlength(ch, font=f)


def code_image(code, f_code, f_cjk, width):
    """Render the code block once per page (it never changes during the page)."""
    _fgc = T.get("code_fg", (200, 220, 200))
    _key = (code, tuple(T["code_bg"]), tuple(_fgc))
    if _key in _CODEX:
        return _CODEX[_key]
    lines = code.split("\n")[:14]
    h = 60 + len(lines) * 46
    img = Image.new("RGB", (width, h), T["code_bg"])
    d = ImageDraw.Draw(img)
    for i, ln in enumerate(lines):
        _mixed_line(d, 30, 28 + i * 46, ln, f_code, f_cjk, _fgc)
    _CODEX[_key] = img
    return img



def _badge(d, text, f, right=90, bottom=210, fill=T["accent"]):
    """右下角小角标（暂停提示 / 答案）。文字是中文，统一用系统中文字体。"""
    f = ImageFont.truetype(FONT_CJK, 26)          # 忽略传入字体，避免风格字体缺中文
    pad_x, pad_y = 22, 12
    w = d.textlength(text, font=f) + pad_x * 2
    h = 56
    x1, y1 = W - right - w, H - bottom
    d.rounded_rectangle([(x1, y1), (x1 + w, y1 + h)], radius=12,
                        outline=fill, width=3, fill=T.get('code_bg', (26, 33, 42)))
    d.text((x1 + pad_x, y1 + pad_y), text, font=f, fill=fill)


def draw_slide(page, idx, total, vis_items=None, vis_steps=None, highlight=None):
    """Draw one frame. vis_* = how many bullets/steps/code-items are visible (None = all)."""
    img = Image.new("RGB", (W, H), T["bg"])
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(T["font_title"], 64)
    f_body = ImageFont.truetype(T["font_body"], 44)
    _f_body_cjk = ImageFont.truetype(FONT_CJK, 44)
    f_code = ImageFont.truetype(FONT_MONO, 34)
    f_code_cjk = ImageFont.truetype(T["font_body"], 30)
    f_small = ImageFont.truetype(T["font_small"], 26)

    _title = page.get("title", "")
    d.text((90, 70), _title, font=_font_for(_title, f_title, ImageFont.truetype(FONT_CJK_BOLD, 64)), fill=T["fg"])
    if T.get("rough"):
        rough_line(d, (92, 168), (W - 92, 166), T["accent"], 3, seed=7)
    else:
        d.line([(90, 165), (W - 90, 165)], fill=(60, 68, 78), width=3)

    y = 210
    visual = page.get("visual") or {}
    vtype = visual.get("type", "bullets")
    items = visual.get("items", [])
    if vis_items is not None:
        items = items[:vis_items]

    if vtype == "bullets":
        all_items = visual.get("items", [])
        for k, item in enumerate(all_items):
            # spotlight mode: everything is on screen, the spoken line is highlighted
            if highlight is not None:
                color = T["accent"] if k == highlight else (T["fg"] if k < highlight else T["dim"])
            else:
                color = T["fg"]
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 260):
                if T.get("rough"):
                    _r = _rnd(hash((page.get("id"), k)) & 0xFFFF)
                    d.ellipse([(118 + _r.uniform(-1, 1), y + 18), (128, y + 28)],
                              fill=color)
                    d.text((152, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=color)
                else:
                    d.text((110, y), _bmark() + ln if ln == item[:len(ln)] else ln, font=_font_for(ln, f_body, _f_body_cjk), fill=color)
                y += 66
            y += 10
    elif vtype == "code":
        code = visual.get("code", "")
        cimg = code_image(code, f_code, f_code_cjk, W - 180)
        img.paste(cimg, (90, y))
        y += cimg.height + 30
        for item in items:
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 260):
                d.text((110, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["dim"])
                y += 60
    elif vtype == "diagram":
        steps = visual.get("steps", [])
        if vis_steps is not None:
            steps = steps[:vis_steps]
        n = max(1, len(visual.get("steps", [])))
        bw = min(380, (W - 260) // n)  # wide enough that 12-14 CJK chars stay on one line
        bx = 120
        for i, s in enumerate(steps):
            if T.get("rough"):
                rough_rect(d, (bx, y + 60, bx + bw, y + 200), T["accent"], 3,
                           seed=(idx * 31 + i), fill=T["card"])
            else:
                d.rounded_rectangle([(bx, y + 60), (bx + bw, y + 200)], radius=12,
                                    outline=T["accent"], width=3, fill=T["card"])
            for j, ln in enumerate(wrap_cjk(d, s, f_small, bw - 30)):
                d.text((bx + 15, y + 100 + j * 36), ln, font=f_small, fill=T["fg"])
            if i < n - 1:
                ax = bx + bw + 10
                if T.get("rough"):
                    rough_arrow(d, (ax, y + 130), (ax + 42, y + 130), T["accent"], 3,
                                seed=(idx * 37 + i))
                else:
                    d.line([(ax, y + 130), (ax + 40, y + 130)], fill=T["accent"], width=4)
                    d.polygon([(ax + 40, y + 130), (ax + 30, y + 124), (ax + 30, y + 136)],
                              fill=T["accent"])
            bx += bw + 50
        y += 280
        for item in items:
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 260):
                d.text((110, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["dim"])
                y += 60
    elif vtype == "quiz":
        for q in visual.get("question", []) or items:
            for ln in wrap_cjk(d, q, _font_for(q, f_body, _f_body_cjk), W - 300):
                d.text((110, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["fg"])
                y += 70
            y += 16
        _badge(d, "暂停 3 秒，自己先想", f_small)
    elif vtype == "recap":
        for item in items:
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 360):
                if T.get("rough"):
                    _r = _rnd(hash((page.get("id"), len(item))) & 0xFFFF)
                    d.ellipse([(118 + _r.uniform(-1, 1), y + 18), (128, y + 28)],
                              fill=T["accent"])
                    d.text((152, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["fg"])
                else:
                    d.text((110, y), _bmark() + ln if ln == item[:len(ln)] else ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["fg"])
                y += 74
            y += 12
        _badge(d, "复盘", f_small, fill=(126, 200, 140))
    elif vtype == "answer":
        for item in items:
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 300):
                d.text((110, y), _bmark() + ln if ln == item[:len(ln)] else ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["fg"])
                y += 66
            y += 10
        _badge(d, "答案", f_small, fill=(126, 200, 140))
    else:  # title
        for item in items:
            for ln in wrap_cjk(d, item, _font_for(item, f_body, _f_body_cjk), W - 260):
                d.text((110, y), ln, font=_font_for(ln, f_body, _f_body_cjk), fill=T["accent"])
                y += 70

    _f_page = ImageFont.truetype(FONT_CJK, 26)   # 页码必须用系统字体，风格字体可能缺字形
    d.text((W - 240, H - 60), f"{idx + 1} / {total}", font=_f_page, fill=T["dim"])
    return img


def render_slide(page, idx, total, out_png):
    """幻灯片页也要吃页级 style：临时切换主题，画完还原。"""
    global T
    saved = dict(T)
    tok = tokens_for(page.get("style"))
    if tok:
        T.update({"bg": _hex(tok["bg"]), "fg": _hex(tok["fg"]),
                  "accent": _hex(tok["accent"]), "dim": _hex(tok["dim"])})
        # 页级字体也要跟着走：否则手写体风格只剩 manim 页，幻灯片页还是黑体（风格割裂）
        if tok.get("font"):
            T["font_title"] = tok["font"]
            T["font_body"] = tok["font"]
            T["font_small"] = tok["font"]
        # 卡片底色也要跟着走：否则浅底风格会留下深色卡片 + 深色文字（图表页全黑块）
        _bg = _hex(tok["bg"]); _fg = _hex(tok["fg"])
        _mix = 0.06 if _is_light(tok["bg"]) else 0.12
        T["card"] = tuple(int(_bg[i] * (1 - _mix) + _fg[i] * _mix) for i in range(3))
        # 代码块：浅底风格用浅卡片 + 深字；深底保持原样
        if _is_light(tok["bg"]):
            T["code_bg"] = tuple(int(_bg[i] * 0.96 + _fg[i] * 0.04) for i in range(3))
            T["code_fg"] = _fg
        else:
            # 深色风格保持主题自带的代码块配色（T 已由 saved 快照负责还原）
            T["code_fg"] = (200, 220, 200)
    try:
        draw_slide(page, idx, total).save(out_png)
    finally:
        T.clear()
        T.update(saved)


def _norm(s):
    return re.sub(r"\s+", "", s)


def reveal_times(texts, narration, marks, page_len):
    """For each element text, when it first gets spoken (seconds inside the page)."""
    times = align_chars(narration, marks)
    narr_n = _norm(narration)
    orig = [i for i, ch in enumerate(narration) if not ch.isspace()]
    out = []
    for s in texts:
        sn = _norm(s)
        key = sn[:8] if len(sn) >= 8 else sn
        k = narr_n.find(key) if key else -1
        if k < 0 and len(sn) >= 4:
            k = narr_n.find(sn[:4])
        if k < 0 and len(sn) >= 2:
            k = narr_n.find(sn[:2])
        if k >= 0 and k < len(orig) and orig[k] in times:
            out.append(times[orig[k]][0])
        else:
            out.append(None)
    n = len(texts)
    # elements never spoken: spread them evenly so the page still develops visually
    fallback = [(page_len * (i + 1) / (n + 1)) for i in range(n)]
    return [x if x is not None else fallback[i] for i, x in enumerate(out)]


ANIM_FPS = 10


def render_animated_frames(page, idx, total, frames_dir, page_len, marks):
    """Progressive reveal synced to speech; returns number of frames written."""
    visual = page.get("visual") or {}
    vtype = visual.get("type")
    os.makedirs(frames_dir, exist_ok=True)
    for old in os.listdir(frames_dir):
        os.remove(os.path.join(frames_dir, old))

    if vtype == "diagram":
        texts, kind = visual.get("steps", []), "steps"
    elif vtype in ("bullets", "code"):
        texts, kind = visual.get("items", []), "items"
    else:
        texts, kind = [], "items"

    rt = reveal_times(texts, page.get("narration", ""), marks, page_len) if texts else []
    n = len(texts)
    if n == 0:
        # e.g. a `title` page: nothing to reveal, so draw the whole page once and hold it.
        draw_slide(page, idx, total).save(os.path.join(frames_dir, "f00000.png"))
        total_frames = max(2, int(math.ceil(page_len * ANIM_FPS)) + 1)
        for f in range(1, total_frames):
            shutil.copyfile(os.path.join(frames_dir, "f00000.png"),
                            os.path.join(frames_dir, f"f{f:05d}.png"))
        return total_frames
    # ceil + 1: an int() truncation here loses up to 1/fps per page and accumulates into
    # exactly the kind of drift the instruction book forbids (seen: 8 pages -> 0.48s).
    total_frames = max(1, int(math.ceil(page_len * ANIM_FPS)) + 1)
    for f in range(total_frames):
        t = f / ANIM_FPS
        shown = sum(1 for x in rt if x <= t) if texts else 0
        if vtype == "bullets":
            # everything visible, current line highlighted
            img = draw_slide(page, idx, total, vis_items=None,
                             highlight=(shown - 1) if shown > 0 else None)
        else:
            vis_items = shown if kind == "items" else None
            vis_steps = shown if kind == "steps" else None
            img = draw_slide(page, idx, total, vis_items=vis_items, vis_steps=vis_steps)
        img.save(os.path.join(frames_dir, f"f{f:05d}.png"))
    return total_frames


XING_PREV = set("执运可都也不就才还只进发行施通流举强横暴")


def tts_normalize(text):
    """Fix polyphone 行: háng (row/line) vs xíng (执行/也行/行为).

    MiniMax/edge read 行 as xíng by default, which is wrong for 行列/行数/每一行/命令行.
    We swap háng cases to the homophone 航 in the TTS input only; length is unchanged, so
    subtitle indices still map 1:1 back onto the original display text.
    """
    out = []
    for i, ch in enumerate(text):
        if ch == "行":
            prev = text[i - 1] if i else ""
            nxt = text[i + 1] if i + 1 < len(text) else ""
            if prev in XING_PREV or nxt == "为":
                out.append(ch)
                continue
            out.append("航")
        else:
            out.append(ch)
    return "".join(out)


def tts_page_minimax(text, voice, mp3_path, marks_path, retries=5, speed=0.9):
    """MiniMax T2A v2 (international host). Returns clause-level marks, interpolated later."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
    from tts_minimax import synthesize

    last = None
    for attempt in range(retries):
        try:
            audio, marks = synthesize(text, voice_id=voice, speed=speed)
            if len(audio) < 2000:
                raise RuntimeError(f"audio too small ({len(audio)} bytes)")
            with open(mp3_path, "wb") as f:
                f.write(audio)
            with open(marks_path, "w", encoding="utf-8") as f:
                for off, dur, w in marks:
                    f.write(f"{off:.3f}\t{dur:.3f}\t{w}\n")
            return marks
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 + attempt * 4)
    raise RuntimeError(f"MiniMax TTS failed after {retries} attempts: {last}")


async def tts_page(text, voice, rate, mp3_path, marks_path, retries=8):
    """edge-tts throttles hard (same text works once, then NoAudioReceived). Retry with backoff."""
    last = None
    # pace requests: hammering the endpoint is what triggers the block in the first place
    await asyncio.sleep(float(os.environ.get("TTS_SPACING", "5")))
    for attempt in range(retries):
        marks = []
        size = 0
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
            with open(mp3_path, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                        size += len(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        marks.append((chunk["offset"] / 1e7, round(chunk["duration"] / 1e7, 3), chunk["text"]))
            if size >= 2000:
                with open(marks_path, "w", encoding="utf-8") as f:
                    for off, dur, w in marks:
                        f.write(f"{off:.3f}\t{dur:.3f}\t{w}\n")
                await asyncio.sleep(1.2)
                return marks
            last = RuntimeError(f"audio too small ({size} bytes)")
        except Exception as e:  # noqa: BLE001
            last = e
        await asyncio.sleep(min(30, 4 + attempt * 5))
    raise RuntimeError(f"TTS failed after {retries} attempts: {last}")


def load_marks(marks_path):
    marks = []
    with open(marks_path, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 3:
                marks.append((float(parts[0]), float(parts[1]), parts[2]))
    return marks


def srt_ts(sec):
    ms = max(0, int(round(sec * 1000)))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


ASCII_TOKEN = re.compile(r"[A-Za-z0-9_\.\-]+")
PUNCT = "，。：；？！、）】」』"
CUE_END = "，。：；？！"


def align_chars(narration, marks):
    """Map each narration char index -> (t0, t1) using word marks as anchors."""
    times = {}
    pos = 0
    for off, dur, word in marks:
        idx = narration.find(word, pos)
        if idx < 0:
            continue
        n = max(1, len(word))
        for k in range(n):
            times[idx + k] = (off + dur * k / n, off + dur * (k + 1) / n)
        pos = idx + n
    return times


def build_cues(narration, marks, page_start, page_end, max_chars=18, align_text=None):
    """Keep original text (punctuation + CJK/ASCII spacing); time it from word marks.

    `align_text` is what was actually sent to TTS (polyphones rewritten, same length),
    so character indices map 1:1 onto the display text.
    """
    times = align_chars(align_text if align_text else narration, marks)
    if not times:
        # 有些 TTS 返回没有时间戳（或字幕文件取不到）：按字数在页内均分，保证字幕不缺席
        chars = [i for i, ch in enumerate(narration) if not ch.isspace()]
        span = max(0.2, page_end - page_start)
        step = span / max(1, len(chars))
        for k, ci in enumerate(chars):
            times[ci] = (page_start - page_start + k * step, (k + 1) * step)
    text = narration.strip()
    if not any(i in times for i in range(len(text))):
        return []

    def is_ascii_word(ix):
        return text[ix].isascii() and (text[ix].isalnum() or text[ix] in "_-.")

    cues = []
    i, n = 0, len(text)
    while i < n:
        # start a cue at the first non-space char
        if text[i].strip() == "":
            i += 1
            continue
        start = i
        end = i
        while end < n:
            ch = text[end]
            if ch in CUE_END:
                break
            if len(text[start:end + 1].strip()) >= max_chars:
                # do not cut inside a token like PagedAttention / AllReduce
                while end + 1 < n and is_ascii_word(end) and is_ascii_word(end + 1):
                    end += 1
                # prefer ending on punctuation: absorb up to 6 more chars if a break is near
                look = end + 1
                while look < n and look - end <= 6:
                    if text[look] in CUE_END:
                        end = look
                        break
                    look += 1
                break
            end += 1
        seg = text[start:min(end + 1, n)].strip()
        idxs = [j for j in range(start, min(end + 1, n)) if j in times]
        if seg and idxs:
            a = page_start + times[idxs[0]][0]
            b = page_start + times[idxs[-1]][1]
            if b - a < 0.4:
                b = a + 0.4
            cues.append((a, min(b, page_end - 0.05), seg))
        i = end + 1
    return cues


def fmt_ts(t, sep):
    h = int(t // 3600)
    m = int(t % 3600 // 60)
    s = t % 60
    if sep == ",":
        ss, ms = divmod(int(round(s * 1000)), 1000)
        return f"{h:02d}:{m:02d}:{ss:02d},{ms:03d}"
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def main():
    require_fonts()
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("outdir")
    ap.add_argument("--voice", default="zh-CN-XiaoxiaoNeural")
    ap.add_argument("--tts", default=os.environ.get("TTS_PROVIDER", "edge"),
                    choices=["edge", "minimax"], help="TTS backend")
    ap.add_argument("--theme", default="dark", choices=["dark", "rough"],
                    help="dark = 深色幻灯片；rough = 手绘白板风（楷体 + 抖动笔画）")
    ap.add_argument("--mm-speed", type=float,
                    default=float(os.environ.get("VKS_TTS_SPEED", "1.08")),
                    help="MiniMax speaking speed; VKS_TTS_SPEED overrides the default")
    ap.add_argument("--rate", default=os.environ.get("VKS_EDGE_TTS_RATE", "+5%"))
    ap.add_argument("--gap", type=float, default=0.25)
    a = ap.parse_args()

    a.outdir = resolve_out(a.outdir)
    set_theme(a.theme)
    base_theme = dict(T)
    with open(a.storyboard, encoding="utf-8") as f:
        sb = json.load(f)
    if "pages" in sb:
        pages = sb["pages"]
    else:  # contract form: {"parts": [{"part": ..., "pages": [...]}]}
        pages = []
        for part in sb.get("parts", []):
            for p in part.get("pages", []):
                p.setdefault("part", part.get("part"))
                pages.append(p)
    if not pages:
        raise SystemExit("storyboard has no pages")
    out = a.outdir
    for sub in ("slides", "audio", "segments"):
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    # 1) per-page TTS (never merged) + slide
    dur = []
    all_marks = []
    for i, p in enumerate(pages):
        mp3 = os.path.join(out, "audio", f"p{i + 1:03d}.mp3")
        mk = os.path.join(out, "audio", f"p{i + 1:03d}.words.txt")
        hpath = os.path.join(out, "audio", f"p{i + 1:03d}.hash")
        tts_text = tts_normalize(p["narration"])
        h = hashlib.sha1(f"{a.tts}|{a.voice}|{a.rate}|{a.mm_speed}|{tts_text}".encode("utf-8")).hexdigest()
        cached = False
        if os.path.exists(mp3) and os.path.exists(mk) and os.path.getsize(mp3) > 2000:
            if not os.path.exists(hpath):
                open(hpath, "w").write(h)          # seed: trust existing audio once
                cached = True
            else:
                cached = open(hpath).read().strip() == h
        if cached:
            marks = load_marks(mk)
            d = probe_duration(mp3)
        else:
            if a.tts == "minimax":
                marks = tts_page_minimax(tts_text, a.voice, mp3, mk, speed=a.mm_speed)
            else:
                marks = asyncio.run(tts_page(tts_text, a.voice, a.rate, mp3, mk))
            d = probe_duration(mp3)
            open(hpath, "w").write(h)
        dur.append(d)
        all_marks.append(marks)
        render_slide(p, i, len(pages), os.path.join(out, "slides", f"p{i + 1:03d}.png"))
        print(f"page {i+1:02d}: audio {d:7.3f}s  words {len(marks):3d}  "
              f"{'cached' if cached else 'tts   '}  -> {p.get('title','')[:30]}", flush=True)

    # 2) segments: video length = audio + gap (never divide total by count).
    #    PCM audio here: AAC frames round each segment up by up to 16ms, which accumulates
    #    0.3s+ over ~19 pages. PCM is sample-exact, and we encode AAC once at the end.
    seg_files = []
    seg_lens = []
    anim_pages = 0
    manim_pages = 0
    frames_so_far = 0
    cum_expected = 0.0
    for i, p in enumerate(pages):
        seg = os.path.join(out, "segments", f"s{i + 1:03d}.mkv")
        hold = float(p.get("hold", 0) or 0)   # 题目页可以让画面多停几秒给人思考
        seg_len = dur[i] + a.gap + hold
        # Pin cumulative frame counts (not per-segment): rounding each page independently
        # leaves up to half a frame of error each, which accumulated to 0.33s over 19 pages.
        cum_expected += seg_len
        target_frames = int(round(cum_expected * FPS))
        seg_frames = max(1, target_frames - frames_so_far)
        _tok = tokens_for(p.get("style"))
        if _tok:
            T.update({"bg": _hex(_tok["bg"]), "fg": _hex(_tok["fg"]),
                      "accent": _hex(_tok["accent"]), "dim": _hex(_tok["dim"])})
        else:
            T.update(base_theme)
        frames_so_far += seg_frames
        exact_len = seg_frames / FPS
        audio_pad = max(0.0, exact_len - dur[i])
        visual = p.get("visual") or {}
        renderer = str(p.get("renderer") or "slide").lower()
        animate = bool(visual.get("animate")) or visual.get("type") == "diagram"
        extra_vf = []
        if renderer == "manim":
            animate = False   # manim 页不出帧目录，别让下面的清理去删它
            # 页级接入：这一页交给 manim 渲染成一段视频，再补到精确段长
            from manim_page import render_page
            pv = render_page(p, exact_len, os.path.join(out, "_manim"))
            vinput = ["-i", pv]
            pad = max(0.0, exact_len - probe_duration(pv) + 0.15)
            if pad > 0.01:
                extra_vf = ["-vf", f"tpad=stop_mode=clone:stop_duration={pad:.3f}"]
            manim_pages += 1
        elif animate:
            fr_dir = os.path.join(out, "frames", f"p{i + 1:03d}")
            render_animated_frames(p, i, len(pages), fr_dir, exact_len, all_marks[i])
            vinput = ["-framerate", str(ANIM_FPS), "-i", os.path.join(fr_dir, "f%05d.png")]
            anim_pages += 1
        else:
            vinput = ["-loop", "1", "-framerate", str(FPS),
                      "-i", os.path.join(out, "slides", f"p{i + 1:03d}.png")]
        run([FFMPEG, "-y", *vinput,
             "-i", os.path.join(out, "audio", f"p{i + 1:03d}.mp3"),
             *extra_vf,
             "-frames:v", str(seg_frames),
             "-af", f"apad=pad_dur={audio_pad:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
             "-r", str(FPS), "-c:a", "pcm_s16le", "-ar", "44100", "-ac", "2",
             "-t", f"{exact_len:.4f}", seg])
        if animate:
            for f in os.listdir(fr_dir):
                os.remove(os.path.join(fr_dir, f))
            os.rmdir(fr_dir)
        seg_files.append(seg)
        seg_lens.append(exact_len)
    print(f"animated pages: {anim_pages}/{len(pages)}  manim pages: {manim_pages}", flush=True)

    # 3) concat demuxer, then verify total == sum
    seg_check = []
    for i, s in enumerate(seg_files):
        sd = probe_duration(s)
        delta = sd - seg_lens[i]
        seg_check.append({"seg": i + 1, "video": round(sd, 3), "audio": round(dur[i], 3),
                          "expect": round(seg_lens[i], 3), "delta": round(delta, 3),
                          "ok": abs(delta) <= 0.1})
    bad = [x for x in seg_check if not x["ok"]]
    print(f"segment sync: {len(seg_check) - len(bad)}/{len(seg_check)} within 0.1s", flush=True)
    if bad:
        print("  BAD:", bad, flush=True)

    listfile = os.path.join(out, "concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for s in seg_files:
            f.write(f"file '{os.path.abspath(s).replace(os.sep, '/')}'\n")
    merged = os.path.join(out, "merged.mkv")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", merged])
    total = probe_duration(merged)
    # The book's rule is "拼接后总时长等于各段之和（误差<0.3s）" -> compare against the
    # ACTUAL segment durations. The audio+gap total is reported separately as bookkeeping.
    seg_sum = sum(probe_duration(s) for s in seg_files)
    expect = sum(dur) + a.gap * len(pages)
    diff = abs(total - seg_sum)
    print(f"concat total={total:.3f}s sum(segments)={seg_sum:.3f}s diff={diff:.3f}s "
          f"| vs audio+gap: {abs(total-expect):.3f}s", flush=True)
    if diff > 0.3:
        raise SystemExit(f"FAIL: concat duration differs from sum(segments) by {diff:.3f}s > 0.3s")

    # 4) subtitles from page bounds + word marks (not ASR)
    cues = []
    t = 0.0
    for i, marks in enumerate(all_marks):
        start = t
        # 关键：页边界必须用真实段长（含 hold），否则带 hold 的页之后的字幕会整体提前
        end = t + seg_lens[i]
        cues.extend(build_cues(pages[i]["narration"], marks, start, end,
                               align_text=tts_normalize(pages[i]["narration"])))
        t = end
    srt = os.path.join(out, "subs.srt")
    with open(srt, "w", encoding="utf-8") as f:
        for i, (x, y, txt) in enumerate(cues, 1):
            f.write(f"{i}\n{srt_ts(x)} --> {srt_ts(y)}\n{txt}\n\n")
    print(f"cues: {len(cues)}", flush=True)
    if cues and cues[-1][1] > total + 0.05:
        raise SystemExit(f"FAIL: subtitle ends at {cues[-1][1]:.2f}s beyond video {total:.2f}s")

    # 5) burn subtitles
    final = os.path.join(out, "final_hardsub.mp4")
    srt_esc = srt.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    film_style = next((p_["style"] for p_ in pages if p_.get("style")), None)
    _tok = tokens_for(film_style) if film_style else None
    if _tok:
        # 页级风格：字幕颜色跟着风格走，浅底用深字、深底用浅字
        fg_c = _ass_color(_tok["fg"])
        bg_c = _ass_color(_tok["bg"])
        fname = "KaiTi" if _is_light(_tok["bg"]) else "Microsoft YaHei"
        # ffmpeg 烧字幕按 PlayResY=288 参考系缩放（1080p 会放大 ~3.75 倍），
        # 所以这里的数值要按“缩小后回到 ~26px 屏幕字号、离底 ~30px”来给。
        style = (f"FontName={fname},FontSize=13,PrimaryColour={fg_c},"
                 f"OutlineColour={bg_c},BackColour={bg_c},BorderStyle=1,Outline=2,Shadow=0,"
                 "Alignment=2,MarginV=4")
    elif T.get("rough"):
        # 纸底墨字：深色字幕 + 浅色描边，不要黑底块
        style = ("FontName=KaiTi,FontSize=24,PrimaryColour=&H00202024,"
                 "OutlineColour=&H00F6F4EE,BackColour=&H00F6F4EE,BorderStyle=1,Outline=2,Shadow=0,"
                 "Alignment=2,MarginV=56")
    else:
        # 字幕压到最底部、缩小，并用半透明底条，避免压住画面里的字
        style = ("FontName=Microsoft YaHei,FontSize=18,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BackColour=&H66000000,BorderStyle=3,Outline=0,Shadow=0,"
                 "Alignment=2,MarginV=24")
    run([FFMPEG, "-y", "-i", merged, "-vf", f"subtitles='{srt_esc}':force_style='{style}'",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-ar", "44100", final])

    rep = {
        "voice": a.voice, "gap": a.gap, "pages": len(pages),
        "audio_durations": dur, "sum_audio": round(sum(dur), 3),
        "audio_plus_gap": round(expect, 3), "sum_segments": round(seg_sum, 3), "actual_total": round(total, 3),
        "drift": round(diff, 3), "cues": len(cues),
        "segments": seg_check,
        "outputs": {"merged": merged, "hardsub": final, "srt": srt},
    }

    # 6) player chapters derived from the storyboard's `part` field
    chapters, t2 = [], 0.0
    for i, p in enumerate(pages):
        part = p.get("part") or p.get("title") or f"第 {i + 1} 页"
        if not chapters or chapters[-1]["label"] != part:
            chapters.append({"label": part, "t": round(t2, 3)})
        t2 += dur[i] + a.gap
    ch_path = os.path.join(out, "chapters.json")
    with open(ch_path, "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=2)
    rep["chapters"] = chapters
    rep["outputs"]["chapters"] = ch_path
    print(f"chapters: {len(chapters)}", flush=True)
    with open(os.path.join(out, "build-report.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
