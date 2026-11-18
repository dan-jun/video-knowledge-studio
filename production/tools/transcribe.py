# -*- coding: utf-8 -*-
"""把视频（本地路径或链接）转成带时间轴的逐字稿。

后端已换成 D 盘的「yt-dlp × faster-whisper」管道（GPU）：
  - 现在 **支持 B站等链接**，平台没字幕也能转录
  - 有 GPU 就用 GPU，通常 15–20× 实时
  - 输出契约不变：transcript.json = [{start,end,text}]、transcript.txt = "[mm:ss.xx] 文本"
  - 额外产出 transcript.srt / transcript.vtt / report.md

管道不可用（或装坏了）会自动回退到原来的 CPU int8 实现，工坊不会因此瘫掉。

用法：
    python transcribe.py <本地文件 或 URL> <输出目录> [--lang zh] [--model small] [--fix "错=对,..."] [--legacy]
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from asr_bridge import transcribe  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("outdir")
    ap.add_argument("--lang", default="zh")
    ap.add_argument("--model", default=None, help="whisper 模型（tiny/base/small/medium），默认 small")
    ap.add_argument("--fix", default=None, help='同音字校正表，如 "分业=分页,快表=块表"')
    ap.add_argument("--glossary", action="append", default=None,
                    help="额外术语表文件（可多次）；管道自带 glossary.txt 会自动加载")
    ap.add_argument("--legacy", action="store_true", help="强制用老的 CPU 实现")
    ap.add_argument("--polish", action="store_true",
                    help="转录后导出校音请求（单字同音交给模型修；改完跑 polish.py apply）")
    a = ap.parse_args()

    kw = {"lang": a.lang, "force_legacy": a.legacy}
    if a.polish:
        kw["polish"] = True
    if a.model:
        kw["model"] = a.model
    if a.fix:
        kw["fix"] = a.fix
    if a.glossary:
        kw["glossary"] = a.glossary
    r = transcribe(a.src, a.outdir, **kw)
    print(json.dumps(r, ensure_ascii=False))


if __name__ == "__main__":
    main()
