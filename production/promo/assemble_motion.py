"""Assemble animated English promo with genuine recorded product interactions.

Render animated_english.py first, and capture the English recordings using the
existing promo recording scripts. Intermediate clips remain in ignored directories.
"""
from pathlib import Path
import json
import subprocess

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUILD = HERE / "build-motion"
MOTION = HERE / "render-motion/videos/animated_english/1080p30"
RECORD = HERE / "recordings-en"
OLD_SCENES = HERE / "render_en/videos/manim_scenes/1080p30"
OUTPUT = ROOT / "docs/media/product-demo-en-motion.mp4"
FONT = "C:/Windows/Fonts/segoeuib.ttf"


def run(args):
    subprocess.run(args, check=True)


def length(path):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], text=True).strip())


def title_card(label, detail, path, top=965):
    image = Image.new("RGBA", (1920, 1080))
    draw = ImageDraw.Draw(image)
    draw.text((82, top + 10), label, font=ImageFont.truetype(FONT, 26), fill=(102, 237, 245, 255))
    draw.text((82, top + 48), detail, font=ImageFont.truetype(FONT, 19), fill=(237, 248, 250, 255))
    image.save(path)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    segments = []

    def motion(name):
        src = MOTION / f"{name}.mp4"
        out = BUILD / f"{name}.mp4"
        run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-an", "-vf", "fps=30,setsar=1,format=yuv420p", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", str(out)])
        segments.append(out)

    def recording(name, start, secs, label, detail, crop):
        src = RECORD / f"{name}.webm"
        index = len(segments)
        out = BUILD / f"ui-{index}.mp4"
        overlay = BUILD / f"label-{index}.png"
        title_card(label, detail, overlay)
        w, h, x, y = crop
        filters = (f"[0:v]setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=1920:940:force_original_aspect_ratio=decrease:flags=lanczos,"
                   "pad=1920:1080:(ow-iw)/2:10:color=0x071017,fps=30,setsar=1[vid];"
                   "[1:v]format=rgba,fade=t=in:st=0.1:d=0.35:alpha=1[label];"
                   "[vid][label]overlay=0:0:shortest=1,format=yuv420p[out]")
        run(["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", str(src), "-loop", "1", "-i", str(overlay),
             "-filter_complex", filters, "-map", "[out]", "-t", str(secs), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", str(out)])
        segments.append(out)

    def evidence(y, height, seconds, label, detail):
        src = RECORD / "learning-final.png"
        out = BUILD / f"evidence-{len(segments)}.mp4"
        overlay = BUILD / f"evidence-label-{len(segments)}.png"
        title_card(label, detail, overlay)
        # A fixed crop keeps the evidence legible without shaking a moving UI.
        filt = (f"[0:v]crop=700:{height}:1208:{y},scale=1560:950:force_original_aspect_ratio=decrease:flags=lanczos,"
                "pad=1920:1080:(ow-iw)/2:10:color=0x071017,fps=30,setsar=1[vid];"
                "[1:v]format=rgba,fade=t=in:st=0.1:d=0.35:alpha=1[label];"
                "[vid][label]overlay=0:0:shortest=1,format=yuv420p[out]")
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str(src), "-loop", "1", "-i", str(overlay),
             "-filter_complex", filt, "-map", "[out]", "-t", str(seconds), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", str(out)])
        segments.append(out)

    def lesson():
        src = OLD_SCENES / "RaftLesson.mp4"
        out = BUILD / "lesson.mp4"
        overlay = BUILD / "lesson-label.png"
        title_card("SHORT EXAMPLE LESSON", "Raft helps servers agree on an ordered history of changes", overlay)
        filt = "[0:v]setpts=PTS-STARTPTS,scale=1920:940:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:10:color=0x071017,fps=30,setsar=1[v];[1:v]format=rgba[label];[v][label]overlay=0:0:shortest=1,format=yuv420p[out]"
        run(["ffmpeg", "-y", "-v", "error", "-ss", "1.4", "-i", str(src), "-loop", "1", "-i", str(overlay), "-filter_complex", filt, "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", str(out)])
        segments.append(out)

    motion("MotionOpening")
    motion("MotionPlan")
    motion("MotionSync")
    recording("learning", 3.0, 7.5, "REAL WORKSPACE", "Raft: a way for servers to agree on changes", (1920, 1080, 0, 0))
    motion("MotionContext")
    recording("learning", 9.5, 2.8, "ASK IN CONTEXT", "Select a passage in the notes", (1920, 1080, 0, 0))
    evidence(500, 275, 4.5, "REVIEW THE ANSWER", "Read the explanation and its timestamps")
    evidence(775, 275, 4.5, "YOU CONTROL THE EDIT", "Accept, reject, or keep a note")
    motion("MotionGraph")
    motion("MotionCreate")
    recording("production", 16.0, 2.3, "REAL PRODUCTION WORKSPACE", "Preview the rendered lesson", (1920, 1080, 0, 0))
    lesson()
    motion("MotionClose")

    listing = BUILD / "clips.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in segments), encoding="utf-8")
    silent = BUILD / "silent.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(listing), "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-an", str(silent)])
    seconds = length(silent)
    run(["ffmpeg", "-y", "-v", "error", "-i", str(silent), "-stream_loop", "-1", "-i", str(HERE / "music/close-up.mp3"),
         "-map", "0:v", "-map", "1:a", "-t", str(seconds), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
         "-af", f"afade=t=in:st=0:d=0.6,afade=t=out:st={seconds-1.8:.3f}:d=1.8,loudnorm=I=-16:LRA=9:TP=-1.5", "-shortest", "-movflags", "+faststart", str(OUTPUT)])
    print(json.dumps({"output": str(OUTPUT), "duration": length(OUTPUT), "segments": len(segments)}))


if __name__ == "__main__":
    main()
