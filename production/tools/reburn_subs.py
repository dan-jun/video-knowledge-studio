# -*- coding: utf-8 -*-
"""只重烧字幕：merged.mkv + subs.srt -> final_hardsub.mp4，不重渲动画。"""
import os
import subprocess
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from paths import resolve_out
from runtime import FFMPEG

FF = FFMPEG

STYLES = {
    "a": "FontName=Microsoft YaHei,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
         "BackColour=&H66000000,BorderStyle=3,Outline=0,Shadow=0,Alignment=2,MarginV=24",
    "b": "FontName=Microsoft YaHei,FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
         "BackColour=&H66000000,BorderStyle=3,Outline=0,Shadow=0,Alignment=2,MarginV=18",
    "c": "FontName=Microsoft YaHei,FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
         "BackColour=&H73000000,BorderStyle=3,Outline=0,Shadow=0,Alignment=2,MarginV=14",
}


def main():
    proj = resolve_out(sys.argv[1])
    key = sys.argv[2] if len(sys.argv) > 2 else "a"
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(proj, f"test_{key}.mp4")
    merged = os.path.join(proj, "merged.mkv")
    srt = os.path.join(proj, "subs.srt")
    srt_esc = srt.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    style = STYLES[key]
    subprocess.run([FF, "-y", "-v", "error", "-i", merged, "-vf",
                    f"subtitles='{srt_esc}':force_style='{style}'",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", out], check=True)
    print("ok ->", out)


if __name__ == "__main__":
    main()
