#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""anim_gen —— 从 JSON 规格生成「storyboard.json + 可运行的 manim 场景文件」。

这是阶段 2 的核心：把「写稿」和「写动画代码」拆开。
  稿子（narration）由人/模型写；画面由 anim_kit 的手法函数按规格装配，不用逐集写 Manim 代码。

用法：
    python tools/anim_gen.py spec.json            # 生成 storyboard + scenes
    python tools/anim_gen.py spec.json --check    # 生成后跑缺字/覆盖门禁

规格（spec.json）：
{
  "topic": "kv-cache",
  "title": "为什么需要 KV Cache",
  "style": "AvgusTa",
  "voice": "zh-CN-XiaoxiaoNeural",
  "source": "https://...",          # 可选，写进 agent.json
  "pages": [
    {"id":"c01","type":"title","title":"...","narration":"..."},
    {"id":"c02","type":"kit","kit":"bar_chart","args":{"data":[["1x",1.0],["8x",5.6]]},
     "title":"...","narration":"..."},
    {"id":"c03","type":"kit","kit":"node_network","args":{"layers":[3,4,4,1]},
     "title":"...","narration":"..."},
    {"id":"c04","type":"bullets","title":"...","narration":"...","items":["a","b"]},
    {"id":"c05","type":"quiz","title":"练一题","narration":"...可以暂停三秒...","question":["...","A.","B."]},
    {"id":"c06","type":"answer","title":"答案","narration":"...","items":["..."]},
    {"id":"c07","type":"recap","title":"复盘","narration":"我们回顾一下。...","items":["..."]}
  ]
}

支持的 kit 手法：question / bottom_note / bar_chart / node_network / numline /
state_machine / timeline / stack_layers / weighted_sum / formula_lines /
two_columns / utilization_grid / chip / cell_row / matrix_grid
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

from runtime import OUT_ROOT as RUNTIME_OUT_ROOT

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT_ROOT = pathlib.Path(RUNTIME_OUT_ROOT)

KIT_FUNCS = {
    "question", "bottom_note", "bar_chart", "node_network", "numline",
    "state_machine", "timeline", "stack_layers", "weighted_sum",
    "formula_lines", "two_columns", "utilization_grid",
    "gradient_sequence", "stacked_bar", "dual_axis_chart",
    "zoom_sequence", "isomorphic_pair", "cache_blocks",
    "two_ends", "pipeline3", "qkv_colors", "annotation_board",
    "recurrence_to_matrix", "token_strip",
    # 2026-11-14 补齐：三维 / 形变 / 双栏同步 / 像素 / 曲线 / 矢量场
    "space_3d", "morph_pair", "split_formula_figure",
    "pixel_grid", "conv_slide", "curve_grow", "vector_field_2d",
    "ray_split", "spectrum_strip",
}

# 需要 3D 场景基类的手法
KIT_3D = {"space_3d"}

HEADER = '''"""自动生成场景：{title}

由 tools/anim_gen.py 从 {spec_name} 生成，手法来自 tools/anim_kit。
改动请改 spec.json 后重新生成，不要手改本文件。
"""
import json
import os
import sys

from manim import *

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools"))
try:
    from anim_kit import Base, Base3D, kit
except ImportError:                                  # 备用：绝对路径
    sys.path.insert(0, r"{kit_dir}")
    from anim_kit import Base, Base3D, kit

SPEC = json.load(open(os.environ["PAGE_SPEC"], encoding="utf-8"))

# 背景色必须在 Scene 初始化前设到 config（camera 背景在初始化时生成，后改不生效）
_BG = (SPEC.get("style_tokens") or {{}}).get("bg")
if _BG:
    config.background_color = _BG


'''

CLASS_TMPL = '''class {cls}({base}):
    """{title}"""

    def construct(self):
        self.setup()
        {head}
{body}
        self.tail()


'''


def _py(v):
    """JSON 值 → Python 字面量（null/true/false 必须转成 None/True/False）。"""
    if v is None:
        return "None"
    if v is True:
        return "True"
    if v is False:
        return "False"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_py(x) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{_py(k)}: {_py(x)}" for k, x in v.items()) + "}"
    return repr(v)


def _fmt_args(args):
    """把 JSON 参数渲染成 python 字面量（保持可读）。"""
    if not args:
        return ""
    parts = []
    for k, v in args.items():
        parts.append(f"{k}={_py(v)}")
    return ",\n                      ".join(parts)


def flat_pages(spec):
    """支持两种 spec：单层 pages，或多章 parts:[{part, pages}]。返回所有页。"""
    if spec.get("parts"):
        out = []
        for pt in spec["parts"]:
            out.extend(pt.get("pages", []))
        return out
    return spec.get("pages", [])


def build_scene(spec, spec_name):
    lines = [HEADER.format(title=spec["title"],
                           spec_name=spec_name,
                           kit_dir=str(ROOT / "tools"))]
    for i, page in enumerate(flat_pages(spec), 1):
        cls = f"P{i:02d}"
        kind = page.get("type")
        body_lines = []
        if kind == "kit":
            body_lines.append("        kit.bg_grid(self)")
            if page.get("tag"):
                body_lines.append(f'        kit.corner_tag(self, {_py(page["tag"])})')
            fn = page["kit"]
            if fn not in KIT_FUNCS:
                raise SystemExit(f"[anim_gen] 未知手法：{fn}（可用：{sorted(KIT_FUNCS)}）")
            args = page.get("args") or {}
            # 位置参数支持：args 里的 "_pos" 列表
            pos = args.pop("_pos", [])
            arg_s = ", ".join(_py(x) for x in pos)
            kw = _fmt_args(args)
            call = f"        kit.{fn}(self"
            call += (", " + arg_s) if arg_s else ""
            call += (",\n                      " + kw) if kw else ""
            call += ")"
            body_lines.append(call)
            if page.get("note"):
                body_lines.append(f'        kit.bottom_note(self, {json.dumps(page["note"], ensure_ascii=False)})')
        head_call = "" if page.get("kit") == "question" else "self.head()"
        base_cls = "Base3D" if page.get("kit") in KIT_3D else "Base"
        lines.append(CLASS_TMPL.format(cls=cls, base=base_cls, title=page.get("title", ""),
                                       head=head_call,
                                       body="\n".join(body_lines) if body_lines else "        pass"))
    return "\n".join(lines), [f"P{i:02d}" for i in range(1, len(flat_pages(spec)) + 1)]


def build_storyboard(spec, topic, cls_names):
    """支持单层 pages 与多章 parts；page 的 scene 类名按「全局页序号」对应。"""

    def _one(page, idx):
        pid = page["id"]
        kind = page.get("type")
        base = {"id": pid, "title": page.get("title", ""),
                "narration": page.get("narration", ""), "style": spec["style"]}
        if page.get("cites"):
            base["cites"] = page["cites"]
        if page.get("kp"):
            base["kp"] = page["kp"]
        if kind == "kit":
            # 类名必须与「全局页序号」严格对应（P01=第1页…），不能用 kit 页计数
            _vis = {"type": "kit", "kit": page.get("kit")}
            if page.get("kp"):
                _vis["kp"] = page["kp"]
            if page.get("technique") or page.get("kit"):
                _vis["technique"] = page.get("technique") or page.get("kit")
            base.update({"renderer": "manim",
                         "scene": f"scenes/gen_{topic}.py:P{idx:02d}",
                         "visual": _vis})
        elif kind == "bullets":
            base["visual"] = {"type": "bullets", "items": page.get("items", [])}
        elif kind == "quiz":
            base["visual"] = {"type": "quiz", "question": page.get("question", [])}
        elif kind == "answer":
            base["visual"] = {"type": "answer", "items": page.get("items", [])}
        elif kind == "recap":
            base["visual"] = {"type": "recap", "items": page.get("items", [])}
        elif kind == "code":
            base["visual"] = {"type": "code", "code": page.get("code", "")}
        else:
            base["visual"] = {"type": "title"}
        if page.get("cites"):
            base["cites"] = page["cites"]
        return base

    parts = []
    idx = 1
    if spec.get("parts"):
        for pt in spec["parts"]:
            pages = []
            for page in pt.get("pages", []):
                pages.append(_one(page, idx))
                idx += 1
            parts.append({"part": pt.get("part", "正文"), "pages": pages})
    else:
        pages = []
        for page in spec.get("pages", []):
            pages.append(_one(page, idx))
            idx += 1
        parts = [{"part": spec.get("part", "正文"), "pages": pages}]

    storyboard = {"topic": topic, "title": spec["title"],
                  "voice": spec.get("voice", "zh-CN-XiaoxiaoNeural"),
                  "parts": parts}
    if spec.get("sources"):
        storyboard["sources"] = spec["sources"]
    return storyboard



def scaffold(kp, style=None):
    """知识点 → 草稿 spec：决策器定路径，注册表给函数与参数模板。

    产出的是「骨架」：页面结构、kit 函数、参数占位符都填好，
    但讲解稿（narration）仍要人来写——这是当前的分工线。
    """
    import subprocess
    sys.path.insert(0, str(ROOT / "tools"))
    import anim_advisor as A
    import path_templates as PT

    res = A.advice(kp, str(pathlib.Path(RUNTIME_OUT_ROOT) / "_anim_corpus"))
    top = res["plans"][0]["path"]
    tmpl = PT.get(top) or PT.PATH_TEMPLATES["P1"]
    _cite = ["TODO 【出处：教材章节 / 论文 / 原片 hh:mm:ss】"]
    pages = [{"id": "c01", "type": "title", "title": kp, "cites": _cite,
              "narration": "【开场：用一句话说清这一集要解决什么】"}]
    n = 2
    for item in tmpl["funcs"]:
        fn = item["fn"]
        if fn not in KIT_FUNCS:
            continue
        pages.append({"id": f"c{n:02d}", "type": "kit", "kit": fn,
                      "args": item["args"], "title": f"【第{n}页标题】",
                      "narration": "【这一页怎么讲：40–80 字】",
                      "cites": ["TODO 【出处：教材章节 / 论文 / 原片 hh:mm:ss】"]})
        n += 1
    pages.append({"id": f"c{n:02d}", "type": "quiz", "cites": _cite, "title": "练一题",
                  "narration": "停一下做道题。【题目口播】可以暂停三秒想一想，我们接着看答案。",
                  "question": ["【题目】", "A. 【选项A】", "B. 【选项B】"]})
    pages.append({"id": f"c{n+1:02d}", "type": "answer", "cites": _cite, "title": "答案",
                  "narration": "答案是【X】。【为什么】"})
    pages.append({"id": f"c{n+2:02d}", "type": "recap", "cites": _cite, "title": "复盘",
                  "narration": "我们回顾一下。第一，【要点1】。第二，【要点2】。第三，【要点3】。",
                  "items": ["【要点1】", "【要点2】", "【要点3】"]})
    spec = {"topic": "draft", "title": kp, "style": style or res["plans"][0]["style"],
            "part": "草稿", "keys": "【知识点覆盖清单，用 | 分隔关键词】",
            "transcript": "【原文讲稿】", "pages": pages}
    return spec, top, res


def _save_agent(proj, meta):
    """写 agent.json 时保留已有自定义字段（src_duration / sources / fixture）。"""
    import os as _os
    path = _os.path.join(str(proj), "agent.json")
    old = {}
    try:
        if _os.path.exists(path):
            old = json.load(open(path, encoding="utf-8")) or {}
    except Exception:
        old = {}
    merged = {**{k: v for k, v in old.items() if k not in meta}, **meta}
    json.dump(merged, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return merged


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", default=None)
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--project", default=None, help="写入这个现有项目目录")
    ap.add_argument("--check", action="store_true", help="生成后跑 glyph/coverage 门禁")
    ap.add_argument("--scaffold", metavar="知识点", default=None,
                    help="不生成文件，只把「知识点 → 草稿 spec」打印出来")
    ap.add_argument("--style", default=None, help="配合 --scaffold 指定风格")
    ap.add_argument("--mode", default=None, choices=["scipop", "course", "remix"],
                    help="分片类型：--check 按该分区跑专属检查（不传只跑通用门禁）")
    a = ap.parse_args()

    if a.scaffold:
        _spec, _pid, _res = scaffold(a.scaffold, a.style)
        print(f"判定类型：{_res['kp_types'][:3]}  推荐路径：{_pid}（{_res['plans'][0]['path_name']}）")
        print(json.dumps(_spec, ensure_ascii=False, indent=2))
        return

    spec_path = pathlib.Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    topic = spec["topic"]
    if not a.mode:
        print("[anim_gen] 注意：未指定 --mode，只跑通用门禁；"
              "分区特有规则（视觉密度/练习密度/cites）不会被检查", file=sys.stderr)
    root = pathlib.Path(a.out_root) if a.out_root else OUT_ROOT
    proj = pathlib.Path(a.project).resolve() if a.project else root / f"remix-{topic}"
    (proj / "src").mkdir(parents=True, exist_ok=True)
    (ROOT / "scenes").mkdir(parents=True, exist_ok=True)

    # 场景文件写到项目内（渲染器按 project 相对路径找 scenes/）
    code, cls_names = build_scene(spec, spec_path.name)
    scene_file = ROOT / "scenes" / f"gen_{topic}.py"
    scene_file.write_text(code, encoding="utf-8")

    sb = build_storyboard(spec, topic, cls_names)
    (proj / "storyboard.json").write_text(json.dumps(sb, ensure_ascii=False, indent=2), encoding="utf-8")

    aj = {"mode": a.mode or "remix", "title": spec["title"], "label": spec.get("label", "生成器产物"),
          "stage": "transcribed",
          "source": {"local": spec.get("source", "")},
          "sources": spec.get("sources", []),
          "params": {"target_min": [0, 999], "gap": 0.25, "mm_speed": 0.85,
                     "quiz": True, "recap": True}}
    _save_agent(proj, aj)   # 保留 src_duration / sources / fixture 等已回填字段

    if spec.get("keys"):
        (proj / "keys.txt").write_text(spec["keys"], encoding="utf-8")
    if spec.get("transcript"):
        (proj / "src" / "transcript.txt").write_text(spec["transcript"], encoding="utf-8")

    if spec.get("glossary"):
        glossary_py = ROOT / "tools" / "glossary_check.py"
        r_glossary = subprocess.run(
            [sys.executable, str(glossary_py), str(spec_path), "--project", str(proj)],
            capture_output=True, text=True, encoding="utf-8",
        )
        line = (r_glossary.stdout or r_glossary.stderr or "").strip().splitlines()
        print("  " + (line[-1] if line else "术语检查无输出"))
        if r_glossary.returncode != 0:
            return r_glossary.returncode

    n_pages = len(flat_pages(spec))
    n_kit = sum(1 for p in flat_pages(spec) if p.get("type") == "kit")
    print(f"[anim_gen] {proj}")
    print(f"  页数 {n_pages}（kit {n_kit} 页）→ {scene_file.name} / storyboard.json")

    if a.check:
        py = sys.executable
        ok = True
        r1 = subprocess.run([py, str(ROOT / "tools" / "glyph_check.py"), str(proj / "storyboard.json")],
                            capture_output=True, text=True, encoding="utf-8")
        print("  " + (r1.stdout.strip().splitlines() or ["glyph_check 无输出"])[-1])
        ok &= r1.returncode == 0
        # 多音字门禁：配音前必过（edge-tts/MiniMax 都不支持拼音标注，只能改文案）
        r0 = subprocess.run([py, str(ROOT / "tools" / "polyphone.py"), "check",
                            str(proj / "storyboard.json"), "--strict"],
                           capture_output=True, text=True, encoding="utf-8")
        try:
            pj = json.loads(r0.stdout or "{}")
            hi = pj.get("high_risk", 0)
            words = sorted({i["word"] for i in pj.get("items", []) if i.get("risk") == "高"})
            print(f"  多音字：命中 {pj.get('hits', 0)}｜高风险 {hi}"
                  + (f"（{'、'.join(words[:5])}）" if words else ""))
        except Exception:
            print("  多音字：解析失败")
        ok &= r0.returncode == 0

        if (proj / "keys.txt").exists():
            r2 = subprocess.run([py, str(ROOT / "tools" / "coverage_check.py"),
                                 str(proj / "storyboard.json"), "--keys", str(proj / "keys.txt")],
                                capture_output=True, text=True, encoding="utf-8")
            m = re.search(r"覆盖 \d+/\d+", r2.stdout)
            print("  " + (m.group(0) if m else "覆盖率解析失败"))
            ok &= r2.returncode == 0
        # 分区专属检查（视觉密度 / 练习密度 / cites / 时长区间 …）
        if a.mode:
            sys.path.insert(0, str(ROOT / "tools"))
            from modes import check as mode_check
            res = mode_check(str(proj), a.mode)
            print(f"  分区[{a.mode}] {res.get('label','')}：{'通过' if res['ok'] else '有未通过项'}")
            for item in res["results"]:
                if item["status"] == "fail":
                    print(f"    [!!] {item['rule']}")
                    for e in item["errors"]:
                        print(f"         - {e}")
                elif item["status"] == "manual":
                    print(f"    [--] {item['rule']}（人工/其余阶段）")
                else:
                    print(f"    [OK] {item['rule']} — {item['detail']}")
            ok &= res["ok"]
        else:
            print("  (未指定 --mode，跳过分区检查)")
        print("  门禁:", "通过" if ok else "有问题")
    return 0


def _cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", nargs="?", help="spec json 路径")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--scaffold", metavar="知识点", help="从知识点生成草稿 spec")
    ap.add_argument("--style", default=None)
    a = ap.parse_args()
    if a.scaffold:
        spec, path_id, res = scaffold(a.scaffold, a.style)
        print(f"判定类型：{res['kp_types'][:3]}  推荐路径：{path_id}")
        print(json.dumps(spec, ensure_ascii=False, indent=2))
        return 0
    return None


if __name__ == "__main__":
    sys.exit(main())
