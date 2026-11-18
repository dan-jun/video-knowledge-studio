# -*- coding: utf-8 -*-
"""Assemble the course: concat chapter mp4s -> master, chapters.json, player.html.

Usage:
  python assemble_course.py out_dir --part "label|path/to/chapter.mp4" --part "..." ...

Writes:
  out_dir/master.mp4          lossless concat (stream copy)
  out_dir/chapters.json       [{label, t}] for the player
  out_dir/assemble-report.json
  out_dir/player.html
"""
import argparse
import json
import os
import subprocess

from runtime import FFMPEG, FFPROBE
HERE = os.path.dirname(os.path.abspath(__file__))


def dur(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True)
    return float(r.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("outdir")
    ap.add_argument("--part", action="append", required=True, help='label|mp4path')
    a = ap.parse_args()

    items = []
    for spec in a.part:
        label, path = spec.split("|", 1)
        if not os.path.exists(path):
            raise SystemExit(f"missing chapter file: {path}")
        items.append((label.strip(), os.path.abspath(path)))

    os.makedirs(a.outdir, exist_ok=True)
    listfile = os.path.join(a.outdir, "concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        for _, p in items:
            f.write(f"file '{p.replace(os.sep, '/')}'\n")

    master = os.path.join(a.outdir, "master.mp4")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", listfile, "-c", "copy", master], check=True)

    chapters, t = [], 0.0
    rows = []
    for label, p in items:
        d = dur(p)
        chapters.append({"label": label, "t": round(t, 3)})
        rows.append({"label": label, "file": os.path.basename(p), "len": round(d, 3), "start": round(t, 3)})
        t += d
    total = dur(master)
    drift = abs(total - t)

    ch_path = os.path.join(a.outdir, "chapters.json")
    json.dump(chapters, open(ch_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    player = os.path.join(a.outdir, "player.html")
    subprocess.run([os.path.join(HERE, "..", ".venv", "Scripts", "python.exe"),
                    os.path.join(HERE, "build_player.py"), master, ch_path, player], check=True)

    rep = {"parts": rows, "sum_parts": round(t, 3), "master": round(total, 3),
           "drift": round(drift, 3), "minutes": round(total / 60, 2),
           "chapters": ch_path, "player": player, "master_path": master}
    json.dump(rep, open(os.path.join(a.outdir, "assemble-report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    for r in rows:
        print(f"{r['start']:8.2f}s +{r['len']:7.2f}s  {r['label'][:30]:32s} {r['file']}")
    print(f"\nsum_parts={t:.3f}s master={total:.3f}s drift={drift:.3f}s "
          f"({total/60:.2f} min) parts={len(rows)}")
    if drift > 0.3:
        raise SystemExit(f"FAIL: master drift {drift:.3f}s > 0.3s")
    if total < 50 * 60:
        print(f"WARN: master {total/60:.2f} min < 50 min target")
    print("chapters:", ch_path)
    print("player  :", player)


if __name__ == "__main__":
    main()
