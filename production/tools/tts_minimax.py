# -*- coding: utf-8 -*-
"""MiniMax T2A v2 adapter.

Endpoint note: this key only works on the INTERNATIONAL host (`api.minimax.io`).
`api.minimaxi.com` / `api.minimax.chat` return 2049/1004 for it.

Timing note: MiniMax returns a sentence-level `subtitle_file` (one entry per clause with
`time_begin`/`time_end` in ms). We fetch it with `curl --ssl-no-revoke` because this
machine's revocation check fails against the OSS host. `align_chars()` then interpolates
per-character time inside each clause, so bullet reveals stay speech-synced.
"""
import json
import os
import subprocess
import urllib.request

API = os.environ.get("MINIMAX_API_URL", "https://api.minimax.io/v1/t2a_v2")
KEY_PATH = os.environ.get("MINIMAX_KEY_FILE", "")


def _key():
    inline = os.environ.get("MINIMAX_API_KEY", "").strip()
    if inline:
        return inline
    if KEY_PATH and os.path.isfile(KEY_PATH):
        with open(KEY_PATH, encoding="utf-8") as handle:
            return handle.read().strip()
    raise RuntimeError(
        "MiniMax API key is missing. Set MINIMAX_API_KEY or MINIMAX_KEY_FILE."
    )


def synthesize(text, voice_id=None, model=None, speed=None,
               fmt="mp3", sample_rate=32000):
    """Returns (audio_bytes, [(t0_sec, dur_sec, clause_text), ...])."""
    voice_id = voice_id or os.environ.get(
        "MINIMAX_TTS_VOICE", "female-yujie"
    )
    model = model or os.environ.get("MINIMAX_TTS_MODEL", "speech-02-hd")
    speed = float(
        os.environ.get("MINIMAX_TTS_SPEED", "1.08")
        if speed is None else speed
    )
    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "voice_setting": {"voice_id": voice_id, "speed": speed, "vol": 1.0, "pitch": 0},
        "audio_setting": {"sample_rate": sample_rate, "bitrate": 128000,
                          "format": fmt, "channel": 1},
        "subtitle_enable": True,
    }
    req = urllib.request.Request(
        API, data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        body = json.loads(r.read().decode("utf-8"))
    br = body.get("base_resp", {})
    if br.get("status_code") != 0:
        raise RuntimeError(f"MiniMax error {br.get('status_code')}: {br.get('status_msg')}")
    data = body.get("data") or {}
    audio = bytes.fromhex(data.get("audio") or "")
    marks = []
    sub_url = data.get("subtitle_file")
    if sub_url:
        tmp = os.path.join(os.environ.get("TEMP", "/tmp"), "mm_sub.json")
        p = subprocess.run(["curl", "-sS", "--ssl-no-revoke", "--max-time", "40",
                            "-o", tmp, sub_url], capture_output=True, text=True)
        if p.returncode == 0 and os.path.exists(tmp):
            try:
                for it in json.load(open(tmp, encoding="utf-8")):
                    t0 = float(it["time_begin"]) / 1000.0
                    t1 = float(it["time_end"]) / 1000.0
                    txt = it.get("text") or it.get("pronounce_text") or ""
                    if txt.strip():
                        marks.append((t0, max(0.05, t1 - t0), txt))
            except Exception:  # noqa: BLE001
                marks = []
    return audio, marks


if __name__ == "__main__":
    a, m = synthesize("测试一下 MiniMax 音色。")
    print("audio bytes:", len(a), "clauses:", len(m))
    for t0, d, txt in m[:3]:
        print(f"  {t0:.2f}s +{d:.2f}s {txt}")
