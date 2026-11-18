"""manim 页模板：读 PAGE_SPEC（JSON）→ 画一页 → 垫满 duration。

由 tools/manim_page.py 调用；不要在故事板里直接引用。
"""
import json
import os

from manim import *
WHITE = '#f2f5f8'

SPEC = json.load(open(os.environ["PAGE_SPEC"], encoding="utf-8"))
DUR = float(SPEC.get("duration", 8.0))

# 风格令牌（page["style"] 决定配色与节奏；没有就用默认深色）
TOK = SPEC.get("style_tokens") or {}
BG = TOK.get("bg", "#0e1116")
TEAL = TOK.get("accent", "#5aa9ff")
GREEN = TOK.get("accent2", "#7ee0a8")
DIM = TOK.get("dim", "#8b96a3")
CARD = "#161c24"
FG = TOK.get("fg", "#f2f5f8")
STEP = float(TOK.get("step", 2.0))
VIS = SPEC.get("visual") or {}
VT = VIS.get("type", "bullets")
FONT = "Microsoft YaHei"


def txt(s, size=0.5, color=FG, weight=NORMAL):
    return Text(s, font=FONT, color=color, weight=weight).scale(size)


class Page(Scene):
    def play(self, *args, **kwargs):
        # 节奏封顶：风格决定单步最多多长
        if "run_time" in kwargs:
            kwargs["run_time"] = min(kwargs["run_time"], STEP)
        return super().play(*args, **kwargs)

    def construct(self):
        self.camera.background_color = BG
        title = txt(SPEC.get("title", ""), 0.56, FG, BOLD).to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=0.9)
        self.rule = Line(title.get_left(), title.get_right(), color=DIM, stroke_width=2)
        self.rule.next_to(title, DOWN, buff=0.18)
        self.play(Create(self.rule), run_time=0.3)

        items = VIS.get("items") or []
        steps = VIS.get("steps") or []
        questions = VIS.get("question") or []
        code = VIS.get("code")

        if VT == "diagram" and steps:
            self._diagram(steps)
        elif VT == "code" and code:
            self._code(code, items)
        elif VT == "quiz":
            self._centre_lines(questions or items)
        elif VT == "recap":
            self._rows(items, check=True)
        elif VT == "title":
            self._centre_lines(items)
        else:
            self._rows(items)

        rest = DUR - 0.12 - self.renderer.time
        if rest > 0.05:
            self.wait(rest)

    # ---- 布局方法 ----
    def _rows(self, items, check=False):
        if not items:
            return
        rows = VGroup()
        for i, it in enumerate(items):
            row = VGroup()
            if check:
                c = VGroup(
                    Circle(radius=0.16, color=GREEN, stroke_width=2),
                    Text("✓", font=FONT, color=GREEN).scale(0.3),
                )
                c[1].move_to(c[0])
                row.add(c)
            row.add(txt(it, 0.52, FG))
            row.arrange(RIGHT, buff=0.28, aligned_edge=DOWN)
            rows.add(row)
        rows.arrange(DOWN, buff=0.42, aligned_edge=LEFT).next_to(self.rule, DOWN, buff=0.7)
        rows.shift(LEFT * (rows.width / 2 - 6.2) * 0 if False else RIGHT * 0)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.25), run_time=0.55)

    def _centre_lines(self, lines):
        if not lines:
            return
        g = VGroup(*[txt(x, 0.52, FG) for x in lines]).arrange(DOWN, buff=0.5)
        g.next_to(self.rule, DOWN, buff=1.6)
        for m in g:
            self.play(FadeIn(m, shift=UP * 0.2), run_time=0.6)

    def _diagram(self, steps):
        n = len(steps)
        gap = 0.75
        avail = config.frame_width - 1.6          # 左右各留 0.8 余量
        bw = min(3.2, (avail - (n - 1) * gap) / n)
        bh = 1.9
        boxes = VGroup()
        for s in steps:
            box = VGroup(
                RoundedRectangle(corner_radius=0.12, width=bw, height=bh,
                                 color=TEAL, stroke_width=2).set_fill(CARD, 0.9),
                txt(s, 0.34, FG),
            )
            boxes.add(box)
        boxes.arrange(RIGHT, buff=gap).move_to(DOWN * 0.4)
        arrows = VGroup(*[
            Arrow(boxes[i].get_right(), boxes[i + 1].get_left(), buff=0.12,
                  color=TEAL, stroke_width=3, max_tip_length_to_length_ratio=0.18)
            for i in range(n - 1)
        ])
        for i, b in enumerate(boxes):
            self.play(FadeIn(b, scale=0.9), run_time=0.45)
            if i < len(arrows):
                self.play(GrowArrow(arrows[i]), run_time=0.35)

    def _code(self, code, items):
        block = Code(
            code_string=code,
            language="python",
            formatter_style="monokai",
            background="window",
            add_line_numbers=False,
        ).scale(0.85).move_to(DOWN * 0.4)
        block.to_edge(LEFT, buff=0.9)
        self.play(Create(block), run_time=1.2)
        if items:
            g = VGroup(*[txt(it, 0.36, DIM) for it in items]).arrange(DOWN, buff=0.3, aligned_edge=LEFT)
            g.next_to(block, RIGHT, buff=0.6)
            for m in g:
                self.play(FadeIn(m), run_time=0.4)
