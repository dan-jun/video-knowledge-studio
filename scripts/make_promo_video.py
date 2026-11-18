#!/usr/bin/env python3
"""Create the short product demo from repository screenshots and a real render."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import edge_tts
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
IMAGES = ROOT / "docs" / "images"
BUILD = ROOT / ".promo-build"
OUTPUT = ROOT / "docs" / "media" / "demo-60s.mp4"

sys.path.insert(0, str(ROOT / "production" / "tools"))
from runtime import FFMPEG, FFPROBE, FONT_CJK, FONT_CJK_BOLD, FONT_MONO  # noqa: E402


SCENES = [
    {
        "eyebrow": "THE PROBLEM",
        "title": "你只有几个小时，却要从零补一块知识",
        "body": "搜索、看视频、截图、记笔记、问 AI，最后什么都没连起来。",
        "narration": "你为了一个项目，只有几个小时补一块知识。搜索、看视频、截图、记笔记、问 AI，最后什么都没连起来。",
        "color": "#ffb454",
    },
    {
        "eyebrow": "THE GOAL",
        "title": "不是多看几个视频，而是真正学会",
        "body": "把知识目标、学习路径、证据和练习组织成一个闭环。",
        "image": IMAGES / "before-after.png",
        "narration": "真正的问题不是多看几个视频，而是把学习目标、路径、证据和练习组织成一个闭环。",
        "color": "#56d8f5",
    },
    {
        "eyebrow": "DEMAND-DRIVEN LEARNING",
        "title": "从一个问题，生成一套自己的课程",
        "body": "Agent 规划来源；视频、笔记和 AI 共享同一份知识数据。",
        "image": IMAGES / "workflow-overview.png",
        "narration": "Video Knowledge Studio 从真实学习目标出发。Agent 规划多来源，工作台统一制作视频、笔记和跟随视频的 AI 上下文。",
        "color": "#73e3a5",
    },
    {
        "eyebrow": "LEARN",
        "title": "视频、画面证据、笔记同步",
        "body": "播放高亮知识块；点击时间戳回到讲解；关键结论始终可追溯。",
        "image": IMAGES / "demo.png",
        "narration": "学习时，视频、画面证据和结构化笔记在同一屏同步。播放会高亮知识块，点击时间戳就能回到原片。",
        "color": "#8d7dff",
    },
    {
        "eyebrow": "ASK",
        "title": "选中不懂的句子，直接问 AI",
        "body": "AI 携带当前秒数、附近讲稿和关键画面；修改必须确认并可撤销。",
        "image": IMAGES / "ai-tutor-demo.png",
        "narration": "不懂的地方，直接在右侧选中文字问 AI。它会结合当前秒数、附近讲稿和关键画面回答，修改建议需要你确认，而且可以撤销。",
        "color": "#ffb454",
    },
    {
        "eyebrow": "CREATE",
        "title": "课程不够好？重新制作",
        "body": "remix 单源重制，course 多源整合，scipop 高密度科普。",
        "image": IMAGES / "production-workspace.png",
        "narration": "如果现有课程不适合自己，还可以用 remix 重制、course 多源整合，或用 scipop 制作几分钟的专题。",
        "color": "#56d8f5",
    },
    {
        "eyebrow": "REAL OUTPUT",
        "title": "这是项目真实生成的成片",
        "body": "从规格、门禁、配音到字幕和 MP4，全部在本地完成。",
        "animation": IMAGES / "production-demo.gif",
        "narration": "下面的片段不是设计稿，而是项目实际生成的动画讲解。",
        "color": "#73e3a5",
    },
    {
        "eyebrow": "LOCAL-FIRST",
        "title": "每个人拥有自己的学习空间",
        "body": "课程、项目、批注和修订留在本机。打开 GitHub，一条命令开始。",
        "narration": "课程、项目、批注和修订都保存在自己的电脑上。打开 GitHub，一条命令开始。",
        "color": "#73e3a5",
        "closing": True,
    },
]


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def wrap(draw: ImageDraw.ImageDraw, text: str, face: ImageFont.FreeTypeFont, width: int) -> list[str]:
    lines, current = [], ""
    for char in text:
        candidate = current + char
        if draw.textlength(candidate, font=face) <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = char
    if current:
        lines.append(current)
    return lines


def rounded(image: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", image.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, image.width, image.height), radius, fill=255)
    result = Image.new("RGBA", image.size, (0, 0, 0, 0))
    result.paste(image.convert("RGBA"), mask=mask)
    return result


def make_slide(scene: dict, index: int) -> Path:
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#071016")
    draw = ImageDraw.Draw(image)
    for x in range(0, width, 80):
        draw.line((x, 0, x, height), fill="#102630", width=1)
    for y in range(0, height, 80):
        draw.line((0, y, width, y), fill="#102630", width=1)

    accent = scene["color"]
    draw.rounded_rectangle((44, 38, 84, 78), radius=11, fill="#0b2029", outline=accent, width=2)
    draw.text((56, 47), "V", font=font(FONT_CJK_BOLD, 22), fill=accent)
    draw.text((98, 51), "VIDEO KNOWLEDGE STUDIO", font=font(FONT_MONO, 15), fill="#85a8b5")
    draw.text((920, 51), f"{index + 1:02d} / {len(SCENES):02d}", font=font(FONT_MONO, 14), fill="#577985")

    draw.text((44, 108), scene["eyebrow"], font=font(FONT_MONO, 16), fill=accent)
    title_font = font(FONT_CJK_BOLD, 39 if scene.get("closing") else 35)
    title_lines = wrap(draw, scene["title"], title_font, 1190)
    y = 140
    for line in title_lines:
        draw.text((44, y), line, font=title_font, fill="#effbff")
        y += 49

    body_font = font(FONT_CJK, 20)
    body_lines = wrap(draw, scene["body"], body_font, 1130)
    y += 4
    for line in body_lines:
        draw.text((44, y), line, font=body_font, fill="#9bb7c2")
        y += 31

    show_y = max(260, y + 18)
    if scene.get("image"):
        source_path = scene["image"]
        if source_path.suffix == ".png":
            source = Image.open(source_path).convert("RGB")
        else:
            source = None
        if source:
            available_h = height - show_y - 42
            source.thumbnail((1190, available_h), Image.Resampling.LANCZOS)
            source = rounded(source, 14)
            x = (width - source.width) // 2
            image.paste(source, (x, show_y), source)
    elif scene.get("closing"):
        draw.rounded_rectangle((44, 280, 1236, 510), radius=20, fill="#0b2029", outline="#27505b")
        draw.text((76, 314), "github.com/dan-jun/video-knowledge-studio", font=font(FONT_MONO, 25), fill="#dff8ff")
        draw.text((76, 365), "From a knowledge gap to a course you can actually learn.", font=font(FONT_CJK, 24), fill="#9bb7c2")
        draw.text((76, 430), "Local-first  ·  Agent-ready  ·  MIT", font=font(FONT_MONO, 19), fill=accent)

    draw.line((44, 681, 1236, 681), fill="#1d3d48")
    draw.text((44, 694), "VIDEO → EVIDENCE → NOTES → MASTERY", font=font(FONT_MONO, 12), fill="#5c7c89")
    draw.text((1100, 694), "MIT · 0.2.0", font=font(FONT_MONO, 12), fill=accent)

    path = BUILD / f"slide-{index + 1:02d}.png"
    image.save(path)
    return path


async def synthesize(text: str, path: Path) -> None:
    await edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate="+3%").save(str(path))


def duration(path: Path) -> float:
    result = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


def render_scene(scene: dict, index: int, slide: Path, audio: Path) -> Path:
    seconds = duration(audio) + 0.7
    output = BUILD / f"scene-{index + 1:02d}.mp4"
    if scene.get("animation"):
        source = scene["animation"]
        command = [
            FFMPEG, "-y", "-v", "error", "-stream_loop", "-1", "-i", str(source), "-i", str(audio),
            "-vf", f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=0x071016,fade=t=in:st=0:d=0.25,fade=t=out:st={seconds - 0.25:.2f}:d=0.25",
        ]
    else:
        command = [
            FFMPEG, "-y", "-v", "error", "-loop", "1", "-framerate", "30", "-i", str(slide), "-i", str(audio),
            "-vf", f"fade=t=in:st=0:d=0.25,fade=t=out:st={seconds - 0.25:.2f}:d=0.25",
        ]
    command += [
        "-af", f"apad,afade=t=out:st={duration(audio):.2f}:d=0.45",
        "-t", f"{seconds:.2f}", "-r", "30", "-c:v", "libx264", "-preset", "medium",
        "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", str(output),
    ]
    subprocess.run(command, check=True)
    return output


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    scene_files = []
    for index, scene in enumerate(SCENES):
        slide = make_slide(scene, index)
        audio = BUILD / f"voice-{index + 1:02d}.mp3"
        asyncio.run(synthesize(scene["narration"], audio))
        scene_files.append(render_scene(scene, index, slide, audio))
    concat = BUILD / "concat.txt"
    concat.write_text(
        "\n".join(f"file '{path.as_posix()}'" for path in scene_files) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-c", "copy", "-movflags", "+faststart", str(OUTPUT)],
        check=True,
    )
    print(json.dumps({"ok": True, "video": str(OUTPUT), "duration": duration(OUTPUT)}))


if __name__ == "__main__":
    main()
