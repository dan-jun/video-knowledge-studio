from __future__ import annotations

from manim import *


FONT = "Noto Sans SC"
MONO = "Cascadia Mono"
INK = "#05070A"
PAPER = "#F5F7F9"
WHITE = "#F8FAFC"
MUTED = "#8092A2"
CYAN = "#64EEFF"
MINT = "#6BE4AC"
AMBER = "#FFD166"
VIOLET = "#A78BFA"
RED = "#FF8C7D"


def label(text: str, size=36, color=WHITE, weight=BOLD, font=FONT):
    return Text(text, font=font, font_size=size, color=color, weight=weight)


def mono(text: str, size=24, color=MUTED):
    return Text(text, font=MONO, font_size=size, color=color)


def grid(opacity=0.08, color="#7FA4B8"):
    lines = VGroup()
    for x in np.arange(-9, 9.1, 1):
        lines.add(Line([x, -5.2, 0], [x, 5.2, 0], color=color, stroke_width=1, stroke_opacity=opacity))
    for y in np.arange(-5, 5.1, 1):
        lines.add(Line([-9, y, 0], [9, y, 0], color=color, stroke_width=1, stroke_opacity=opacity))
    return lines


def brand_mark(scale=1.0):
    ring = Circle(radius=0.58, color=CYAN, stroke_width=4)
    inner = Circle(radius=0.22, color=WHITE, stroke_width=0)
    inner.set_fill(WHITE, opacity=1)
    slash1 = Line([-0.39, 0.32, 0], [0.04, -0.34, 0], color=WHITE, stroke_width=6)
    slash2 = Line([0.04, -0.34, 0], [0.42, 0.31, 0], color=WHITE, stroke_width=6)
    return VGroup(ring, inner, slash1, slash2).scale(scale)


class Opening(Scene):
    def construct(self):
        config.background_color = INK
        g = grid(opacity=0.055)
        g.set_opacity(0)
        self.add(g)
        self.play(g.animate.set_opacity(1), run_time=1.2)

        mark = brand_mark(0.9)
        mark.move_to(UP * 0.95)
        self.play(Create(mark[0]), FadeIn(mark[1]), Create(mark[2]), Create(mark[3]), run_time=1.3)

        kicker = label("认识一下", 58, WHITE, weight=BOLD).move_to(DOWN * 0.25)
        self.play(FadeIn(kicker, shift=UP * 0.2), run_time=0.65)

        name = label("VIDEO KNOWLEDGE STUDIO", 34, WHITE, weight=BOLD).move_to(DOWN * 1.25)
        sub = mono("LOCAL-FIRST  /  EVIDENCE-LINKED  /  LEARNING SYSTEM", 20).next_to(name, DOWN, buff=0.28)
        self.play(FadeIn(name), FadeIn(sub), run_time=0.8)
        self.wait(0.8)


class UseCaseIntro(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.065))

        mark = brand_mark(0.32).move_to([-6.55, 3.62, 0])
        brand = mono("VIDEO KNOWLEDGE STUDIO", 18, WHITE).next_to(mark, RIGHT, buff=0.18)
        time_badge = label("23:47", 25, CYAN, weight=BOLD).move_to([6.0, 3.62, 0])
        self.play(FadeIn(mark), FadeIn(brand), FadeIn(time_badge), run_time=0.45)

        title = label("明天要改 Raft 日志复制", 51, WHITE, weight=BOLD).move_to(UP * 2.65)
        subtitle = label("你只有 4 小时，却面对 9 个视频、3 篇文章和 2 份旧笔记", 26, MUTED, weight=MEDIUM)
        subtitle.next_to(title, DOWN, buff=0.25)
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(subtitle, shift=UP * 0.1), run_time=0.45)

        cases = [
            ("01  /  PROJECT", "接手陌生项目", "4 小时补齐关键机制", CYAN),
            ("02  /  RESEARCH", "论文复现卡住", "多份资料串成一条线", VIOLET),
            ("03  /  CAREER", "面试或转岗", "零散时间形成体系", AMBER),
        ]
        cards = VGroup()
        for code, head, desc, color in cases:
            box = RoundedRectangle(
                corner_radius=0.18,
                width=3.75,
                height=2.2,
                stroke_color=color,
                stroke_width=2,
                fill_color=color,
                fill_opacity=0.07,
            )
            c = mono(code, 17, color).move_to(box.get_corner(UL) + RIGHT * 0.68 + DOWN * 0.32)
            h = label(head, 28, WHITE, weight=BOLD).move_to(box.get_center() + UP * 0.34)
            d = label(desc, 20, MUTED, weight=MEDIUM).move_to(box.get_center() + DOWN * 0.42)
            cards.add(VGroup(box, c, h, d))
        cards.arrange(RIGHT, buff=0.43).move_to(DOWN * 0.55)
        self.play(LaggedStart(*[FadeIn(card, shift=UP * 0.18) for card in cards], lag_ratio=0.16), run_time=1.1)

        self.play(
            cards[1:].animate.set_opacity(0.35),
            cards[0][0].animate.set_stroke(width=4),
            run_time=0.55,
        )

        insight = label("你缺的不是更多视频，", 31, MUTED, weight=MEDIUM).move_to(DOWN * 3.0)
        punch = label("是一条能落到工作上的学习链。", 39, WHITE, weight=BOLD).move_to(DOWN * 3.75)
        self.play(FadeIn(insight), run_time=0.35)
        self.play(Write(punch), run_time=0.65)
        self.wait(0.9)


class Promise(Scene):
    def construct(self):
        config.background_color = INK
        black_bg = FullScreenRectangle(fill_color=INK, fill_opacity=1, stroke_width=0)
        paper_bg = FullScreenRectangle(fill_color=PAPER, fill_opacity=1, stroke_width=0)
        self.add(black_bg)

        t1 = label("不是又一个", 50, MUTED, weight=BOLD).move_to(UP * 1.2)
        t2 = label("视频总结器", 76, WHITE, weight=BOLD).move_to(DOWN * 0.05)
        self.play(FadeIn(t1, shift=RIGHT * 0.35), run_time=0.65)
        self.play(Write(t2), run_time=0.9)
        self.wait(1.0)

        self.add(paper_bg)
        t3 = label("而是", 38, "#36424D", weight=MEDIUM).move_to(UP * 1.35)
        t4 = label("一条完整学习链", 72, INK, weight=BOLD).move_to(UP * 0.3)
        line = Line(LEFT * 5.1, RIGHT * 5.1, color=INK, stroke_width=4).move_to(DOWN * 0.75)
        tags = label("规划  →  选源  →  制作  →  学习  →  追问  →  体系", 24, "#314252", weight=MEDIUM)
        tags.move_to(DOWN * 1.45)
        self.play(FadeIn(t3), run_time=0.4)
        self.play(Write(t4), run_time=0.85)
        self.play(Create(line), FadeIn(tags, shift=UP * 0.15), run_time=0.7)
        self.wait(1.2)


class LearningChain(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.07))
        title = label("同一份数据，贯穿每一步", 42, WHITE, weight=BOLD).to_edge(UP, buff=0.75)
        self.play(FadeIn(title, shift=DOWN * 0.15), run_time=0.6)

        entries = [
            ("01", "学习缺口", "工作 / 科研 / 项目", CYAN),
            ("02", "规划选源", "多个互补视频", VIOLET),
            ("03", "动画课程", "关键画面讲清机制", AMBER),
            ("04", "知识笔记", "术语 · 因果 · 易错点", MINT),
            ("05", "边看边问", "时间戳 + 转录 + 画面", RED),
            ("06", "知识体系", "节点连成一张网", CYAN),
        ]

        cards = VGroup()
        for idx, (num, head, sub, color) in enumerate(entries):
            card = RoundedRectangle(
                corner_radius=0.18,
                width=2.45,
                height=1.55,
                stroke_color=color,
                stroke_width=2,
                fill_color=color,
                fill_opacity=0.07,
            )
            n = mono(num, 18, color).move_to(card.get_corner(UL) + RIGHT * 0.42 + DOWN * 0.25)
            h = label(head, 30, WHITE, weight=BOLD)
            s = label(sub, 18, MUTED, weight=MEDIUM)
            text_group = VGroup(h, s).arrange(DOWN, buff=0.18, aligned_edge=LEFT)
            text_group.move_to(card.get_center() + DOWN * 0.04)
            cards.add(VGroup(card, n, text_group))

        cards.arrange(RIGHT, buff=0.36)
        cards.set_width(13.1)
        cards.move_to(UP * 0.35)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.25) for c in cards], lag_ratio=0.16), run_time=2.2)

        arrows = VGroup()
        for left, right in zip(cards[:-1], cards[1:]):
            arrows.add(Arrow(
                left.get_right() + RIGHT * 0.02,
                right.get_left() + LEFT * 0.02,
                buff=0,
                color="#5C7485",
                stroke_width=2,
                max_tip_length_to_length_ratio=0.18,
            ))
        self.play(LaggedStart(*[Create(a) for a in arrows], lag_ratio=0.1), run_time=1.2)

        shared = VGroup(
            label("视频", 23, CYAN, weight=BOLD),
            label("笔记", 23, MINT, weight=BOLD),
            label("证据", 23, AMBER, weight=BOLD),
            label("AI", 23, VIOLET, weight=BOLD),
        ).arrange(RIGHT, buff=1.1).move_to(DOWN * 2.05)
        shared_line = Line(LEFT * 5.4, RIGHT * 5.4, color="#385061", stroke_width=2).next_to(shared, UP, buff=0.3)
        caption = label("共用同一份时间戳与知识数据", 30, WHITE, weight=MEDIUM).next_to(shared, DOWN, buff=0.28)
        self.play(Create(shared_line), FadeIn(shared), run_time=0.8)
        self.play(FadeIn(caption, shift=UP * 0.12), run_time=0.55)
        self.wait(1.0)


class EvidenceLoop(Scene):
    def construct(self):
        config.background_color = "#071018"
        self.add(grid(opacity=0.06))
        difference = label("差异 01  /  问题不离开原片", 20, CYAN, weight=BOLD).to_edge(UP, buff=0.42)
        header = label("不懂，就停在那一秒问", 42, WHITE, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(difference), run_time=0.35)
        self.play(FadeIn(header), run_time=0.5)

        video = RoundedRectangle(corner_radius=0.18, width=7.8, height=4.35, stroke_width=2,
                                 stroke_color=CYAN, fill_color="#0D2533", fill_opacity=0.9)
        video.move_to(LEFT * 3.0 + DOWN * 0.15)
        frame_title = label("当前视频", 24, CYAN, weight=BOLD).move_to(video.get_corner(UL) + RIGHT * 0.75 + DOWN * 0.38)
        frame_body = label("原片画面 + 当前秒数 + 附近转录", 27, WHITE, weight=MEDIUM).move_to(video.get_center() + UP * 0.3)
        progress = Line(video.get_corner(DL) + RIGHT * 0.55 + UP * 0.5,
                        video.get_corner(DR) + LEFT * 0.55 + UP * 0.5,
                        color="#284858", stroke_width=5)
        played = Line(progress.get_left(), progress.point_from_proportion(0.58), color=CYAN, stroke_width=5)
        knob = Dot(played.get_end(), radius=0.09, color=CYAN)
        stamp = mono("00:29", 20, CYAN).next_to(knob, UP, buff=0.14)
        self.play(FadeIn(video), FadeIn(frame_title), FadeIn(frame_body), run_time=0.7)
        self.play(Create(progress), Create(played), FadeIn(knob), FadeIn(stamp), run_time=0.7)

        note = RoundedRectangle(corner_radius=0.18, width=5.0, height=4.35, stroke_width=2,
                                stroke_color=MINT, fill_color="#0A1D19", fill_opacity=0.92)
        note.move_to(RIGHT * 4.15 + DOWN * 0.15)
        note_title = label("知识笔记", 24, MINT, weight=BOLD).move_to(note.get_corner(UL) + RIGHT * 0.75 + DOWN * 0.38)
        node = label("节点：可独立回答问题的判断", 27, WHITE, weight=MEDIUM).move_to(note.get_center() + UP * 1.0)
        edge = label("边：说明前后依赖的因果句", 27, WHITE, weight=MEDIUM).move_to(note.get_center() + UP * 0.25)
        question = label("“这里的边界为什么成立？”", 25, AMBER, weight=MEDIUM).move_to(note.get_center() + DOWN * 0.75)
        note_ui = VGroup(note_title, node, edge, question)
        self.play(FadeIn(note), FadeIn(note_ui), run_time=0.8)

        connect = DashedLine(video.get_right() + RIGHT * 0.1, note.get_left() + LEFT * 0.1, color="#6A8798", dash_length=0.15)
        answer = label("解释 + 证据 + 修改建议", 24, CYAN, weight=BOLD).move_to(DOWN * 2.65)
        self.play(Create(connect), FadeIn(answer), run_time=0.7)
        self.wait(1.0)


class ContextStatement(Scene):
    def construct(self):
        config.background_color = PAPER
        paper_bg = FullScreenRectangle(fill_color=PAPER, fill_opacity=1, stroke_width=0)
        self.add(paper_bg)
        eyebrow = label("差异 02  /  AI 看到同一份证据", 23, "#586976", weight=MEDIUM).move_to(UP * 1.9)
        rows = VGroup(
            label("当前秒数", 33, INK, weight=BOLD),
            label("附近的转录", 33, INK, weight=BOLD),
            label("正在看的画面", 33, INK, weight=BOLD),
        ).arrange(RIGHT, buff=1.2)
        rows.move_to(UP * 0.25)
        rule = Line(LEFT * 5.2, RIGHT * 5.2, color=INK, stroke_width=3).move_to(DOWN * 0.55)
        note = label("不是脱离视频的泛泛而谈", 29, "#3D4B56", weight=MEDIUM).move_to(DOWN * 1.35)
        self.play(FadeIn(eyebrow), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(row, shift=UP * 0.18) for row in rows], lag_ratio=0.18), run_time=0.8)
        self.play(Create(rule), FadeIn(note), run_time=0.55)
        self.wait(1.6)


class KnowledgeNetwork(Scene):
    def construct(self):
        config.background_color = "#061018"
        self.add(grid(opacity=0.07))
        difference = label("差异 03  /  笔记不是清单", 20, CYAN, weight=BOLD).to_edge(UP, buff=0.42)
        title = label("知识不是清单，是一张网", 42, WHITE, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(difference), run_time=0.3)
        self.play(FadeIn(title), run_time=0.5)

        center = RoundedRectangle(corner_radius=0.18, width=2.0, height=0.9,
                                  stroke_color=CYAN, stroke_width=3,
                                  fill_color=CYAN, fill_opacity=0.14).move_to(ORIGIN)
        center_text = label("矩阵", 36, WHITE, weight=BOLD).move_to(center)
        center_node = VGroup(center, center_text)

        positions = {
            "基向量": [-5.0, 1.55, 0],
            "空间": [-2.8, -1.9, 0],
            "行列式": [0.0, 2.15, 0],
            "逆矩阵": [4.8, 1.6, 0],
            "复合": [2.8, -1.9, 0],
            "特征向量": [6.0, -0.55, 0],
        }
        colors = {
            "基向量": VIOLET,
            "空间": MINT,
            "行列式": AMBER,
            "逆矩阵": RED,
            "复合": CYAN,
            "特征向量": AMBER,
        }
        nodes = {}
        for name, pos in positions.items():
            color = colors[name]
            box = RoundedRectangle(corner_radius=0.16, width=2.1, height=0.78,
                                   stroke_color=color, stroke_width=2,
                                   fill_color=color, fill_opacity=0.09).move_to(pos)
            txt = label(name, 27, WHITE, weight=BOLD).move_to(box)
            nodes[name] = VGroup(box, txt)

        edges = VGroup()
        links = [
            ("基向量", "矩阵"),
            ("矩阵", "空间"),
            ("空间", "行列式"),
            ("矩阵", "逆矩阵"),
            ("矩阵", "复合"),
            ("复合", "特征向量"),
            ("行列式", "逆矩阵"),
        ]
        all_nodes = {"矩阵": center_node, **nodes}
        for left, right in links:
            edges.add(Arrow(
                all_nodes[left].get_right() if left == "矩阵" else all_nodes[left].get_center(),
                all_nodes[right].get_left() if right == "矩阵" else all_nodes[right].get_center(),
                buff=0.35,
                color="#436276",
                stroke_width=2,
                max_tip_length_to_length_ratio=0.12,
            ))

        self.play(FadeIn(center_node, scale=0.88), run_time=0.55)
        self.play(LaggedStart(*[FadeIn(node, shift=UP * 0.18) for node in nodes.values()], lag_ratio=0.12), run_time=1.2)
        self.play(LaggedStart(*[Create(edge) for edge in edges], lag_ratio=0.08), run_time=1.2)

        highlight = VGroup(center_node, nodes["基向量"], nodes["空间"], nodes["行列式"])
        self.play(
            *[node[0].animate.set_stroke(width=5, color=WHITE) for node in highlight],
            run_time=0.65,
        )

        note = label("节点要可回答，边要说明依赖", 31, WHITE, weight=MEDIUM).move_to(DOWN * 3.45)
        self.play(FadeIn(note, shift=UP * 0.16), run_time=0.5)
        self.wait(1.2)


class ThreeModes(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.055))
        difference = label("差异 04  /  生产与学习不换上下文", 20, CYAN, weight=BOLD).to_edge(UP, buff=0.42)
        title = label("三种产线，不是三个孤立按钮", 40, WHITE, weight=BOLD).to_edge(UP, buff=0.85)
        self.play(FadeIn(difference), run_time=0.3)
        self.play(FadeIn(title), run_time=0.55)

        specs = [
            ("remix", "视频涅槃", "单源重制", "信息守恒 · 严格出处 · 练习复盘", CYAN),
            ("course", "长教学", "多源整合", "15–60 分钟 · 分章 · 多来源", VIOLET),
            ("scipop", "科普短片", "单点讲透", "2–6 分钟 · 高动画密度", AMBER),
        ]
        cards = VGroup()
        for code, name, tag, desc, color in specs:
            card = RoundedRectangle(corner_radius=0.24, width=4.5, height=4.6,
                                    stroke_color=color, stroke_width=2,
                                    fill_color=color, fill_opacity=0.075)
            code_line = mono(code, 27, color).move_to(card.get_corner(UL) + RIGHT * 0.75 + DOWN * 0.42)
            title_line = label(name, 38, WHITE, weight=BOLD).move_to(card.get_center() + UP * 0.95)
            chip_box = RoundedRectangle(corner_radius=0.15, width=2.2, height=0.55,
                                        stroke_width=0, fill_color=color, fill_opacity=0.16)
            chip_text = label(tag, 22, color, weight=BOLD).move_to(chip_box)
            tag_group = VGroup(chip_box, chip_text).move_to(card.get_center() + UP * 0.25)
            rule = label(desc, 21, MUTED, weight=MEDIUM)
            rule.set_width(3.55)
            rule.move_to(card.get_center() + DOWN * 1.02)
            cards.add(VGroup(card, code_line, title_line, tag_group, rule))
        cards.arrange(RIGHT, buff=0.55).set_width(12.9).move_to(UP * 0.1)
        self.play(LaggedStart(*[FadeIn(c, shift=UP * 0.3) for c in cards], lag_ratio=0.18), run_time=1.5)

        pipeline = VGroup(
            label("规格", 24, WHITE, weight=BOLD),
            mono("→", 27, "#6A8190"),
            label("分镜", 24, WHITE, weight=BOLD),
            mono("→", 27, "#6A8190"),
            label("门禁", 24, WHITE, weight=BOLD),
            mono("→", 27, "#6A8190"),
            label("渲染", 24, WHITE, weight=BOLD),
            mono("→", 27, "#6A8190"),
            label("成片", 24, CYAN, weight=BOLD),
        ).arrange(RIGHT, buff=0.45).move_to(DOWN * 2.9)
        self.play(FadeIn(pipeline, shift=UP * 0.2), run_time=0.7)
        self.wait(0.8)


class ProductionStatement(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.05))
        title = label("从一句需求", 44, MUTED, weight=BOLD).move_to(UP * 1.15)
        line2 = label("到一部可验证的成片", 66, WHITE, weight=BOLD).move_to(DOWN * 0.0)
        rule = Line(LEFT * 5.25, RIGHT * 5.25, color=CYAN, stroke_width=3).move_to(DOWN * 0.9)
        pipeline = VGroup(
            label("规格", 26, WHITE, weight=BOLD),
            mono("→", 25, CYAN),
            label("分镜", 26, WHITE, weight=BOLD),
            mono("→", 25, CYAN),
            label("门禁", 26, WHITE, weight=BOLD),
            mono("→", 25, CYAN),
            label("渲染", 26, WHITE, weight=BOLD),
        ).arrange(RIGHT, buff=0.42).move_to(DOWN * 1.55)
        self.play(FadeIn(title), run_time=0.4)
        self.play(Write(line2), run_time=0.75)
        self.play(Create(rule), FadeIn(pipeline), run_time=0.6)
        self.wait(1.4)


class DifferenceBridge(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.05))
        eyebrow = label("WHY THIS IS DIFFERENT", 20, CYAN, weight=BOLD).to_edge(UP, buff=0.55)
        self.play(FadeIn(eyebrow), run_time=0.35)

        old_box = RoundedRectangle(
            corner_radius=0.2, width=4.8, height=3.2,
            stroke_color="#53616B", stroke_width=2,
            fill_color="#53616B", fill_opacity=0.07,
        ).move_to(LEFT * 3.8)
        old_title = label("普通生成器", 30, MUTED, weight=BOLD).move_to(old_box.get_center() + UP * 0.82)
        old_body = label("视频做完\n学习就结束", 42, "#91A0AA", weight=BOLD, font=FONT)
        old_body.set_line_spacing(0.75).move_to(old_box.get_center() + DOWN * 0.18)

        new_box = RoundedRectangle(
            corner_radius=0.2, width=5.2, height=3.2,
            stroke_color=CYAN, stroke_width=3,
            fill_color=CYAN, fill_opacity=0.08,
        ).move_to(RIGHT * 3.7)
        new_title = label("Video Knowledge Studio", 27, WHITE, weight=BOLD).move_to(new_box.get_center() + UP * 0.82)
        new_body = label("视频 + 笔记 + 证据 + AI\n继续进入同一个工作台", 30, CYAN, weight=BOLD)
        new_body.set_line_spacing(0.8).move_to(new_box.get_center() + DOWN * 0.18)

        arrow = Arrow(old_box.get_right(), new_box.get_left(), buff=0.24, color=CYAN,
                      stroke_width=3, max_tip_length_to_length_ratio=0.18)
        self.play(FadeIn(old_box), FadeIn(old_title), FadeIn(old_body), run_time=0.55)
        self.play(Create(arrow), run_time=0.3)
        self.play(FadeIn(new_box), FadeIn(new_title), FadeIn(new_body), run_time=0.55)

        statement = label("成片不是终点，是下一次学习的起点。", 35, WHITE, weight=BOLD).move_to(DOWN * 3.0)
        self.play(FadeIn(statement, shift=UP * 0.12), run_time=0.5)
        self.wait(1.1)


class RaftLesson(Scene):
    def construct(self):
        config.background_color = "#071018"
        self.add(grid(opacity=0.055))

        badge = label("SCIPOP  /  生成课程", 20, CYAN, weight=BOLD).move_to([-6.2, 4.45, 0])
        title = label("只给 4 小时，怎么读懂 Raft 日志复制？", 38, WHITE, weight=BOLD)
        title.move_to(UP * 3.45)
        focus = VGroup(
            label("目标拆解", 18, CYAN, weight=BOLD),
            label("多源对照", 18, VIOLET, weight=BOLD),
            label("关键动画", 18, AMBER, weight=BOLD),
        ).arrange(RIGHT, buff=0.45).next_to(title, DOWN, buff=0.25)
        self.play(FadeIn(badge), run_time=0.35)
        self.play(Write(title), run_time=0.75)
        self.play(FadeIn(focus, shift=UP * 0.12), run_time=0.45)

        def server(name, pos, color):
            box = RoundedRectangle(
                corner_radius=0.16,
                width=2.2,
                height=0.95,
                stroke_color=color,
                stroke_width=2,
                fill_color=color,
                fill_opacity=0.09,
            ).move_to(pos)
            text = label(name, 24, WHITE, weight=BOLD).move_to(box)
            return VGroup(box, text)

        client = server("客户端", [-5.9, 0.4, 0], MUTED)
        leader = server("Leader", [-2.7, 0.4, 0], CYAN)
        follower_a = server("Follower A", [2.0, 1.8, 0], MINT)
        follower_b = server("Follower B", [2.0, -1.2, 0], AMBER)
        committed = server("已提交", [5.6, 0.35, 0], VIOLET)

        self.play(
            FadeIn(client), FadeIn(leader), FadeIn(follower_a),
            FadeIn(follower_b), FadeIn(committed),
            run_time=0.7,
        )

        route_in = Arrow(client.get_right(), leader.get_left(), buff=0.08, color="#6E8390",
                         stroke_width=2, max_tip_length_to_length_ratio=0.16)
        route_a = Arrow(leader.get_right() + UP * 0.12, follower_a.get_left(), buff=0.1,
                        color="#5D7786", stroke_width=2, max_tip_length_to_length_ratio=0.15)
        route_b = Arrow(leader.get_right() + DOWN * 0.12, follower_b.get_left(), buff=0.1,
                        color="#5D7786", stroke_width=2, max_tip_length_to_length_ratio=0.15)
        route_commit = Arrow(follower_a.get_right(), committed.get_top() + UP * 0.65,
                             buff=0.08, color="#5D7786", stroke_width=2,
                             max_tip_length_to_length_ratio=0.15)
        self.play(Create(route_in), Create(route_a), Create(route_b), run_time=0.6)

        packet = Dot(radius=0.10, color=AMBER).move_to(client.get_right())
        self.play(packet.animate.move_to(leader.get_left()), run_time=0.55)
        packet_a = Dot(radius=0.09, color=MINT).move_to(leader.get_right())
        packet_b = Dot(radius=0.09, color=AMBER).move_to(leader.get_right())
        self.play(
            packet_a.animate.move_to(follower_a.get_left()),
            packet_b.animate.move_to(follower_b.get_left()),
            run_time=0.8,
        )

        log_a = VGroup(*[
            Rectangle(width=0.24, height=0.12, stroke_width=0, fill_color=MINT, fill_opacity=0.9)
            for _ in range(4)
        ]).arrange(RIGHT, buff=0.05).move_to(follower_a.get_center() + DOWN * 0.48)
        log_b = VGroup(*[
            Rectangle(width=0.24, height=0.12, stroke_width=0, fill_color=AMBER, fill_opacity=0.9)
            for _ in range(3)
        ]).arrange(RIGHT, buff=0.05).move_to(follower_b.get_center() + DOWN * 0.48)
        self.play(LaggedStart(*[GrowFromCenter(x) for x in log_a], lag_ratio=0.12),
                  LaggedStart(*[GrowFromCenter(x) for x in log_b], lag_ratio=0.12),
                  run_time=0.75)

        majority = label("多数副本", 25, MINT, weight=BOLD).move_to([-0.55, -2.45, 0])
        check = Circle(radius=0.24, color=MINT, stroke_width=3).move_to([-2.65, -2.45, 0])
        check_mark = VGroup(
            Line([-0.10, 0.02, 0], [-0.01, -0.10, 0], color=MINT, stroke_width=4),
            Line([-0.01, -0.10, 0], [0.15, 0.12, 0], color=MINT, stroke_width=4),
        ).move_to(check)
        self.play(Create(check), Create(check_mark), FadeIn(majority), run_time=0.55)

        note = RoundedRectangle(
            corner_radius=0.16,
            width=4.2,
            height=0.82,
            stroke_color=VIOLET,
            stroke_width=2,
            fill_color=VIOLET,
            fill_opacity=0.09,
        ).move_to([4.25, -2.45, 0])
        note_text = label("确认后才允许提交", 24, WHITE, weight=BOLD).move_to(note)
        self.play(FadeIn(note), FadeIn(note_text), run_time=0.45)
        self.play(packet_a.animate.move_to(follower_a.get_left() + UP * 0.1), run_time=0.25)

        slogan = label("先看见机制，再回到代码。", 34, WHITE, weight=BOLD).move_to(DOWN * 3.65)
        self.play(FadeIn(slogan, shift=UP * 0.12), run_time=0.45)
        self.wait(0.8)


class Finale(Scene):
    def construct(self):
        config.background_color = INK
        self.add(grid(opacity=0.05))
        a = label("不是功能更多", 34, MUTED, weight=BOLD).move_to(UP * 2.25)
        b = label("而是每一步都能回到同一份证据", 50, WHITE, weight=BOLD).move_to(UP * 1.1)
        line = Line(LEFT * 5.4, RIGHT * 5.4, color="#3D5362", stroke_width=3).move_to(UP * 0.2)
        c = label("知识不用收藏", 48, WHITE, weight=BOLD).move_to(DOWN * 0.75)
        d = label("做成自己的体系", 58, CYAN, weight=BOLD).move_to(DOWN * 1.75)
        self.play(FadeIn(a), run_time=0.35)
        self.play(Write(b), run_time=0.7)
        self.play(Create(line), run_time=0.35)
        self.play(FadeIn(c, shift=UP * 0.12), run_time=0.35)
        self.play(Write(d), run_time=0.65)

        mark = brand_mark(0.55).move_to(DOWN * 1.85)
        mark.move_to(DOWN * 3.05)
        name = label("VIDEO KNOWLEDGE STUDIO", 27, WHITE, weight=BOLD).next_to(mark, RIGHT, buff=0.35)
        local = mono("LOCAL-FIRST · TEACHABLE · TRACEABLE", 17).next_to(name, DOWN, buff=0.13)
        self.play(FadeIn(mark), FadeIn(name), FadeIn(local), run_time=0.8)
        self.wait(1.2)
