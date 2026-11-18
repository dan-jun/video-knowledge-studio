# -*- coding: utf-8 -*-
"""QA 抽帧拼图：每页取 30%/65%/92% 三帧，拼成 contact sheet。

用法：python tools/contact_sheet.py <merged.mkv> <build-report.json> <outdir>
输出：outdir/sheet1.png ...（并在 stdout 打印每张的绝对路径）
"""
import json
import os
import subprocess

from PIL import Image, ImageDraw, ImageFont
from runtime import FFMPEG, FONT_CJK

FF = FFMPEG
FONT = FONT_CJK
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def main(merged, report, outdir):
    os.makedirs(outdir, exist_ok=True)
    rep = json.load(open(report, encoding="utf-8"))
    t0, stamps = 0.0, []
    for seg in rep["segments"]:
        dur = float(seg.get("video") or seg.get("expect") or 0)
        for frac in (0.30, 0.65, 0.92):
            stamps.append((round(t0 + dur * frac, 1), seg.get("seg")))
        t0 += dur

    frames = []
    for i, (t, segno) in enumerate(stamps):
        p = os.path.join(outdir, f"f{i:03d}_{t}.png")
        subprocess.run([FF, "-y", "-v", "error", "-ss", str(t), "-i", merged,
                        "-frames:v", "1", p], check=True, creationflags=NO_WINDOW)
        frames.append((p, f"p{segno}@{t}s"))

    f = ImageFont.truetype(FONT, 24)
    cols, rows, tw, th = 3, 3, 720, 405
    per = cols * rows
    for s in range(0, len(frames), per):
        chunk = frames[s:s + per]
        img = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
        d = ImageDraw.Draw(img)
        for i, (p, lab) in enumerate(chunk):
            im = Image.open(p).resize((tw, th))
            x, y = (i % cols) * tw, (i // cols) * th
            img.paste(im, (x, y))
            d.text((x + 10, y + 8), lab, font=f, fill=(255, 200, 60))
        out = os.path.join(outdir, f"sheet{s // per + 1}.png")
        img.save(out)
        print(out)


if __name__ == "__main__":
    import sys
    main(sys.argv[1], sys.argv[2], sys.argv[3])
