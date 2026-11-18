"""anim_kit —— 把蒸馏出来的「教学手法」变成可调用的 Manim 代码。

设计原则：
  1. 每个函数 = 一个手法（F1/F4/F7/F8/F10/F16/F17…），参数化、与题材无关
  2. 自动吃 style_tokens（PAGE_SPEC），换风格只改令牌不改编排
  3. 所有时间调用走 Base.play（带预算裁剪），场景不会超时

用法（生成器产出的场景文件里）：
    from anim_kit import Base, kit
    class Page01(Base):
        def construct(self):
            self.setup(); self.head()
            kit.bar_chart(self, [("batch=1",1.0),("batch=8",5.6)], color=self.tok("accent"))
            kit.bottom_note(self, "权重复用 → 吞吐更高")
            self.tail()
"""
import os
import re
import sys
import time

from manim import *

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from runtime import CJK_FONT_NAME, FONT_HAND
try:
    from mathtex import render_formula
except Exception:                                    # mathtex 可选
    render_formula = None

CJK_FONT = CJK_FONT_NAME
KAI_FONT = FONT_HAND or CJK_FONT_NAME


# ─────────────────────────── 基类 ───────────────────────────
class Base(Scene):
    """统一处理：背景色、时间预算、标题、收尾补齐。"""

    def setup(self):
        # 关键：只设 camera.background_color 不够——相机背景在 Scene 初始化时已按
        # config.background_color 生成，后改不会刷新（实测仍是 #0D1117）。两处都要设。
        _bg = self.tok("bg", "#0D1117")
        config.background_color = _bg
        self.camera.background_color = _bg
        try:
            # 相机背景在初始化时生成，必须显式重建，否则还是主题默认色
            self.camera.set_background(color=_bg)
        except Exception:
            pass
        self.t0 = time.time()
        self.budget = max(4.0, self.dur * 0.85)
        self.used = 0.0
        self._step = float(self.tok("step", 1.5))

    @property
    def spec(self):
        """PAGE_SPEC 在**场景模块**里加载，不能读 anim_kit 的 globals。"""
        mod = sys.modules.get(self.__class__.__module__)
        if mod is not None:
            spec = getattr(mod, "SPEC", None)
            if spec:
                return spec
        return globals().get("SPEC", {})

    @property
    def dur(self):
        return float(self.spec.get("duration", 20.0))

    def tok(self, key, default=None):
        t = self.spec.get("style_tokens") or {}
        return t.get(key, default)

    def play(self, *args, **kwargs):
        rt = float(kwargs.get("run_time", 1.0))
        left = max(0.12, self.budget - self.used)
        rt = min(rt, self._step, left)
        self.used += rt
        kwargs["run_time"] = rt
        return super().play(*args, **kwargs)

    def head(self, text=None):
        t = self.spec.get("title", "") if text is None else text
        if not t:
            return
        m = Text(t, font=CJK_FONT, color=self.tok("fg", "#eaf2f8"), weight=BOLD).scale(0.44)
        m.to_edge(UP, buff=0.42)
        self.play(Write(m), run_time=0.7)

    def tail(self):
        rest = self.dur - (time.time() - self.t0) - 0.4
        if rest > 0.2:
            self.wait(rest)

    # 便捷取色
    def fg(self):
        return self.tok("fg", "#eaf2f8")

    def accent(self):
        return self.tok("accent", "#58C4DD")

    def accent2(self):
        return self.tok("accent2", "#F08A24")

    def dim(self):
        return self.tok("dim", "#4E6B7A")


# ─────────────────────────── 基础零件 ───────────────────────────
def text(s, size=0.4, color=None, font=CJK_FONT, weight=NORMAL):
    return Text(s, font=font, color=color or "#FFFFFF", weight=weight).scale(size)


def formula(tex, color="#FFFFFF", height=0.7):
    """公式渲染：**优先真 LaTeX（MathTex）**，不可用时退回 matplotlib mathtext。

    安装 TeX Live 时 MathTex 可用，排版为 TeX 级
    （分数、求和极限、bmatrix、根号、\\top 全支持）。
    没有 TeX 的机器上自动降级到 mathtext（不支持 \\begin{...} 环境）。
    """
    try:
        m = MathTex(tex, color=color)
        if m.height > 0:
            m.height = height
            return m
    except Exception:
        pass
    if "\\begin{" in tex:
        import re as _re
        def _mat(mo):
            rows = [r.strip() for r in mo.group(1).split("\\\\")]
            cells = ["[" + ", ".join(c.strip() for c in r.split("&")) + "]" for r in rows]
            return "[" + ", ".join(cells) + "]"
        tex = _re.sub(r"\\begin\{bmatrix\}(.*?)\\end\{bmatrix\}", _mat, tex, flags=_re.S)
        tex = tex.replace("\\", "").replace("{", "").replace("}", "")
    if render_formula is None:
        return text(tex, height * 0.6, color)
    try:
        path = render_formula(tex, color=color, fontsize=40)
        img = ImageMobject(path)
        img.height = height
        return img
    except Exception:
        return text(tex, height * 0.6, color)


def chip(s, color, size=0.34, font=CJK_FONT):
    """圆角标签（闪客的「作者/飞天/闪客」那种）。"""
    t = Text(s, font=font, color="#FFFFFF").scale(size)
    box = RoundedRectangle(corner_radius=0.12, width=t.width + 0.34, height=t.height + 0.24,
                           fill_color=color, fill_opacity=1, stroke_width=0)
    t.move_to(box)
    return VGroup(box, t)


def cell_row(values, color, n=None, cell=0.28, gap=0.05, hollow_below=None):
    """一行方格（值 → 深浅）。values 可为数字列表或 0/1。"""
    n = n or len(values)
    vmax = max(values) if values else 1
    group = VGroup()
    for i in range(n):
        v = values[i] if i < len(values) else 0
        op = 0.12 + 0.85 * (v / vmax if vmax else 0)
        sq = Square(side_length=cell, stroke_width=1.2, stroke_color=color,
                    fill_color=color, fill_opacity=op)
        group.add(sq)
    group.arrange(RIGHT, buff=gap)
    return group


def matrix_grid(rows, cols, color, cell=0.3, gap=0.05):
    g = VGroup()
    for r in range(rows):
        row = VGroup(*[Square(side_length=cell, stroke_width=1, stroke_color=color,
                              fill_color=color, fill_opacity=0.15) for _ in range(cols)])
        row.arrange(RIGHT, buff=gap)
        g.add(row)
    g.arrange(DOWN, buff=gap)
    return g


def highlight_box(mobj, color="#5FD08A", buff=0.2):
    return SurroundingRectangle(mobj, color=color, buff=buff, stroke_width=3)


# ─────────────────────────── 手法函数 ───────────────────────────
def question(scene, s, color=None):
    """F1 一屏一问句（放大居中，避免整屏空荡）。"""
    kicker = text("本集问题", 0.3, scene.dim()).move_to([0, 1.75, 0])
    q = text(s, 0.62, color or scene.fg(), weight=BOLD).move_to([0, 0.45, 0])
    u = Line([-3.4, -0.15, 0], [3.4, -0.15, 0], color=scene.accent(), stroke_width=3)
    mark = text("?", 1.1, scene.accent2()).move_to([0, -1.35, 0])
    scene.play(FadeIn(kicker), run_time=0.6)
    scene.play(Write(q), run_time=1.0)
    scene.play(Create(u), run_time=0.4)
    scene.play(FadeIn(mark, shift=DOWN * 0.2), run_time=0.6)
    return VGroup(kicker, q, u, mark)


def bottom_note(scene, s, color=None, size=0.32):
    t = text(s, size, color or scene.dim()).to_edge(DOWN, buff=1.3)
    scene.play(FadeIn(t), run_time=0.8)
    return t


def bar_chart(scene, data, colors=None, base_y=-1.55, unit="x", max_h=3.0):
    """F10 条形图量级对比。data: [(label, value, color?)]"""
    vals = [d[1] for d in data]
    vmax = max(vals) or 1
    n = len(data)
    width = min(1.2, 4.4 / max(1, n))
    step = 8.6 / max(1, n)
    axis = Line([-4.6, base_y, 0], [4.6, base_y, 0], color=scene.dim(), stroke_width=2)
    scene.play(Create(axis), run_time=0.5)
    bars = VGroup()
    for i, d in enumerate(data):
        label, val = d[0], d[1]
        col = d[2] if len(d) > 2 else (colors[i] if colors else scene.accent())
        h = max(0.15, val / vmax * max_h)
        bar = Rectangle(width=width, height=h, fill_color=col, fill_opacity=0.85, stroke_width=0)
        bar.move_to([-4.3 + step * (i + 0.5), base_y + h / 2, 0])
        lab = text(f"{label}", 0.3, col).next_to(bar, DOWN, buff=0.14)
        num = text(f"{val:g}{unit}", 0.32, col).next_to(bar, UP, buff=0.12)
        scene.play(GrowFromEdge(bar, DOWN), FadeIn(lab), FadeIn(num), run_time=0.65)
        bars.add(VGroup(bar, lab, num))
    return bars


def node_network(scene, layers, radius=0.13, buff_x=1.5, buff_y=0.55, color=None):
    """节点网络（AvgusTa/间宫 风格）：逐层点亮。layers: [3,4,4,1]"""
    color = color or scene.accent()
    cols = []
    for n in layers:
        col = VGroup(*[Circle(radius=radius, stroke_color=color, stroke_width=2,
                              fill_opacity=0.0) for _ in range(n)])
        col.arrange(DOWN, buff=buff_y)
        cols.append(col)
    group = VGroup(*cols).arrange(RIGHT, buff=buff_x)
    edges = VGroup()
    for a, b in zip(cols, cols[1:]):
        for na in a:
            for nb in b:
                edges.add(Line(na.get_center(), nb.get_center(), stroke_color=scene.dim(),
                               stroke_width=1, stroke_opacity=0.45))
    scene.play(LaggedStart(*[FadeIn(c) for c in cols], lag_ratio=0.3), run_time=1.4)
    scene.play(Create(edges), run_time=0.8)
    return VGroup(edges, group), cols


def numline(scene, x_range=(-3.5, 3.5), y=0.0, color=None, ticks=None):
    """F16 数轴 / 阈值线。

    坐标是 manim 单位（可见宽度约 ±7）。如果传入的是数据量级的坐标
    （比如 x_range=[0, 200]），自动等比缩到屏幕内，避免整根线跑出画外。
    """
    color = color or scene.dim()
    _xs = list(x_range) + [t[0] for t in (ticks or [])
                           if isinstance(t, (list, tuple)) and len(t) == 2]
    _max = max(abs(x) for x in _xs) if _xs else 0
    if _max > 7:
        _k = 5.0 / _max
        x_range = [x * _k for x in x_range]
        if ticks:
            ticks = [(t[0] * _k, t[1]) if isinstance(t, (list, tuple)) and len(t) == 2 else t
                     for t in ticks]
    line = Line([x_range[0], y, 0], [x_range[1], y, 0], color=color, stroke_width=3)
    scene.play(Create(line), run_time=0.6)
    marks = VGroup()
    if ticks:
        for x, lab in ticks:
            tick = Line([x, y - 0.08, 0], [x, y + 0.08, 0], color=color, stroke_width=2)
            t = text(str(lab), 0.3, scene.fg()).next_to(tick, DOWN, buff=0.12)
            marks.add(VGroup(tick, t))
        scene.play(LaggedStart(*[FadeIn(m) for m in marks], lag_ratio=0.08), run_time=0.7)
    return VGroup(line, marks)


def state_machine(scene, nodes, edges, r=0.55):
    """F4 状态机 + 概率弧。nodes: [(label,x,y)]，edges: [(i,j,label,curved)]"""
    circles = []
    for label, x, y in nodes:
        c = Circle(radius=r, stroke_color=scene.accent(), stroke_width=3,
                   fill_opacity=0.1, fill_color=scene.accent()).move_to([x, y, 0])
        t = text(label, 0.34, scene.fg()).move_to(c)
        scene.play(Create(c), FadeIn(t), run_time=0.6)
        circles.append(VGroup(c, t))
    for i, j, lab, curved in edges:
        a, b = circles[i][0].get_center(), circles[j][0].get_center()
        if curved:
            arrow = CurvedArrow(a, b, angle=-TAU / 4, color=scene.accent2(), stroke_width=3)
        else:
            arrow = Arrow(a, b, buff=r, color=scene.accent2(), stroke_width=3)
        mid = (a + b) / 2 + UP * 0.35
        t = text(lab, 0.3, scene.accent2()).move_to(mid)
        scene.play(Create(arrow), FadeIn(t), run_time=0.7)
    return VGroup(*circles)


def timeline(scene, items, y=-0.1, color=None):
    """P10 时间轴推进。items: [(label, width_ratio)]"""
    color = color or scene.accent()
    # 兼容两种写法：["步骤1","步骤2"] 或 [("步骤1", 2.0), ...]
    norm = []
    for it in items:
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            norm.append((str(it[0]), float(it[1])))
        else:
            norm.append((str(it), 1.0))
    items = norm
    total = sum(w for _, w in items) or 1
    x = -4.4
    blocks = VGroup()
    for label, w in items:
        width = 8.8 * w / total
        rect = Rectangle(width=width * 0.94, height=0.55, fill_color=color,
                         fill_opacity=0.7, stroke_width=0).move_to([x + width / 2, y, 0])
        lab = text(label, 0.28, "#FFFFFF").move_to(rect)
        scene.play(GrowFromEdge(rect, LEFT), FadeIn(lab), run_time=0.6)
        blocks.add(VGroup(rect, lab))
        x += width
    line = Line([-4.4, y - 0.45, 0], [4.4, y - 0.45, 0], color=scene.dim(), stroke_width=2)
    scene.play(Create(line), run_time=0.4)
    return blocks


def stack_layers(scene, names, x=0.0, repeat=None):
    """F7 分层堆叠 + ×N 大括号。names 自上而下。"""
    rows = VGroup()
    for nm in names:
        box = RoundedRectangle(corner_radius=0.08, width=4.2, height=0.55,
                               stroke_color=scene.dim(), stroke_width=1.5,
                               fill_opacity=0.08, fill_color=scene.accent())
        t = text(nm, 0.3, scene.fg()).move_to(box)
        rows.add(VGroup(box, t))
    rows.arrange(DOWN, buff=0.14).move_to([x, 0, 0])
    for r in rows:
        scene.play(FadeIn(r), run_time=0.5)
    if repeat:
        brace = Brace(rows, RIGHT, color=scene.accent2())
        lab = text(f"× {repeat}", 0.34, scene.accent2()).next_to(brace, RIGHT, buff=0.12)
        scene.play(GrowFromCenter(brace), FadeIn(lab), run_time=0.7)
    return rows


def weighted_sum(scene, items, result, y=0.0):
    """F8 加权求和：系数 × 色块 相加 = 结果。items: [(coef, color, label)]"""
    x = -4.2
    parts = VGroup()
    for i, (coef, col, label) in enumerate(items):
        c = text(f"{coef:g}", 0.36, col).move_to([x, y, 0])
        sq = Square(side_length=0.3, fill_color=col, fill_opacity=0.9, stroke_width=0)
        sq.next_to(c, RIGHT, buff=0.12)
        lab = text(label, 0.26, col).next_to(sq, DOWN, buff=0.1)
        parts.add(VGroup(c, sq, lab))
        scene.play(FadeIn(parts[-1]), run_time=0.5)
        x += 1.85
        if i < len(items) - 1:
            plus = text("+", 0.36, scene.fg()).move_to([x - 1.0, y, 0])
            scene.play(FadeIn(plus), run_time=0.3)
    eq = text("=", 0.4, scene.fg()).move_to([x - 1.1, y, 0])
    res = Square(side_length=0.34, fill_color=result, fill_opacity=0.9, stroke_width=0)
    res.next_to(eq, RIGHT, buff=0.15)
    scene.play(FadeIn(eq), GrowFromCenter(res), run_time=0.7)
    return VGroup(parts, eq, res)



def _latex_to_plain(t):
    """纯文本行里误写 LaTeX 时做降级替换，避免把 \\times 之类原样显示出来。"""
    rep = {"\\;": " ", "\\,": " ", "\\ ": " ", "\\times": "×", "\\div": "÷",
           "\\cdot": "·", "\\approx": "≈", "\\leq": "≤", "\\geq": "≥",
           "\\rightarrow": "→", "\\Rightarrow": "→", "\\pi": "π", "\\infty": "∞"}
    for a, b in rep.items():
        t = t.replace(a, b)
    return t.replace("{", "").replace("}", "").replace("$", "")


def formula_lines(scene, lines, highlight_last=True, box_color="#5FD08A"):
    """F2 公式逐行展开 + 结论高亮。lines: [(tex_or_text, is_formula)]"""
    group = Group()   # Group 而非 VGroup：formula() 可能返回 ImageMobject（LaTeX 渲染图）
    for item, is_math in lines:
        m = formula(item, scene.fg(), 0.8) if is_math else text(_latex_to_plain(item), 0.4, scene.fg())
        group.add(m)
    group.arrange(DOWN, buff=0.45).move_to([0, 0.15, 0])
    for m in group:
        scene.play(FadeIn(m), run_time=0.7)
    if highlight_last:
        box = highlight_box(group[-1], box_color)
        scene.play(Create(box), run_time=0.7)
    return group


def two_columns(scene, left_title, left_items, right_title, right_items,
                left_color=None, right_color=None):
    """P3 左右对照（两栏）。"""
    lc, rc = left_color or scene.accent(), right_color or scene.accent2()
    lv = VGroup(text(left_title, 0.42, lc, weight=BOLD),
                *[text(i, 0.32, scene.fg()) for i in left_items])
    rv = VGroup(text(right_title, 0.42, rc, weight=BOLD),
                *[text(i, 0.32, scene.fg()) for i in right_items])
    for v in (lv, rv):
        v.arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    lv.move_to([-3.2, 0, 0]); rv.move_to([3.2, 0, 0])
    for i in range(max(len(lv), len(rv))):
        anims = []
        if i < len(lv):
            anims.append(FadeIn(lv[i]))
        if i < len(rv):
            anims.append(FadeIn(rv[i]))
        scene.play(*anims, run_time=0.55)
    return VGroup(lv, rv)


def utilization_grid(scene, rows, cols=8, color=None):
    """利用率格阵：rows: [(label, filled)]"""
    color = color or scene.accent()
    out = VGroup()
    for label, filled in rows:
        cells = VGroup(*[Square(side_length=0.3, stroke_width=1.2, stroke_color=scene.dim(),
                                fill_color=color, fill_opacity=1.0 if j < filled else 0.06)
                         for j in range(cols)])
        cells.arrange(RIGHT, buff=0.05)
        lab = text(label, 0.3, scene.accent2()).next_to(cells, LEFT, buff=0.3)
        out.add(VGroup(lab, cells))
    out.arrange(DOWN, buff=0.35, aligned_edge=LEFT).move_to([0, 0.1, 0])
    for r in out:
        scene.play(FadeIn(r), run_time=0.6)
    return out



def bg_grid(scene, x_range=(-7.0, 7.0), y_range=(-3.9, 3.9), spacing=1.1, opacity=0.05):
    """密度层：极淡的背景网格。参考片边缘密度是我们 4 倍，靠这层补上去且不抢内容。"""
    g = VGroup()
    x = x_range[0]
    while x <= x_range[1]:
        g.add(Line([x, y_range[0], 0], [x, y_range[1], 0],
                   stroke_color=scene.fg(), stroke_width=1, stroke_opacity=opacity))
        x += spacing
    y = y_range[0]
    while y <= y_range[1]:
        g.add(Line([x_range[0], y, 0], [x_range[1], y, 0],
                   stroke_color=scene.fg(), stroke_width=1, stroke_opacity=opacity))
        y += spacing
    scene.add(g)
    return g


def corner_tag(scene, text_s, color=None, pos=UR):
    """角标：右上角一行小字（来源/编号），补密度也补信息。"""
    t = Text(text_s, font=CJK_FONT, color=color or scene.dim()).scale(0.26)
    t.to_corner(pos, buff=0.32)
    scene.add(t)
    return t


def legend(scene, items, pos=DR):
    """图例：一组色块 + 名字，放右下角。items: [(label, color)]"""
    rows = VGroup()
    for label, col in items:
        sq = Square(side_length=0.16, fill_color=col, fill_opacity=0.9, stroke_width=0)
        t = Text(label, font=CJK_FONT, color=scene.dim()).scale(0.24)
        rows.add(VGroup(sq, t).arrange(RIGHT, buff=0.12))
    rows.arrange(DOWN, buff=0.1, aligned_edge=LEFT)
    rows.to_corner(pos, buff=0.6)
    scene.add(rows)
    return rows


def gradient_sequence(scene, labels, colors=None, y=0.2, size=0.62):
    """F19 五连图渐变（同源逐级变化）：一排小方块 + 箭头 + 阶段标签。
    适用：加噪/去噪、压缩、精度下降等「同一对象逐级变化」。"""
    n = len(labels)
    step = min(2.0, 9.0 / max(1, n))
    x0 = -step * (n - 1) / 2
    group = VGroup()
    for i, lab in enumerate(labels):
        col = (colors or [scene.accent()] * n)[i] if colors else scene.accent()
        op = 0.15 + 0.8 * (i / max(1, n - 1))
        sq = Square(side_length=size, stroke_color=col, stroke_width=2,
                    fill_color=col, fill_opacity=op)
        sq.move_to([x0 + i * step, y, 0])
        t = text(lab, 0.26, scene.dim()).next_to(sq, DOWN, buff=0.14)
        scene.play(FadeIn(sq), FadeIn(t), run_time=0.5)
        group.add(VGroup(sq, t))
        if i < n - 1:
            a = Arrow(sq.get_right(), sq.get_right() + RIGHT * (step - size - 0.1),
                      buff=0.02, color=scene.dim(), stroke_width=2)
            scene.play(Create(a), run_time=0.25)
            group.add(a)
    return group


def stacked_bar(scene, parts, y=0.2, width=6.0, height=0.7):
    """F21 堆叠条 + 百分比：parts=[(标签, 数值, 色)]，按比例拼成一条。"""
    total = sum(v for _, v, _ in parts) or 1
    x = -width / 2
    group = VGroup()
    for label, v, col in parts:
        wpx = width * v / total
        rect = Rectangle(width=wpx, height=height, fill_color=col, fill_opacity=0.85,
                         stroke_width=0)
        rect.move_to([x + wpx / 2, y, 0])
        pct = v / total * 100
        t = text(f"{label}\n{pct:.0f}%", 0.24, "#FFFFFF").move_to(rect)
        scene.play(GrowFromEdge(rect, LEFT), FadeIn(t), run_time=0.55)
        group.add(VGroup(rect, t))
        x += wpx
    return group


def dual_axis_chart(scene, xs, series_up, series_down, up_label="资源", down_label="性能"):
    """F23 双曲线共用 x 轴：上=资源占用，下=性能。
    series_up / series_down = [(标签, [y值...], 色)]"""
    from manim import Axes, VMobject
    ax1 = Axes(x_range=[0, len(xs), 1], y_range=[0, max(max(s[1]) for s in series_up) * 1.2 or 1, 1],
               x_length=6.4, y_length=1.7, tips=False,
               axis_config={"color": scene.dim(), "stroke_width": 1.5}).move_to([0, 1.35, 0])
    ax2 = Axes(x_range=[0, len(xs), 1], y_range=[0, max(max(s[1]) for s in series_down) * 1.2 or 1, 1],
               x_length=6.4, y_length=1.7, tips=False,
               axis_config={"color": scene.dim(), "stroke_width": 1.5}).move_to([0, -1.15, 0])
    scene.play(Create(ax1), Create(ax2), run_time=0.8)
    scene.add(text(up_label, 0.26, scene.dim()).next_to(ax1, LEFT, buff=0.1))
    scene.add(text(down_label, 0.26, scene.dim()).next_to(ax2, LEFT, buff=0.1))
    for ax, series in ((ax1, series_up), (ax2, series_down)):
        for label, ys, col in series:
            pts = [ax.c2p(i, v) for i, v in enumerate(ys)]
            line = VMobject().set_points_as_corners(pts).set_stroke(col, 3)
            dot = Dot(pts[-1], color=col, radius=0.05)
            scene.play(Create(line), FadeIn(dot), run_time=0.7)
            scene.add(text(label, 0.24, col).next_to(dot, RIGHT, buff=0.1))
    return VGroup(ax1, ax2)


def zoom_sequence(scene, levels, x=0.0, y=0.1):
    """F13 无限放大：整体 → 局部 → 更局部。
    levels = [(标签, 宽, 高, 填充色)]，从大到小；每层套在上一层中央。"""
    prev = None
    group = VGroup()
    for i, (label, w, h, col) in enumerate(levels):
        rect = Rectangle(width=w, height=h, stroke_color=col, stroke_width=2.5,
                         fill_color=col, fill_opacity=0.06 + 0.05 * i)
        rect.move_to([x, y, 0])
        if prev is not None:
            rect.move_to(prev.get_center())
        # 标签贴各自矩形的左上角内部，避免多层标签叠在一起
        tag = text(label, 0.24, col).move_to(rect.get_corner(UL) + RIGHT * (0.9 + 0.5 * i) + UP * 0.2)
        scene.play(Create(rect), FadeIn(tag), run_time=0.7)
        group.add(VGroup(rect, tag))
        prev = rect
    return group


def isomorphic_pair(scene, left_title, right_title, rows,
                    left_color=None, right_color=None, y=0.1):
    """F22 同构并排（逻辑 vs 物理视图）：左右两组同结构，行间画映射箭头。
    rows = ["Block1", "Block2", ...]"""
    lc = left_color or scene.accent()
    rc = right_color or scene.accent2()
    def column(title, col, dx):
        head = text(title, 0.34, col, weight=BOLD).move_to([dx, y + 1.75, 0])
        boxes = VGroup()
        for nm in rows:
            b = RoundedRectangle(corner_radius=0.08, width=2.6, height=0.42,
                                stroke_color=col, stroke_width=1.5,
                                fill_color=col, fill_opacity=0.08)
            t = text(nm, 0.26, scene.fg()).move_to(b)
            boxes.add(VGroup(b, t))
        boxes.arrange(DOWN, buff=0.12).move_to([dx, y - 0.1, 0])
        return head, boxes
    lh, lb = column(left_title, lc, -3.2)
    rh, rb = column(right_title, rc, 3.2)
    scene.play(FadeIn(lh), FadeIn(rh), run_time=0.6)
    for i in range(len(rows)):
        scene.play(FadeIn(lb[i]), FadeIn(rb[i]), run_time=0.45)
        arrow = Arrow(lb[i][0].get_right(), rb[i][0].get_left(), buff=0.12,
                      color=scene.dim(), stroke_width=2)
        scene.play(Create(arrow), run_time=0.25)
    return VGroup(lh, lb, rh, rb)


def cache_blocks(scene, tokens, y=0.6, color=None):
    """F11 缓存块：每个 token 下面挂存储块，表示「算过就存起来」。
    tokens = ["猫", "坐", "在", "沙发"]"""
    color = color or scene.accent()
    n = len(tokens)
    step = min(1.9, 8.0 / max(1, n))
    x0 = -step * (n - 1) / 2
    group = VGroup()
    for i, tok in enumerate(tokens):
        chip = RoundedRectangle(corner_radius=0.1, width=0.9, height=0.5,
                                stroke_color=scene.dim(), stroke_width=1.5,
                                fill_color=scene.fg(), fill_opacity=0.05)
        chip.move_to([x0 + i * step, y, 0])
        t = text(tok, 0.3, scene.fg()).move_to(chip)
        blocks = VGroup(*[Square(side_length=0.22, stroke_width=1,
                                 stroke_color=color, fill_color=color,
                                 fill_opacity=0.85).move_to([x0 + i * step, y - 0.75 - j * 0.28, 0])
                          for j in range(2)])
        scene.play(FadeIn(chip), FadeIn(t), run_time=0.4)
        scene.play(LaggedStart(*[FadeIn(b) for b in blocks], lag_ratio=0.2), run_time=0.4)
        group.add(VGroup(chip, t, blocks))
    return group


def two_ends(scene, left_label, left_items, right_label, right_items,
             mid_label=None, y=0.1, sub_label=None):
    """F12 两端对齐：左边输入/预测，右边目标，中间网络或算子，底部差异。
    适合：监督学习、对比学习、蒸馏、loss 讲解。"""
    lv = VGroup(text(left_label, 0.3, scene.dim()),
                *[text(i, 0.3, scene.fg()) for i in left_items])
    rv = VGroup(text(right_label, 0.3, scene.dim()),
                *[text(i, 0.3, scene.fg()) for i in right_items])
    for v in (lv, rv):
        v.arrange(DOWN, buff=0.16, aligned_edge=LEFT)
    lv.move_to([-3.4, y, 0]); rv.move_to([3.4, y, 0])
    scene.play(FadeIn(lv), run_time=0.7)
    scene.play(FadeIn(rv), run_time=0.7)
    box = RoundedRectangle(corner_radius=0.1, width=2.4, height=1.1,
                           stroke_color=scene.accent(), stroke_width=2,
                           fill_opacity=0.08, fill_color=scene.accent()).move_to([0, y, 0])
    ml = text(mid_label or "模型", 0.3, scene.accent()).move_to(box)
    scene.play(Create(box), FadeIn(ml), run_time=0.7)
    a1 = Arrow(lv.get_right(), box.get_left(), buff=0.15, color=scene.dim(), stroke_width=2)
    a2 = Arrow(box.get_right(), rv.get_left(), buff=0.15, color=scene.dim(), stroke_width=2)
    scene.play(Create(a1), Create(a2), run_time=0.5)
    sub = sub_label or "两边差异 = 损失"
    diff = text(sub, 0.28, scene.accent2()).next_to(box, DOWN, buff=0.25)
    scene.play(FadeIn(diff), run_time=0.5)
    return VGroup(lv, rv, box, a1, a2)


def pipeline3(scene, steps, y=0.0, colors=None, size=0.3):
    """F20 三框 pipeline：输入 → 处理 → 输出，箭头上标步骤名。
    steps = [("标签1", 说明1), ("标签2", 说明2), ...] 支持 2–4 步。"""
    n = len(steps)
    step_x = min(3.2, 8.6 / max(1, n))
    x0 = -step_x * (n - 1) / 2
    boxes = VGroup()
    for i, (label, note) in enumerate(steps):
        col = (colors[i] if colors and i < len(colors) else scene.accent())
        box = RoundedRectangle(corner_radius=0.1, width=step_x * 0.72, height=0.85,
                               stroke_color=col, stroke_width=2,
                               fill_color=col, fill_opacity=0.10).move_to([x0 + i * step_x, y, 0])
        t = text(label, size, scene.fg()).move_to(box)
        sub = text(note, size * 0.78, scene.dim()).next_to(box, DOWN, buff=0.14)
        scene.play(Create(box), FadeIn(t), FadeIn(sub), run_time=0.55)
        boxes.add(VGroup(box, t, sub))
        if i < n - 1:
            a = Arrow(box.get_right(), box.get_right() + RIGHT * (step_x - box.width - 0.12),
                      buff=0.02, color=scene.dim(), stroke_width=2.5)
            scene.play(Create(a), run_time=0.3)
    return boxes


def qkv_colors(scene, tokens, q_color="#58C4DD", k_color="#F08A24", v_color="#8FE388", y=0.3):
    """F9 QKV 三色编码：每个 token 下挂 Q/K/V 三色方块，再用斜箭头求加权和。"""
    n = len(tokens)
    step = min(1.8, 7.6 / max(1, n))
    x0 = -step * (n - 1) / 2
    cols = []
    for i, tok in enumerate(tokens):
        chip = RoundedRectangle(corner_radius=0.08, width=0.85, height=0.42,
                                stroke_color=scene.fg(), stroke_width=1.2,
                                fill_color=scene.fg(), fill_opacity=0.06)
        chip.move_to([x0 + i * step, y, 0])
        t = text(tok, 0.28, scene.fg()).move_to(chip)
        blocks = VGroup(*[Square(side_length=0.2, stroke_width=0,
                                 fill_color=c, fill_opacity=0.9).move_to(
                                   [x0 + i * step, y - 0.5 - j * 0.26, 0])
                          for j, c in enumerate((q_color, k_color, v_color))])
        scene.play(FadeIn(chip), FadeIn(t), run_time=0.35)
        scene.play(LaggedStart(*[FadeIn(b) for b in blocks], lag_ratio=0.15), run_time=0.35)
        cols.append(VGroup(chip, t, blocks))
    labels = VGroup(*[text(s, 0.22, c).next_to(cols[0][2][j], LEFT, buff=1.2 + 0.0)
                      for j, (s, c) in enumerate((("Q", q_color), ("K", k_color), ("V", v_color)))])
    scene.play(FadeIn(labels), run_time=0.4)
    return VGroup(*cols)


def annotation_board(scene, title, lines, color_points=None):
    """F26 印刷题面 + 红笔批注：白色面板 + 黑字题面 + 红笔圈注。"""
    board = RoundedRectangle(corner_radius=0.12, width=10.0, height=3.6,
                             stroke_color=scene.dim(), stroke_width=1.5,
                             fill_color="#FFFFFF", fill_opacity=0.94).move_to([0, -0.15, 0])
    scene.play(Create(board), run_time=0.7)
    head = text(title, 0.34, "#1F2328", weight=BOLD).move_to(board.get_top() + DOWN * 0.35)
    scene.play(FadeIn(head), run_time=0.4)
    rows = VGroup()
    for ln in lines:
        rows.add(text(ln, 0.26, "#333333"))
    rows.arrange(DOWN, buff=0.18, aligned_edge=LEFT).next_to(head, DOWN, buff=0.3).align_to(board, LEFT).shift(RIGHT * 0.5)
    for r in rows:
        scene.play(FadeIn(r), run_time=0.3)
    marks = VGroup()
    if color_points:
        for idx, label in color_points:
            if idx < len(rows):
                box = SurroundingRectangle(rows[idx], color="#D93A2B", buff=0.06, stroke_width=2)
                note = text(label, 0.24, "#D93A2B").next_to(box, RIGHT, buff=0.15)
                scene.play(Create(box), FadeIn(note), run_time=0.4)
                marks.add(VGroup(box, note))
    return VGroup(board, head, rows, marks)


def recurrence_to_matrix(scene, rec_lines, matrix_tex, y=0.2):
    """F5 递推式 → 矩阵形变：先列递推，再把同样内容改写成矩阵乘向量。"""
    rec = Group(*[formula(t, scene.fg(), 0.62) for t in rec_lines])   # 可能含 ImageMobject
    rec.arrange(DOWN, buff=0.3).move_to([0, y + 1.3, 0])
    for r in rec:
        scene.play(FadeIn(r), run_time=0.6)
    arrow = Arrow([0, y + 0.2, 0], [0, y - 0.5, 0], buff=0, color=scene.accent(), stroke_width=3)
    lab = text("改写成矩阵形式", 0.26, scene.accent()).next_to(arrow, RIGHT, buff=0.15)
    scene.play(GrowArrow(arrow), FadeIn(lab), run_time=0.6)
    mat = formula(matrix_tex, scene.accent(), 0.95).move_to([0, y - 1.3, 0])
    scene.play(FadeIn(mat), run_time=0.9)
    box = highlight_box(mat, scene.accent2())
    scene.play(Create(box), run_time=0.5)
    return VGroup(rec, arrow, mat)


def token_strip(scene, tokens, values=None, y=0.7, color=None):
    """横排 token 条 + 每词下方数值块（注意力权重 / 相似度）。"""
    color = color or scene.accent()
    n = len(tokens)
    step = min(1.75, 8.0 / max(1, n))
    x0 = -step * (n - 1) / 2
    group = VGroup()
    for i, tok in enumerate(tokens):
        t = text(tok, 0.34, scene.fg()).move_to([x0 + i * step, y, 0])
        scene.play(FadeIn(t), run_time=0.3)
        parts = [t]
        if values:
            v = values[i]
            blk = Square(side_length=0.26, stroke_width=0, fill_color=color,
                         fill_opacity=min(1.0, 0.2 + v)).move_to([x0 + i * step, y - 0.55, 0])
            num = text(f"{v:.2f}", 0.22, scene.dim()).next_to(blk, DOWN, buff=0.08)
            scene.play(FadeIn(blk), FadeIn(num), run_time=0.25)
            parts += [blk, num]
        group.add(VGroup(*parts))
    return group


# ─────────────────────────── 3D 基类（P4） ───────────────────────────
class Base3D(ThreeDScene):
    """三维页基类：相机、背景、预算、标题全部复用 Base 的约定。"""

    def setup(self):
        _bg = self.tok("bg", "#0D1117")
        config.background_color = _bg
        self.camera.background_color = _bg
        try:
            self.camera.set_background(color=_bg)
        except Exception:
            pass
        self.t0 = time.time()
        self.budget = max(4.0, self.dur * 0.85)
        self.used = 0.0
        self._step = float(self.tok("step", 1.5))
        self.set_camera_orientation(phi=70 * DEGREES, theta=-50 * DEGREES, zoom=0.9)

    # 与 Base 同名接口，逻辑一致
    @property
    def spec(self):
        mod = sys.modules.get(self.__class__.__module__)
        if mod is not None:
            spec = getattr(mod, "SPEC", None)
            if spec:
                return spec
        return globals().get("SPEC", {})

    @property
    def dur(self):
        return float(self.spec.get("duration", 20.0))

    def tok(self, key, default=None):
        t = self.spec.get("style_tokens") or {}
        return t.get(key, default)

    def fg(self):
        return self.tok("fg", "#eaf2f8")

    def accent(self):
        return self.tok("accent", "#58C4DD")

    def accent2(self):
        return self.tok("accent2", "#F08A24")

    def dim(self):
        return self.tok("dim", "#4E6B7A")

    def play(self, *args, **kwargs):
        rt = float(kwargs.get("run_time", 1.0))
        left = max(0.12, self.budget - self.used)
        rt = min(rt, self._step, left)
        self.used += rt
        kwargs["run_time"] = rt
        return super().play(*args, **kwargs)

    def head(self, text=None):
        t = self.spec.get("title", "") if text is None else text
        if not t:
            return
        m = Text(t, font=CJK_FONT, color=self.fg(), weight=BOLD).scale(0.44)
        m.to_corner(UL, buff=0.45)
        self.add_fixed_in_frame_mobjects(m)
        self.play(Write(m), run_time=0.7)

    def tail(self):
        rest = self.dur - (time.time() - self.t0) - 0.4
        if rest > 0.2:
            self.wait(rest)


# ─────────────────── P4：三维空间（坐标轴 / 向量 / 旋转） ───────────────────
def space_3d(scene, vectors=None, labels=None, rotate=True, scale=1.0):
    """三维坐标系 + 向量束 + 相机缓慢旋转。
    vectors = [[x,y,z], ...]；labels = ["v1", ...]（可省）。
    这是 P4「降维投影」的核心：先把高维对象立起来，再让相机转。"""
    axes = ThreeDAxes(x_range=[-3, 3, 1], y_range=[-3, 3, 1], z_range=[-2, 2, 1],
                      x_length=5.4 * scale, y_length=5.4 * scale, z_length=3.6 * scale,
                      axis_config={"color": scene.dim(), "stroke_width": 2})
    scene.play(Create(axes), run_time=1.0)
    group = VGroup(axes)
    colors = [scene.accent(), scene.accent2(), "#8FE388", "#F49BC8"]
    for i, v in enumerate(vectors or []):
        col = colors[i % len(colors)]
        vec = Arrow3D(ORIGIN, np.array(v, dtype=float), color=col, thickness=0.03)
        lab = text(labels[i], 0.32, col) if labels and i < len(labels) else None
        scene.play(Create(vec), run_time=0.5)   # Arrow3D 不支持 GrowArrow
        if lab is not None:
            lab.move_to(np.array(v, dtype=float) * 1.12)
            scene.add_fixed_orientation_mobjects(lab)
            scene.play(FadeIn(lab), run_time=0.3)
        group.add(vec)
    if rotate:
        scene.begin_ambient_camera_rotation(rate=0.18)
    return group


# ─────────────────── P5：真形变（morph，中间态插值） ───────────────────
def morph_pair(scene, before_tex, after_tex, caption=None, y=0.2):
    """同一个对象从 A 连续变形成 B（不是切页、不是并列）。
    before/after 为 Mathtext 字符串；用 Transform 保留中间态，观众看到的是「过程」。"""
    a = formula(before_tex, scene.fg(), 1.0).move_to([0, y + 0.9, 0])
    b = formula(after_tex, scene.accent(), 1.0).move_to([0, y - 0.9, 0])
    scene.play(FadeIn(a), run_time=0.6)
    scene.play(Transform(a, b), run_time=1.4)      # 关键：同一个 mobject 变形
    box = highlight_box(a, scene.accent())
    scene.play(Create(box), run_time=0.5)
    if caption:
        scene.play(FadeIn(text(caption, 0.3, scene.dim()).next_to([0, y - 1.8, 0], DOWN, buff=0.1)),
                   run_time=0.4)
    return VGroup(a, box)


# ─────────────────── P8：数形双栏（左公式 / 右图，同帧推进） ───────────────────
def split_formula_figure(scene, tex_lines, plot_points, y=0.1,
                         left_head="公式", right_head="图形"):
    """左栏公式逐行出、右栏曲线同步生长——同一进度推动两边。

    版式：左栏占 x∈[-6.2,-2.0]，右栏坐标轴占 x∈[0.6,4.4]，中间留空避免打架。
    """
    axes = Axes(x_range=[0, 10, 5], y_range=[0, 5, 1], x_length=3.2, y_length=2.4,
                tips=False, axis_config={"color": scene.dim(), "stroke_width": 1.6})
    axes.move_to([2.6, y - 0.35, 0])
    rh = text(right_head, 0.3, scene.dim()).next_to(axes, UP, buff=0.2)
    lh = text(left_head, 0.3, scene.dim()).move_to([-4.3, y + 1.55, 0])
    scene.play(FadeIn(lh), FadeIn(rh), Create(axes), run_time=0.7)

    lines = Group(*[formula(t, scene.fg(), 0.5) for t in tex_lines])   # 可能含 ImageMobject
    lines.arrange(DOWN, buff=0.26, aligned_edge=LEFT).move_to([-4.3, y + 0.55, 0])
    n = max(1, len(lines))
    curve = None
    for i, ln in enumerate(lines):
        scene.play(FadeIn(ln), run_time=0.5)
        k = max(2, int(len(plot_points) * (i + 1) / n))
        seg = plot_points[:k]
        if len(seg) >= 2:
            new_curve = axes.plot_line_graph([p[0] for p in seg], [p[1] for p in seg],
                                             add_vertex_dots=False, line_color=scene.accent())
            if curve is None:
                scene.play(Create(new_curve), run_time=0.4)
            else:
                scene.play(Transform(curve, new_curve), run_time=0.35)
            curve = new_curve
    return VGroup(lines, axes)


# ─────────────────── 像素网格 + 卷积核滑动（图像题材） ───────────────────
def pixel_grid(scene, rows=6, cols=6, color=None, cell=0.42, values=None, x=-3.4, y=0.3):
    """一张像素图：格子矩阵 + 可选灰度值（0–1）。图像类知识点的底座。"""
    color = color or scene.accent()
    g = VGroup()
    for r in range(rows):
        row = VGroup()
        for c in range(cols):
            v = 0.0
            if values and r < len(values) and c < len(values[r]):
                v = float(values[r][c])
            sq = Square(side_length=cell, stroke_width=1, stroke_color=scene.dim(),
                        fill_color=color, fill_opacity=0.08 + 0.85 * v)
            row.add(sq)
        row.arrange(RIGHT, buff=0.03)
        g.add(row)
    g.arrange(DOWN, buff=0.03).move_to([x, y, 0])
    scene.play(LaggedStart(*[FadeIn(m) for m in g], lag_ratio=0.02), run_time=0.9)
    return g


def conv_slide(scene, grid=None, k=3, rows=6, cols=6, values=None,
               cell=0.42, color=None, x=-3.4, y=0.3):
    """卷积核在像素网格上逐格滑动，每到一格框出覆盖区。

    grid 省略时**自动先画一张像素网格**（JSON spec 无法传对象，必须自给自足）。
    """
    color = color or scene.accent2()
    if grid is None:
        grid = pixel_grid(scene, rows=rows, cols=cols, values=values,
                          cell=cell, color=scene.accent(), x=x, y=y)
    span = cell + 0.03
    n_rows, n_cols = len(grid), len(grid[0])
    frame = Square(side_length=span * k, stroke_color=color, stroke_width=3,
                   fill_opacity=0).move_to(grid[0][0].get_center())
    scene.play(Create(frame), run_time=0.4)
    targets = []
    for r in range(max(1, n_rows - k + 1)):
        for c in range(max(1, n_cols - k + 1)):
            base = grid[r][c].get_center()
            targets.append(base + RIGHT * (span * (k - 1) / 2) + DOWN * (span * (k - 1) / 2))
    for t in targets:
        scene.play(frame.animate.move_to(t), run_time=0.16)
    return VGroup(grid, frame)


# ─────────────────── 曲线生长（优化/概率题材） ───────────────────
def curve_grow(scene, fn=None, xs=None, color=None, axis_labels=("x", "y"), note=None):
    """坐标轴 + 曲线从 0 长到满（可配合「越来越平」讲收敛/饱和）。"""
    color = color or scene.accent()
    axes = Axes(x_range=[0, 10, 2], y_range=[0, 5, 1], x_length=7.2, y_length=3.4,
                tips=True, axis_config={"color": scene.dim(), "stroke_width": 2})
    axes.move_to([0, -0.1, 0])
    scene.play(Create(axes), run_time=0.8)
    lab_x = text(axis_labels[0], 0.28, scene.dim()).next_to(axes.x_axis.get_end(), RIGHT, buff=0.12)
    lab_y = text(axis_labels[1], 0.28, scene.dim()).next_to(axes.y_axis.get_end(), UP, buff=0.12)
    scene.play(FadeIn(lab_x), FadeIn(lab_y), run_time=0.3)
    xs = xs or [i * 0.1 for i in range(101)]
    if fn is None:
        fn = lambda x: 4.6 * (1 - np.exp(-x / 3.0))
    graph = axes.plot(fn, x_range=[0, 10], color=color, stroke_width=4)
    scene.play(Create(graph), run_time=1.8)
    if note:
        scene.play(FadeIn(text(note, 0.3, scene.dim()).next_to([0, -2.6, 0], DOWN, buff=0.05)),
                   run_time=0.4)
    return graph


# ─────────────────── 二维矢量场（场/梯度题材） ───────────────────
def vector_field_2d(scene, fn=None, color=None, nx=7, ny=5, width=8.0, height=4.4):
    """按网格铺一排箭头，长度/方向由 fn(x,y) 决定——讲梯度场、流向、电磁。"""
    color = color or scene.accent()
    if fn is None:
        def fn(x, y):
            return (-y, x)
    arrows = VGroup()
    for i in range(nx):
        for j in range(ny):
            x = -width / 2 + width * i / (nx - 1)
            y = -height / 2 + height * j / (ny - 1)
            dx, dy = fn(x, y)
            norm = (dx * dx + dy * dy) ** 0.5 or 1
            dx, dy = dx / norm * 0.38, dy / norm * 0.38
            a = Arrow([x, y, 0], [x + dx, y + dy, 0], buff=0, color=color,
                      stroke_width=3, max_tip_length_to_length_ratio=0.35)
            arrows.add(a)
    scene.play(LaggedStart(*[GrowArrow(a) for a in arrows], lag_ratio=0.02), run_time=1.6)
    return arrows


def ray_split(scene, scatter_color=None, straight_color=None,
              scatter_count=14, density=1.0, trail_color=None):
    """F41 多路光线分流：一束光进入介质，短波长被散射到各个方向，长波长直行。

    这是「为什么天是蓝的 / 为什么远处信号弱 / 为什么短波被吸收」这类
    「同一输入的不同成分响应不同」问题的最小可视化。
    """
    scatter_color = scatter_color or "#58C4DD"
    straight_color = straight_color or "#E0574A"
    trail_color = trail_color or scene.dim()

    src = Dot([-5.6, 1.5, 0], radius=0.09, color="#FFFFFF")
    label = text("白光", 0.3, scene.fg()).next_to(src, LEFT, buff=0.18)
    scene.play(FadeIn(src), FadeIn(label), run_time=0.5)

    # 主干：从光源斜向下进入介质
    body = Line([-5.4, 1.45, 0], [4.6, -1.6, 0], color=trail_color, stroke_width=2)
    scene.play(Create(body), run_time=0.9)

    # 长波长成分：继续直行
    straight = Arrow([-4.4, 1.2, 0], [4.4, -1.55, 0], buff=0,
                     color=straight_color, stroke_width=4)
    s_lab = text("长波：直行", 0.28, straight_color).next_to(straight.get_end(), UP, buff=0.12)
    scene.play(Create(straight), FadeIn(s_lab), run_time=0.8)

    # 短波长成分：沿主干若干点向四周散开
    import random as _rnd
    _rnd.seed(7)
    rays = VGroup()
    for i in range(scatter_count):
        t = 0.12 + 0.82 * i / max(1, scatter_count - 1)
        px = -4.4 + (4.4 - (-4.4)) * t
        py = 1.2 + (-1.55 - 1.2) * t
        ang = _rnd.uniform(-2.4, 2.4)
        ln = _rnd.uniform(0.75, 1.45) * density
        ex, ey = px + ln * (0.5 + 0.7 * abs(ang)), py + ln * (0.9 * ang / 2.4)
        ray = Line([px, py, 0], [ex, ey, 0], color=scatter_color,
                   stroke_width=2.2, stroke_opacity=0.85)
        rays.add(ray)
    scene.play(LaggedStart(*[Create(r) for r in rays], lag_ratio=0.06), run_time=1.6)
    s2 = text("短波：四散", 0.3, scatter_color).move_to([1.2, -1.0, 0])
    scene.play(FadeIn(s2), run_time=0.4)
    return VGroup(src, body, straight, rays)


def spectrum_strip(scene, labels=None, colors=None, y=0.4, size=0.62):
    """白光分解成色带（F42）：一排彩色方块，说明「白光是混合」。"""
    labels = labels or ["红", "橙", "黄", "绿", "蓝", "紫"]
    colors = colors or ["#E0574A", "#F08A24", "#E8C547", "#7FBF6A", "#58C4DD", "#B388E8"]
    n = len(labels)
    step = min(1.5, 8.6 / n)
    x0 = -step * (n - 1) / 2
    g = VGroup()
    for i, (lab, col) in enumerate(zip(labels, colors)):
        sq = Square(side_length=size, stroke_width=0, fill_color=col,
                    fill_opacity=0.95).move_to([x0 + i * step, y, 0])
        t = text(lab, 0.26, scene.dim()).next_to(sq, DOWN, buff=0.12)
        scene.play(FadeIn(sq), FadeIn(t), run_time=0.28)
        g.add(VGroup(sq, t))
    return g

# 让 `from anim_kit import kit` 可用（kit.xxx 即本模块的手法函数）
import sys as _sys
kit = _sys.modules[__name__]
