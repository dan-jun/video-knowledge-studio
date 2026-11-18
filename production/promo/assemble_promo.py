from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[1]
SCENES = HERE / "render" / "videos" / "manim_scenes" / "1080p30"
RECORDINGS = HERE / "recordings"
BUILD = HERE / "build"
CLIPS = BUILD / "clips"
FINAL = STUDIO / "docs" / "media" / "product-demo.mp4"
POSTER = STUDIO / "docs" / "images" / "product-demo-poster.png"

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
WIDTH = 1920
HEIGHT = 1080
FPS = 30


def run(args: list[str]) -> None:
    subprocess.run(args, check=True)


def normalize_scene(name: str, speed: float = 1.0) -> Path:
    source = SCENES / f"{name}.mp4"
    target = CLIPS / f"{name}.mp4"
    vf = f"fps={FPS},scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2,setsar=1"
    if speed != 1.0:
        vf = f"setpts=(PTS-STARTPTS)/{speed}," + vf
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source), "-an", "-vf", vf,
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), str(target),
    ])
    return target


def normalize_screen(
    name: str,
    start: float,
    end: float,
    speed: float = 1.0,
    framed: bool = True,
) -> Path:
    source = RECORDINGS / f"{name}.webm"
    target = CLIPS / f"{name}_{start:g}_{end:g}_{speed:g}.mp4"
    filters = []
    if speed != 1.0:
        filters.append(f"setpts=(PTS-STARTPTS)/{speed}")
    filters.append(f"fps={FPS}")
    if name == "output":
        filters.extend([
            "crop=1248:702:336:0",
            "scale=1920:1080:flags=lanczos",
        ])
    elif framed:
        filters.extend([
            "scale=1760:990:force_original_aspect_ratio=decrease",
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#05070A",
            "drawbox=x=80:y=45:w=1760:h=990:color=#315368@0.7:t=2",
        ])
    else:
        filters.extend([
            "scale=1920:1080:force_original_aspect_ratio=decrease",
            "pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=#05070A",
        ])
    filters.append("setsar=1")
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", str(start), "-to", str(end), "-i", str(source),
        "-an", "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), str(target),
    ])
    return target


def freeze_screen(name: str, seconds: float) -> Path:
    source = RECORDINGS / name
    target = CLIPS / f"{source.stem}_freeze.mp4"
    frames = int(seconds * FPS)
    vf = (
        f"scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={WIDTH}:{HEIGHT}:(ow-iw)/2:(oh-ih)/2:color=#05070A,"
        f"zoompan=z='min(zoom+0.00045,1.075)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},setsar=1"
    )
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(source), "-t", str(seconds), "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), str(target),
    ])
    return target


def freeze_crop(name: str, crop: tuple[int, int, int, int], seconds: float) -> Path:
    source = RECORDINGS / name
    x, y, width, height = crop
    target = CLIPS / f"{source.stem}_crop.mp4"
    frames = int(seconds * FPS)
    vf = (
        f"crop={width}:{height}:{x}:{y},"
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,"
        f"zoompan=z='min(zoom+0.00025,1.035)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS},setsar=1"
    )
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(source), "-t", str(seconds), "-vf", vf,
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), str(target),
    ])
    return target


def duration(path: Path) -> float:
    text = subprocess.check_output([
        FFPROBE, "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", str(path),
    ], text=True).strip()
    return float(text)


def make_original_score(total: float, target: Path) -> None:
    sr = 48000
    n = int(math.ceil(total * sr))
    t = np.arange(n, dtype=np.float64) / sr
    rng = np.random.default_rng(20261118)
    mix = np.zeros(n, dtype=np.float64)

    bpm = 110.0
    beat = 60.0 / bpm
    eighth = beat / 2.0

    def add(signal: np.ndarray, at: float, gain: float = 1.0) -> None:
        start = max(0, int(at * sr))
        if start >= n:
            return
        count = min(len(signal), n - start)
        mix[start:start + count] += signal[:count] * gain

    # Warm four-note pad. The sequence changes slowly so cuts remain the focus.
    chords = [
        [55.00, 82.41, 110.00, 164.81],
        [49.00, 73.42, 98.00, 146.83],
        [43.65, 65.41, 87.31, 130.81],
        [55.00, 82.41, 110.00, 164.81],
    ]
    pad_gain = np.interp(
        t,
        [0, 6, 18, 55, 70, total - 5, total],
        [0.08, 0.24, 0.20, 0.14, 0.24, 0.30, 0.0],
    )
    for idx, freqs in enumerate(chords):
        chord_t0 = idx * 4 * beat
        while chord_t0 < total:
            local_len = min(4 * beat, total - chord_t0)
            local_n = int(local_len * sr)
            if local_n <= 0:
                break
            local_t = np.arange(local_n) / sr
            env = np.sin(np.pi * np.minimum(local_t / 0.45, 1.0))
            env *= np.exp(-0.2 * local_t)
            block = np.zeros(local_n)
            for freq in freqs:
                block += np.sin(2 * np.pi * freq * local_t)
                block += 0.18 * np.sin(2 * np.pi * freq * 2.003 * local_t)
            start = int(chord_t0 * sr)
            count = min(local_n, n - start)
            mix[start:start + count] += block[:count] * env[:count] * pad_gain[start:start + count] * 0.018
            chord_t0 += 4 * beat

    # Kick, sub pulse and tight high ticks carry the reference-like edit rhythm.
    kick_t = 0.0
    while kick_t < total:
        local_n = int(0.34 * sr)
        local_t = np.arange(local_n) / sr
        freq = 47 + 25 * np.exp(-local_t * 24)
        phase = 2 * np.pi * np.cumsum(freq) / sr
        body = np.sin(phase) * np.exp(-local_t * 11)
        section = 0.75 if kick_t < 55 else 1.0
        add(body, kick_t, 0.165 * section)
        kick_t += beat

    tick_t = 3.0
    while tick_t < total:
        local_n = int(0.045 * sr)
        local_t = np.arange(local_n) / sr
        tick = rng.normal(0, 1, local_n) * np.exp(-local_t * 95)
        # First difference gives a crisp, inexpensive high-pass.
        tick = np.diff(np.r_[0.0, tick])
        add(tick, tick_t, 0.025)
        tick_t += eighth

    # Short UI ticks through the real-product portions.
    for sec in np.arange(43, total - 5, 0.67):
        local_n = int(0.028 * sr)
        local_t = np.arange(local_n) / sr
        click = np.sin(2 * np.pi * 1850 * local_t) * np.exp(-local_t * 130)
        add(click, float(sec), 0.012)

    # Low impacts mark semantic transitions.
    for at in [0.0, 5.6, 11.2, 17.4, 28.0, 49.5, 58.5, 72.5, 84.5, total - 4.0]:
        local_n = int(0.8 * sr)
        local_t = np.arange(local_n) / sr
        freq = 38 + 35 * np.exp(-local_t * 6)
        phase = 2 * np.pi * np.cumsum(freq) / sr
        boom = np.sin(phase) * np.exp(-local_t * 4.2)
        add(boom, at, 0.11)

    # Airy rises under concept-to-screen transitions.
    for at in [18.5, 55.0, 78.0]:
        local_n = int(0.8 * sr)
        local_t = np.arange(local_n) / sr
        noise = rng.normal(0, 1, local_n)
        phase = 2 * np.pi * (200 * local_t + 700 * local_t ** 2)
        whoosh = 0.5 * noise + 0.5 * np.sin(phase)
        whoosh *= np.sin(np.pi * local_t / 0.8) ** 2
        add(whoosh, at, 0.018)

    # Gentle global movement and a clean fade at both ends.
    mix *= 0.86 + 0.14 * np.sin(2 * np.pi * 0.055 * t)
    fade_in = np.clip(t / 0.7, 0, 1)
    fade_out = np.clip((total - t) / 1.5, 0, 1)
    mix *= fade_in * fade_out
    peak = np.max(np.abs(mix)) or 1.0
    stereo = np.column_stack([mix / peak * 0.78, mix / peak * 0.78])
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(str(target), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sr)
        handle.writeframes(pcm.tobytes())


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(parents=True, exist_ok=True)
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    POSTER.parent.mkdir(parents=True, exist_ok=True)

    ordered: list[Path] = []
    for scene in (
        "Opening",
        "Promise",
        "LearningChain",
        "EvidenceLoop",
    ):
        ordered.append(normalize_scene(scene))

    ordered.append(normalize_screen("learning", 1.0, 13.5))
    ordered.append(normalize_screen("learning", 13.5, 27.1, speed=2.2))
    ordered.append(freeze_crop("learning-final.png", (1188, 676, 712, 400), 4.0))
    ordered.append(normalize_scene("KnowledgeNetwork"))
    ordered.append(normalize_scene("ContextStatement"))
    ordered.append(normalize_scene("ThreeModes"))
    ordered.append(normalize_screen("production", 1.1, 13.1))
    ordered.append(freeze_crop("production-frames/t12.5.png", (1220, 300, 590, 332), 4.0))
    ordered.append(normalize_scene("ProductionStatement"))
    ordered.append(normalize_screen("output", 1.5, 14.0, framed=False))
    ordered.append(normalize_scene("Finale"))

    concat_file = BUILD / "clips.txt"
    concat_file.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in ordered) + "\n",
        encoding="utf-8",
    )
    silent = BUILD / "product-demo-silent.mp4"
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-r", str(FPS), "-an", str(silent),
    ])
    total = duration(silent)
    score = BUILD / "original-score.wav"
    make_original_score(total, score)

    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(silent), "-i", str(score),
        "-c:v", "libx264", "-preset", "slow", "-crf", "22",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "160k", "-ar", "48000",
        "-af", "loudnorm=I=-16:LRA=9:TP=-1.5",
        "-shortest", "-movflags", "+faststart", str(FINAL),
    ])
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-ss", "23.5", "-i", str(FINAL), "-frames:v", "1", str(POSTER),
    ])
    print({
        "final": str(FINAL),
        "poster": str(POSTER),
        "duration": duration(FINAL),
        "clips": len(ordered),
    })


if __name__ == "__main__":
    main()
