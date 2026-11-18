# -*- coding: utf-8 -*-
"""Estimate total runtime BEFORE rendering, and gate the >50 min requirement.

Chinese TTS runs ~230-280 chars/min depending on voice; we calibrate with the two
builds we actually measured (edge-tts zh-CN-XiaoxiaoNeural, MiniMax speech-02-hd@0.87).

Usage:
  python estimate_duration.py <dir-or-files...> [--cpm 250] [--min-min 50]
Exit code 1 when the estimate is under the target.
"""
import argparse
import glob
import json
import os
import sys


def pages_of(path):
    sb = json.load(open(path, encoding="utf-8"))
    return sb.get("pages") or [p for part in sb.get("parts", []) for p in part.get("pages", [])]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("targets", nargs="+")
    ap.add_argument("--cpm", type=float, default=284.0,
                    help="chars per minute of speech (284 = measured: 13947 chars / (2984.5s - 154*0.25s gaps))")
    ap.add_argument("--gap", type=float, default=0.25, help="inter-page gap seconds")
    ap.add_argument("--min-min", type=float, default=50.0)
    a = ap.parse_args()

    files = []
    for t in a.targets:
        if os.path.isdir(t):
            files.extend(sorted(glob.glob(os.path.join(t, "*.json"))))
        else:
            files.append(t)

    total_chars = total_pages = 0
    rows = []
    for f in files:
        pages = pages_of(f)
        chars = sum(len("".join(p.get("narration", "").split())) for p in pages)
        secs = chars / a.cpm * 60 + len(pages) * a.gap
        total_chars += chars
        total_pages += len(pages)
        rows.append((os.path.basename(f), len(pages), chars, secs))

    for name, n, chars, secs in rows:
        print(f"{name:46s} pages={n:3d} chars={chars:5d} ≈{secs/60:5.2f} min")
    total_secs = total_chars / a.cpm * 60 + total_pages * a.gap
    print(f"\nTOTAL files={len(rows)} pages={total_pages} chars={total_chars} "
          f"≈{total_secs/60:.2f} min  (target >{a.min_min:g} min)")
    if total_secs / 60 < a.min_min:
        short = a.min_min - total_secs / 60
        need_chars = int(short * a.cpm)
        print(f"[FAIL] short by {short:.2f} min -> add ~{need_chars} chars "
              f"(≈{need_chars/90:.0f} pages at 90 chars/page)")
        return 1
    print("[OK] estimate clears the target before a single frame is rendered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
