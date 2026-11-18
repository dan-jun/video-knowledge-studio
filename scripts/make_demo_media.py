#!/usr/bin/env python3
"""Generate the redistribution-safe demo video used by the sample course."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "packs" / "demo" / "media" / "demo.mp4"

SCENES = [
    ("信息不是越短越好", "把事实、画面、时间与因果关系保留下来", "01 · EVIDENCE"),
    ("先把知识连成图", "定义 → 机制 → 例子 → 易错边界 → 主动回忆", "02 · STRUCTURE"),
    ("回到视频核对证据", "点击时间轴，比较笔记与原始画面是否一致", "03 · VERIFY"),
    ("让理解经得起复述", "看视频、读笔记、合上资料，用自己的话重建因果链", "04 · RECALL"),
]


def font(size: int, bold=False):
    candidates = [
        Path(r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def make_scene(index: int, title: str, body: str, kicker: str, path: Path):
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#07111b")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / height
        r = int(6 + 4 * ratio)
        g = int(15 + 10 * ratio)
        b = int(24 + 14 * ratio)
        draw.line((0, y, width, y), fill=(r, g, b))
    for x in range(0, width, 64):
        draw.line((x, 0, x, height), fill=(10, 38, 50))
    for y in range(0, height, 64):
        draw.line((0, y, width, y), fill=(10, 38, 50))
    draw.rounded_rectangle((72, 72, 1208, 648), radius=28, fill="#091925", outline="#1b5363", width=2)
    draw.rounded_rectangle((112, 112, 302, 156), radius=22, fill="#08323b")
    draw.text((132, 122), kicker, font=font(20, True), fill="#6fe8f2")
    draw.text((112, 228), title, font=font(58, True), fill="#effcff")
    draw.multiline_text((112, 342), body, font=font(30), fill="#a7c9d4", spacing=16)
    draw.line((112, 540, 1168, 540), fill="#1b5664", width=2)
    draw.text((112, 574), "VIDEO KNOWLEDGE STUDIO  /  GENERATED DEMO",
              font=font(18, True), fill="#4f9eac")
    draw.text((1050, 574), str(index + 1).zfill(2), font=font(24, True), fill="#70e3ed")
    image.save(path, quality=96)


def main():
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="vks_demo_") as td:
        td = Path(td)
        scene_files = []
        for i, (title, body, kicker) in enumerate(SCENES):
            path = td / f"scene{i + 1}.png"
            make_scene(i, title, body, kicker, path)
            scene_files.append(path)
            if i == 0:
                shutil.copyfile(path, OUT.parent / "poster.png")
        cmd = [ffmpeg, "-y", "-v", "error"]
        for path in scene_files:
            cmd += ["-loop", "1", "-t", "10", "-i", str(path)]
        filters = []
        for i in range(len(scene_files)):
            filters.append(
                f"[{i}:v]scale=1280:720,format=yuv420p,"
                f"fade=t=in:st=0:d=0.6,fade=t=out:st=9.3:d=0.7[v{i}]"
            )
        filters.append("".join(f"[v{i}]" for i in range(len(scene_files))) +
                       f"concat=n={len(scene_files)}:v=1:a=0[v]")
        cmd += [
            "-filter_complex", ";".join(filters), "-map", "[v]",
            "-t", "40", "-r", "30", "-c:v", "libx264", "-preset", "medium",
            "-crf", "22", "-movflags", "+faststart", str(OUT),
        ]
        subprocess.run(cmd, check=True)
    print(OUT)


if __name__ == "__main__":
    main()
