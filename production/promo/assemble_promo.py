from __future__ import annotations

import subprocess
import urllib.request
from pathlib import Path


HERE = Path(__file__).resolve().parent
STUDIO = HERE.parents[1]
SCENES = HERE / "render" / "videos" / "manim_scenes" / "1080p30"
RECORDINGS = HERE / "recordings"
BUILD = HERE / "build"
CLIPS = BUILD / "clips"
FINAL = STUDIO / "docs" / "media" / "product-demo.mp4"
POSTER = STUDIO / "docs" / "images" / "product-demo-poster.png"
MUSIC_CACHE = HERE / "music" / "close-up.mp3"
MUSIC_URL = "https://assets.mixkit.co/music/1167/1167.mp3"

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
    vf = (
        f"crop={width}:{height}:{x}:{y},"
        f"scale={WIDTH}:{HEIGHT}:flags=lanczos,"
        f"fps={FPS},setsar=1"
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


def prepare_music(total: float, target: Path) -> None:
    if not MUSIC_CACHE.is_file():
        MUSIC_CACHE.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MUSIC_URL, MUSIC_CACHE)
    fade_out_start = max(0.0, total - 1.8)
    run([
        FFMPEG, "-y", "-hide_banner", "-loglevel", "error",
        "-stream_loop", "-1", "-i", str(MUSIC_CACHE), "-t", f"{total:.3f}",
        "-af",
        f"afade=t=in:st=0:d=0.65,afade=t=out:st={fade_out_start:.3f}:d=1.8,volume=0.82",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", str(target),
    ])


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(parents=True, exist_ok=True)
    FINAL.parent.mkdir(parents=True, exist_ok=True)
    POSTER.parent.mkdir(parents=True, exist_ok=True)

    ordered: list[Path] = []
    for scene in (
        "UseCaseIntro",
        "WorkflowSpine",
        "DifferenceOverview",
    ):
        ordered.append(normalize_scene(scene))

    ordered.append(normalize_screen("learning", 1.0, 12.6))
    ordered.append(freeze_crop("learning-final.png", (1188, 676, 712, 400), 4.0))
    ordered.append(normalize_scene("KnowledgeNetwork"))
    ordered.append(normalize_scene("ContextStatement"))
    ordered.append(normalize_scene("ThreeModes"))
    ordered.append(normalize_screen("production", 1.1, 13.1))
    ordered.append(freeze_crop("production-frames/t12.5.png", (1220, 300, 590, 332), 4.0))
    ordered.append(normalize_scene("DifferenceBridge"))
    ordered.append(normalize_scene("RaftLesson"))
    ordered.append(normalize_scene("FinalRecap"))

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
    score = BUILD / "licensed-score.wav"
    prepare_music(total, score)

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
