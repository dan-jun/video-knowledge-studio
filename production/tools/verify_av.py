# -*- coding: utf-8 -*-
"""Independent audio-video sync check: sample N timestamps, listen (+/-3s) with ASR,
compare what is HEARD against what the page's narration should be.

Usage:
  python verify_av.py <storyboard.json> <render_out_dir> [--n 10] [--out report.md]

<render_out_dir> must contain audio/pNNN.mp3 (as build_video.py writes).
"""
import argparse

# 覆盖率下限：低于它就不算「ASR 噪声」，判 low（不通过）。
# 2026-11-16 补硬：原来 asr_noise 一律算通过，覆盖率 0.00 的点也能写「通过」。
ASR_NOISE_FLOOR = 0.15
import json
import os
import random
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from runtime import FFMPEG, FFPROBE

MODEL = os.environ.get("VKS_WHISPER_MODEL") or "small"
GAP = 0.25


def dur(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def norm(s):
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s)


def _t2s(s):
    """whisper-small tends to emit traditional Chinese; normalise before comparing."""
    try:
        from opencc import OpenCC
        global _CC
        _CC = globals().get("_CC") or OpenCC("t2s")
        return _CC.convert(s)
    except Exception:
        return s


def load_marks(render_dir, idx):
    path = os.path.join(render_dir, "audio", f"p{idx + 1:03d}.words.txt")
    out = []
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            parts = line.rstrip("\n").split("\t")
            if len(parts) == 3:
                out.append((float(parts[0]), float(parts[1]), parts[2]))
    return out


def expected_slice(marks, t0, t1, pad=0.35):
    """What the narration should say inside [t0, t1] (seconds, page-relative)."""
    return "".join(w for off, d, w in marks if off + d >= t0 - pad and off <= t1 + pad)


def _read_wav(path):
    """Decode 16k mono wav to float32 numpy array (avoids PyAV version drift)."""
    import wave

    import numpy as np
    with wave.open(path, "rb") as w:
        data = w.readframes(w.getnframes())
    return np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0


def coverage(expected, heard):
    """fraction of expected characters that ASR actually heard (order-insensitive bigram)."""
    e, h = norm(expected), norm(heard)
    if not e:
        return 0.0
    grams = [e[i:i + 2] for i in range(len(e) - 1)]
    hit = sum(1 for g in grams if g in h)
    return hit / max(1, len(grams))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("storyboard")
    ap.add_argument("render_dir")
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out")
    ap.add_argument("--allow-miss", type=int, default=1,
                    help="允许挂几个抽点仍算 PASS（原来硬编码 n-1，也就是 1）")
    a = ap.parse_args()

    sb = json.load(open(a.storyboard, encoding="utf-8"))
    pages = sb.get("pages") or [p for part in sb.get("parts", []) for p in part.get("pages", [])]

    # page timeline from the real per-page audio (never from guessing)
    starts, t = [], 0.0
    for i, p in enumerate(pages):
        starts.append(t)
        t += dur(os.path.join(a.render_dir, "audio", f"p{i + 1:03d}.mp3")) + GAP
    total = t

    video = None
    for cand in ("final_hardsub.mp4", "merged.mp4"):
        fp = os.path.join(a.render_dir, cand)
        if os.path.exists(fp):
            video = fp
            break
    if not video:
        raise SystemExit("no rendered video in " + a.render_dir)

    picks = []
    for frac in (0.02, 0.25, 0.5, 0.75, 0.97):  # 开头/中段/结尾都要覆盖
        picks.append(round(total * frac, 2))
    random.seed(7)
    while len(picks) < a.n:
        picks.append(round(random.uniform(0.05 * total, 0.95 * total), 2))
    picks = sorted(picks[: a.n])

    from faster_whisper import WhisperModel
    model = WhisperModel(MODEL, device="cpu", compute_type="int8")

    rows, bad = [], 0
    tmp = os.path.join(a.render_dir, "_avcheck")
    os.makedirs(tmp, exist_ok=True)
    for k, ts in enumerate(picks):
        idx = 0
        for i, s in enumerate(starts):
            if s <= ts + 1e-6:
                idx = i
        page = pages[idx]
        local0 = max(0.0, ts - 3 - starts[idx])
        local1 = ts + 3 - starts[idx]
        want = expected_slice(load_marks(a.render_dir, idx), local0, local1)
        if len(norm(want)) < 6:  # window fell in a gap / very short page
            want = page["narration"]
        clip = os.path.join(tmp, f"c{k:02d}.wav")
        subprocess.run([FFMPEG, "-y", "-v", "error", "-ss", f"{max(0, ts - 3):.2f}",
                        "-t", "6", "-i", video, "-vn", "-ac", "1", "-ar", "16000", clip], check=True)
        segs, _ = model.transcribe(_read_wav(clip), language="zh", vad_filter=False)
        heard = "".join(s.text for s in segs)
        heard_s = _t2s(heard)
        cov = coverage(want, heard_s)

        # distinguish real desync from ASR noise: does a neighbouring page fit much better?
        def page_cov(j):
            if j < 0 or j >= len(pages):
                return 0.0
            w = expected_slice(load_marks(a.render_dir, j), local0, local1)
            return coverage(w if len(norm(w)) >= 6 else pages[j]["narration"], heard_s)

        near = max(page_cov(idx - 1), page_cov(idx + 1))
        if cov >= 0.45:
            verdict = "ok"
        elif near - cov > 0.20:
            verdict = "DESYNC"
        elif cov >= ASR_NOISE_FLOOR:
            # 覆盖率达到下限、邻页也没更贴 —— 这才叫 ASR 噪声
            verdict = "asr_noise"
        else:
            # 覆盖率低于下限：基本不是识别噪声，是没对上（2026-11-16 补硬）
            verdict = "low"
        ok = verdict not in ("DESYNC", "low")
        if not ok:
            bad += 1
        rows.append({"t": ts, "page": page.get("id"), "title": page.get("title"),
                     "want": want, "coverage": round(cov, 2), "ok": ok, "verdict": verdict,
                     "neighbour": round(near, 2), "heard": heard.strip()[:60]})
        print(f"{ts:8.2f}s  page {page.get('id'):>5}  cov={cov:.2f} near={near:.2f}  {verdict:<10} "
              f"want={want[:20]} | heard={heard.strip()[:20]}", flush=True)

    rep = sum(1 for r in rows if r["ok"])
    lines = [f"# 音画独立抽检（ASR）", "",
             f"- 素材：`{os.path.basename(video)}`  总长 {total/60:.2f} 分钟 / {len(pages)} 页",
             f"- 方法：随机 {len(rows)} 个时间点，取该点前后共 6 秒音频，用 faster-whisper 转写，"
             f"与「该时刻应用的那一页讲解文本」比对字符二元组覆盖率"
             f"（≥0.45 通过；0.15–0.45 且邻页没更贴算 ASR 噪声；<0.15 判 low 不通过）",
             f"- 结果：**{rep}/{len(rows)} 通过**", "",
             "| 时间点 | 页 | 字幕/讲解标题 | 覆盖率 | 判定 | 听到的片段 |",
             "|---|---|---|---|---|---|"]
    for r in rows:
        mark = "通过" if r["ok"] else f"**不通过（{r['verdict']}）**"
        lines.append(f"| {r['t']:.2f}s | {r['page']} | {r['title']} | {r['coverage']:.2f} | "
                     f"{mark} | {r['heard']} |")
    report = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(report)
        print("report:", a.out)
    print(f"\nPASS {rep}/{len(rows)}  (允许挂 {a.allow_miss} 个)")
    return 0 if rep >= len(rows) - a.allow_miss else 1


if __name__ == "__main__":
    sys.exit(main())
