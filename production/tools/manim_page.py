# -*- coding: utf-8 -*-
"""把 storyboard 的一页渲染成一段 manim 视频（页级接入）。

用法（build_video.py 内部调用）：
    from manim_page import render_page
    mp4 = render_page(page_dict, duration_sec, workdir)

依赖：.venv-manim（manim 0.22.1）。输出 1920x1080@30fps，长度≈duration。
"""
import json
import os
import shutil
import subprocess
import sys
import uuid

from runtime import FONT_CJK_NAME

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MANIM_PY = os.environ.get("VF_MANIM_PY") or sys.executable
SCENE_SRC = os.path.join(HERE, "manim_page_scene.py")


def render_page(page, duration, workdir, timeout=600):
    workdir = os.path.abspath(workdir)
    os.makedirs(workdir, exist_ok=True)
    tag = uuid.uuid4().hex[:8]
    scene_dir = os.path.join(workdir, f"page_{tag}")
    os.makedirs(scene_dir, exist_ok=True)
    scene_dir = os.path.abspath(scene_dir)
    scene_file = os.path.join(scene_dir, f"scene_{tag}.py")
    custom = page.get("scene")
    scene_class = "Page"
    if custom:
        # 自定义场景：page["scene"] = "scenes/xxx.py:ClassName"
        rel, _, cls = custom.partition(":")
        src = rel if os.path.isabs(rel) else os.path.join(ROOT, rel)
        shutil.copyfile(src, scene_file)
        scene_class = cls or "Page"
    else:
        shutil.copyfile(SCENE_SRC, scene_file)

    from styles import tokens_for
    spec = {
        "title": page.get("title", ""),
        "duration": round(float(duration), 3),
        "visual": page.get("visual") or {},
        "style_tokens": tokens_for(page.get("style")),
    }
    spec_path = os.path.join(scene_dir, "spec.json")
    json.dump(spec, open(spec_path, "w", encoding="utf-8"), ensure_ascii=False)

    env = dict(os.environ)
    latex = shutil.which("latex")
    if latex:
        env["PATH"] = os.path.dirname(latex) + os.pathsep + env.get("PATH", "")
    env.setdefault("VKS_FONT_CJK_NAME", FONT_CJK_NAME)
    env["PAGE_SPEC"] = spec_path
    env["PYTHONIOENCODING"] = "utf-8"
    _h = int(os.environ.get("VF_H", "1080"))
    _w = int(round(_h * 16 / 9))
    r = subprocess.run(
        [MANIM_PY, "-m", "manim", "-r", f"{_w},{_h}", "--fps", "30",
         "--disable_caching", os.path.basename(scene_file), scene_class],
        cwd=scene_dir, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    if r.returncode != 0:
        detail = ((r.stdout or "") + "\n--- stderr ---\n" + (r.stderr or ""))
        raise RuntimeError("manim page failed:\n" + detail[-1500:])

    produced = os.path.join(scene_dir, "media", "videos",
                            os.path.splitext(os.path.basename(scene_file))[0],
                            f"{_h}p30", f"{scene_class}.mp4")
    if not os.path.exists(produced):
        raise RuntimeError("manim output missing: " + produced)
    return produced


if __name__ == "__main__":
    import sys
    page = json.load(open(sys.argv[1], encoding="utf-8"))
    out = render_page(page, float(sys.argv[3]) if len(sys.argv) > 3 else 8.0,
                      os.path.join(HERE, "_manim_pages"))
    print("rendered:", out)
