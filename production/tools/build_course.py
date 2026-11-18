# -*- coding: utf-8 -*-
"""End-to-end course build from rendered chapter videos.

Usage:
  python build_course.py outdir \
      --seg "out/chapter-AB|out/chapter-AB/chapters.json" \
      --seg "out/chapter-C|out/chapter-C/chapters.json" ...

Does:
  1. concat all segment videos in order with -c copy  -> master.mp4
  2. build a GLOBAL chapters.json (labels + absolute times)
  3. build player.html
  4. split master into one mp4 per chapter (分 P)
  5. verify: master duration == sum(segments), and 分P sum == master
"""
import argparse
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_out  # noqa: E402
import os
import shutil
import subprocess

from runtime import FFMPEG, FFPROBE
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed: {r.stderr[-600:]}")
    return r.stdout


def dur(path):
    return float(run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", path]).strip())


def safe(name):
    for ch in '<>:"/\\|?*':
        name = name.replace(ch, "-")
    return name.strip()[:60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--seg", action="append", required=True, help="video|chapters.json")
    ap.add_argument("--no-split", action="store_true",
                    help="each --seg already is one chapter: copy parts instead of re-encoding")
    a = ap.parse_args()
    a.outdir = resolve_out(a.outdir)

    segs = []
    for spec in a.seg:
        video, chj = spec.split("|", 1)
        if not os.path.exists(video):
            raise SystemExit(f"missing video: {video}")
        if not os.path.exists(chj):
            raise SystemExit(f"missing chapters: {chj}")
        segs.append((os.path.abspath(video), json.load(open(chj, encoding="utf-8"))))

    os.makedirs(a.outdir, exist_ok=True)
    listfile = os.path.join(a.outdir, "concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for v, _ in segs:
            f.write(f"file '{v.replace(os.sep, '/')}'\n")

    master = os.path.join(a.outdir, "master.mp4")
    run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", listfile,
         "-c", "copy", master])

    # global chapter table
    chapters, seg_rows, t = [], [], 0.0
    for v, chs in segs:
        d = dur(v)
        for c in chs:
            chapters.append({"label": c["label"], "t": round(t + float(c["t"]), 3)})
        seg_rows.append({"file": os.path.basename(v), "start": round(t, 3), "len": round(d, 3)})
        t += d
    total = dur(master)
    drift = abs(total - t)

    ch_path = os.path.join(a.outdir, "chapters.json")
    json.dump(chapters, open(ch_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    player = os.path.join(a.outdir, "player.html")
    run([PY, os.path.join(HERE, "build_player.py"), master, ch_path, player])

    # split into 分 P
    parts_dir = os.path.join(a.outdir, "parts")
    os.makedirs(parts_dir, exist_ok=True)
    rows = []
    if a.no_split:
        # Fast path: each segment already IS one chapter -> copy, never re-encode.
        for i, (video, chs) in enumerate(segs):
            if len(chs) != 1:
                raise SystemExit(f"--no-split needs 1 chapter per segment; {os.path.basename(video)} "
                                 f"has {len(chs)}")
            label = chs[0]["label"]
            name = f"P{i + 1:02d}-{safe(label)}.mp4"
            path = os.path.join(parts_dir, name)
            shutil.copy2(video, path)
            rows.append({"part": i + 1, "label": label, "start": round(chapters[i]["t"], 3),
                         "len": round(dur(path), 3), "file": name, "reencoded": False})
    else:
        for i, c in enumerate(chapters):
            start = float(c["t"])
            end = float(chapters[i + 1]["t"]) if i + 1 < len(chapters) else total
            length = max(0.1, end - start)
            name = f"P{i + 1:02d}-{safe(c['label'])}.mp4"
            path = os.path.join(parts_dir, name)
            run([FFMPEG, "-y", "-v", "error", "-ss", f"{start:.3f}", "-i", master,
                 "-t", f"{length:.3f}",
                 "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                 "-c:a", "aac", "-b:a", "160k", path])
            rows.append({"part": i + 1, "label": c["label"], "start": round(start, 3),
                         "len": round(dur(path), 3), "file": name, "reencoded": True})

    rep = {"segments": seg_rows, "sum_segments": round(t, 3), "master": round(total, 3),
           "drift": round(drift, 3), "minutes": round(total / 60, 2),
           "chapters": chapters, "parts": rows,
           "paths": {"master": master, "chapters": ch_path, "player": player, "parts": parts_dir}}
    json.dump(rep, open(os.path.join(a.outdir, "build-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    for r in rows:
        print(f"P{r['part']:02d} {r['start']:8.2f}s +{r['len']:7.2f}s  {r['label'][:34]}")
    print(f"\nsegments={len(segs)} chunks, {len(chapters)} chapters")
    print(f"sum_segments={t:.3f}s master={total:.3f}s drift={drift:.3f}s -> {total/60:.2f} min")
    print(f"parts_sum={sum(r['len'] for r in rows):.3f}s")
    if drift > 0.3:
        raise SystemExit(f"FAIL drift {drift:.3f}s > 0.3s")
    if total < 50 * 60:
        print(f"WARN: {total/60:.2f} min < 50 min")
    print("master :", master)
    print("player :", player)
    print("parts  :", parts_dir)


if __name__ == "__main__":
    main()
