# -*- coding: utf-8 -*-
"""把「yt-dlp × faster-whisper」管道桥接成视频工坊的转录后端。

为什么要有这一层：
  - 工坊原来的 transcribe.py 只认本地文件，B站链接进不来 → 无字幕的片子没法涅槃
  - 原来固定 CPU/int8，一批片子要等到地老天荒
  - 原来只出 transcript.json/txt，没有 srt、没有术语校正

这一层负责：
  1. 调 D 盘的 vt.py（GPU + yt-dlp 下载 + 术语校正）干活
  2. 把它的输出**转成工坊契约**：transcript.json = [{start,end,text}]，transcript.txt = "[mm:ss.xx] 文本"
  3. vt.py 不可用时回退到老实现（CPU int8），保证工坊不会因为这套装没装而瘫

环境变量：
  VIDEO_ASR_HOME   可选的外部 GPU 转录管道目录
  VIDEO_ASR_MODEL  模型（默认 small）
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

ASR_HOME = os.environ.get("VIDEO_ASR_HOME") or ""
VT_PY = os.path.join(ASR_HOME, ".venv", "Scripts", "python.exe")
VT_PY = os.environ.get("VIDEO_ASR_PYTHON") or VT_PY
VT_SCRIPT = os.path.join(ASR_HOME, "vt.py")
DEFAULT_MODEL = os.environ.get("VIDEO_ASR_MODEL") or "small"


def pipeline_available() -> bool:
    return os.path.isfile(VT_SCRIPT) and os.path.isfile(VT_PY)


def _mmss(sec: float) -> str:
    return f"[{int(sec // 60):02d}:{sec % 60:05.2f}]"


def _write_contract(segments: list[dict], outdir: str) -> None:
    """按工坊契约落盘：下游 coverage_check / cites 都按这个格式读。"""
    rows = [{"start": round(float(s["start"]), 2),
             "end": round(float(s["end"]), 2),
             "text": (s.get("text") or "").strip()} for s in segments if (s.get("text") or "").strip()]
    with open(os.path.join(outdir, "transcript.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    with open(os.path.join(outdir, "transcript.txt"), "w", encoding="utf-8") as f:
        for r in rows:
            f.write(f"{_mmss(r['start'])} {r['text']}\n")


def run_pipeline(src: str, outdir: str, lang: str = "zh",
                 model: str = DEFAULT_MODEL, max_height: int = 480,
                 fix: str | None = None, glossary: list[str] | None = None,
                 polish: bool = False, timeout: int = 7200) -> dict:
    """调外部管道转写。src 可以是 URL（B站/本地路径都行）。"""
    os.makedirs(outdir, exist_ok=True)
    raw_dir = os.path.join(outdir, "_asr_raw")
    cmd = [VT_PY, VT_SCRIPT, src, "-o", raw_dir, "-l", lang, "-m", model,
           "--max-height", str(max_height)]
    if fix:
        cmd += ["--fix", fix]
    for g in glossary or []:
        cmd += ["--glossary", g]
    if polish:
        cmd += ["--polish"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"转写管道失败（exit={proc.returncode}）：{(proc.stderr or proc.stdout or '')[-800:]}")

    raw_json = os.path.join(raw_dir, "transcript.json")
    if not os.path.isfile(raw_json):
        raise RuntimeError(f"管道跑完但没找到 {raw_json}")
    data = json.load(open(raw_json, encoding="utf-8"))
    result = data.get("result", {})
    segments = result.get("segments", [])

    _write_contract(segments, outdir)

    # srt/report 也搬到工坊目录顶层，方便直接塞进剪辑软件
    for name in ("transcript.srt", "report.md", "transcript.vtt"):
        s = os.path.join(raw_dir, name)
        if os.path.isfile(s):
            with open(s, "rb") as fi, open(os.path.join(outdir, name), "wb") as fo:
                fo.write(fi.read())

    return {
        "ok": True,
        "backend": "whisper-pipeline",
        "segments": len(segments),
        "duration": round(float(result.get("duration") or data.get("probe", {}).get("duration") or 0), 1),
        "elapsed": result.get("elapsed"),
        "speedup": result.get("speedup"),
        "language": result.get("language"),
        "outdir": outdir,
        "raw_dir": raw_dir,
    }


# ── 回退实现（原 transcribe.py 的逻辑，CPU int8） ─────────────────────────

from runtime import FFMPEG as FF

LEGACY_MODEL = os.environ.get("VKS_WHISPER_MODEL") or "small"


def run_legacy(src: str, outdir: str, lang: str = "zh") -> dict:
    os.makedirs(outdir, exist_ok=True)
    wav = os.path.join(tempfile.gettempdir(), "remix_audio.wav")
    subprocess.run([FF, "-y", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav], check=True)

    import wave

    import numpy as np
    with wave.open(wav, "rb") as wf:
        raw = wf.readframes(wf.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

    from faster_whisper import WhisperModel
    model = WhisperModel(LEGACY_MODEL, device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio, language=lang or "zh", vad_filter=True,
                                      vad_parameters={"min_silence_duration_ms": 400})
    rows = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments if s.text.strip()]
    _write_contract(rows, outdir)
    return {"ok": True, "backend": "legacy-cpu", "segments": len(rows),
            "duration": round(info.duration, 1), "outdir": outdir}


def transcribe(src: str, outdir: str, lang: str = "zh", model: str = DEFAULT_MODEL,
               fix: str | None = None, force_legacy: bool = False,
               glossary: list[str] | None = None, polish: bool = False) -> dict:
    """统一入口：优先 GPU 管道，失败或不可用则回退 CPU。"""
    if not force_legacy and pipeline_available():
        try:
            return run_pipeline(src, outdir, lang=lang, model=model, fix=fix,
                                glossary=glossary, polish=polish)
        except Exception as e:  # noqa: BLE001
            print(f"[asr] 管道失败，回退 CPU：{type(e).__name__}: {e}", file=sys.stderr)
    return run_legacy(src, outdir, lang=lang)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python asr_bridge.py <src 路径或链接> <outdir> [lang]")
        raise SystemExit(2)
    print(json.dumps(transcribe(sys.argv[1], sys.argv[2],
                                lang=(sys.argv[3] if len(sys.argv) > 3 else "zh")),
                     ensure_ascii=False))
