"""Motion graphics for the English product demo; render with Manim at 1080p30."""
from manim import *

config.background_color = "#071017"
WHITE = "#F4FAFC"
MUTED = "#9BB3C2"
CYAN = "#60E8F2"
VIOLET = "#AD9AFF"
MINT = "#69E4B0"
GOLD = "#FFD479"
PANEL = "#102630"
FONT = "Segoe UI"


def txt(s, size=30, color=WHITE, weight=NORMAL):
    return Text(s, font=FONT, font_size=size, color=color, weight=weight)


def small(s, color=CYAN):
    return txt(s, 17, color, BOLD)


def bg():
    lines = VGroup()
    for i in range(-8, 9):
        lines.add(Line([i, -4, 0], [i, 4, 0], stroke_color="#122832", stroke_width=0.5))
    for i in range(-4, 5):
        lines.add(Line([-8, i, 0], [8, i, 0], stroke_color="#122832", stroke_width=0.5))
    return lines


def card(title, sub, color=CYAN, width=3.3, height=1.25):
    box = RoundedRectangle(corner_radius=.16, width=width, height=height,
        stroke_color=color, stroke_width=2, fill_color=PANEL, fill_opacity=0.97)
    a = txt(title, 24, WHITE, BOLD)
    b = txt(sub, 16, MUTED)
    content = VGroup(a, b).arrange(DOWN, buff=.12)
    if content.width > width-.4: content.scale_to_fit_width(width-.4)
    content.move_to(box)
    return VGroup(box, content)


def header(tag, title, subtitle=None):
    k = small(tag).to_edge(UP, buff=.28).to_edge(LEFT, buff=.65)
    t = txt(title, 42, WHITE, BOLD).next_to(k, DOWN, aligned_edge=LEFT, buff=.25)
    group = VGroup(k, t)
    if subtitle:
        group.add(txt(subtitle, 21, MUTED).next_to(t, DOWN, aligned_edge=LEFT, buff=.18))
    return group


def connect(a, b, color=CYAN):
    return Arrow(a, b, buff=.12, stroke_width=2.5, color=color, max_tip_length_to_length_ratio=.13)


class MotionOpening(Scene):
    def construct(self):
        self.add(bg())
        brand = small("VIDEO KNOWLEDGE STUDIO").to_corner(UL, buff=.5)
        self.play(FadeIn(brand), run_time=.3)
        time = txt("4 HOURS", 86, CYAN, BOLD).move_to(LEFT*3.7+UP*1.5)
        line = txt("to understand unfamiliar code", 32, WHITE).next_to(time, DOWN, aligned_edge=LEFT)
        self.play(Write(time), FadeIn(line, shift=UP*.2), run_time=1.1)
        sources = VGroup(card("VIDEOS", "multiple explanations", VIOLET, 2.5, 1),
                         card("PAPERS", "details and context", GOLD, 2.5, 1),
                         card("NOTES", "scattered ideas", MINT, 2.5, 1)).arrange(DOWN, buff=.18).move_to(RIGHT*4.6+UP*.2)
        self.play(LaggedStart(*[FadeIn(c, shift=LEFT*.6) for c in sources], lag_ratio=.18), run_time=1)
        goal = txt("Turn sources into understanding you can use.", 32, WHITE, BOLD).to_edge(DOWN, buff=.9)
        self.play(FadeIn(goal, shift=UP*.2), run_time=.6)
        self.wait(1.5)


class MotionPlan(Scene):
    def construct(self):
        self.add(bg())
        h = header("01  /  PLAN", "Start with a real goal", "An Agent is an assistant that uses tools to help find and compare sources.")
        self.play(FadeIn(h, shift=UP*.15), run_time=.55)
        nodes = VGroup(card("GOAL", "What must I do?", CYAN, 2.8),
                       card("SOURCES", "Choose useful material", VIOLET, 2.8),
                       card("LEARNING PATH", "Order the ideas", MINT, 2.8),
                       card("APPLY", "Return to the task", GOLD, 2.8)).arrange(RIGHT, buff=.55).move_to(DOWN*.35)
        arrows = VGroup(*[connect(nodes[i].get_right(), nodes[i+1].get_left(), MUTED) for i in range(3)])
        for i, node in enumerate(nodes):
            self.play(FadeIn(node, shift=RIGHT*.3), run_time=.35)
            if i < 3: self.play(GrowArrow(arrows[i]), run_time=.2)
        dot = Dot(color=CYAN, radius=.09).move_to(nodes[0].get_center())
        self.add(dot)
        self.play(dot.animate.move_to(nodes[-1].get_center()), run_time=1.4, rate_func=linear)
        disclaimer = txt("Agent-assisted search requires tools and accessible sources.", 20, MUTED).to_edge(DOWN, buff=.62)
        self.play(FadeIn(disclaimer), run_time=.4)
        self.wait(.8)


class MotionSync(Scene):
    def construct(self):
        self.add(bg())
        h = header("02  /  LEARN", "One moment, two views", "A timestamp is a time marker that returns you to the matching video moment.")
        self.play(FadeIn(h), run_time=.5)
        video = RoundedRectangle(corner_radius=.16, width=6, height=3.3, stroke_color=CYAN, fill_color="#0A151D", fill_opacity=1).move_to(LEFT*3.2+DOWN*.3)
        play = Triangle(color=CYAN, fill_color=CYAN, fill_opacity=1).scale(.26).rotate(-PI/2).move_to(video.get_center()+UP*.25)
        rail = Line(video.get_left()+RIGHT*.35+DOWN*1.25, video.get_right()+LEFT*.35+DOWN*1.25, color=MUTED, stroke_width=3)
        marker = Dot(rail.get_start(), radius=.09, color=CYAN)
        note = VGroup(*[card(f"{i:02d}:{i*5:02d}", desc, col, 4.3, .7) for i,desc,col in [(0,"Start with the question",CYAN),(1,"See the mechanism",VIOLET),(2,"Check the result",MINT)]]).arrange(DOWN,buff=.17).move_to(RIGHT*3.5+DOWN*.3)
        self.play(Create(video), GrowFromCenter(play), Create(rail), FadeIn(marker), LaggedStart(*[FadeIn(n, shift=LEFT*.2) for n in note],lag_ratio=.15),run_time=1.1)
        link=DashedLine(marker.get_center(),note[1].get_left(),color=CYAN,stroke_width=2)
        self.play(marker.animate.move_to(rail.point_from_proportion(.55)), note[1][0].animate.set_stroke(CYAN,4), Create(link),run_time=.8)
        self.play(link.animate.put_start_and_end_on(marker.get_center(),note[1].get_left()),run_time=.3)
        self.wait(1)


class MotionContext(Scene):
    def construct(self):
        self.add(bg())
        h = header("03  /  ASK", "Ask with context", "The AI tutor is an assistant that answers using information from the lesson.")
        self.play(FadeIn(h, shift=UP*.15),run_time=.6)
        inputs = VGroup(card("SELECTED NOTE", "the passage in question", CYAN, 3.3, .95),
                        card("TIMESTAMP", "the current video moment", VIOLET, 3.3, .95),
                        card("TRANSCRIPT + FRAME", "available words and image", MINT, 3.3, .95)).arrange(DOWN,buff=.2).move_to(LEFT*4+DOWN*.35)
        tutor = card("AI TUTOR", "explanation + evidence", CYAN, 3.4, 1.6).move_to(RIGHT*2.0+DOWN*.35)
        self.play(LaggedStart(*[FadeIn(i, shift=RIGHT*.25) for i in inputs],lag_ratio=.18),FadeIn(tutor,scale=.9),run_time=1)
        arrows=VGroup(*[connect(i.get_right(),tutor.get_left(),col) for i,col in zip(inputs,[CYAN,VIOLET,MINT])])
        self.play(LaggedStart(*[GrowArrow(a) for a in arrows],lag_ratio=.18),run_time=.9)
        pulses=VGroup(*[Dot(a.get_start(),radius=.08,color=col) for a,col in zip(arrows,[CYAN,VIOLET,MINT])])
        self.add(pulses)
        self.play(*[p.animate.move_to(tutor.get_left()) for p in pulses],run_time=1,rate_func=linear)
        self.play(tutor[0].animate.set_stroke(MINT,4),run_time=.3)
        self.wait(.8)


class MotionGraph(Scene):
    def construct(self):
        self.add(bg())
        h=header("04  /  CONNECT", "Turn notes into a knowledge map", "A map links ideas so you can revisit how they relate.")
        self.play(FadeIn(h),run_time=.5)
        nodes=VGroup(card("QUESTION", "What must I understand?", CYAN, 2.9,1),
                     card("MECHANISM", "How does it work?", VIOLET,2.9,1),
                     card("EVIDENCE", "Where is it explained?", MINT,2.9,1),
                     card("PRACTICE", "Can I use it?", GOLD,2.9,1))
        for n,pos in zip(nodes,[LEFT*4.4+UP*.1,LEFT*.9+UP*.85,LEFT*.9+DOWN*1.3,RIGHT*3.1+DOWN*.2]): n.move_to(pos)
        lines=VGroup(connect(nodes[0].get_right(),nodes[1].get_left(),CYAN),connect(nodes[0].get_right(),nodes[2].get_left(),MINT),connect(nodes[1].get_right(),nodes[3].get_left(),VIOLET),connect(nodes[2].get_right(),nodes[3].get_left(),GOLD))
        self.play(LaggedStart(*[FadeIn(n,scale=.85) for n in nodes],lag_ratio=.15),run_time=1)
        self.play(LaggedStart(*[GrowArrow(l) for l in lines],lag_ratio=.15),run_time=1.1)
        for node in nodes:
            self.play(node[0].animate.set_stroke(WHITE,4),run_time=.12)
            self.play(node[0].animate.set_stroke(width=2),run_time=.12)
        self.wait(.8)


class MotionCreate(Scene):
    def construct(self):
        self.add(bg())
        h=header("05  /  CREATE", "From a plan to a lesson", "Production modes are different sets of rules for making a video.")
        self.play(FadeIn(h),run_time=.5)
        modes=VGroup(card("REMIX","Rework one source",CYAN,3.1,1),card("COURSE","Combine sources",VIOLET,3.1,1),card("SCI-POP","Explain one idea",GOLD,3.1,1)).arrange(RIGHT,buff=.4).move_to(UP*.45)
        self.play(LaggedStart(*[FadeIn(n,shift=UP*.3) for n in modes],lag_ratio=.2),run_time=.9)
        steps=VGroup(*[txt(s,25,WHITE,BOLD) for s in ["PLAN","→","BUILD","→","CHECK","→","PREVIEW"]]).arrange(RIGHT,buff=.34).move_to(DOWN*1.5)
        self.play(LaggedStart(*[FadeIn(s,shift=UP*.2) for s in steps],lag_ratio=.14),run_time=1.3)
        dot=Dot(steps[0].get_bottom()+DOWN*.23,color=CYAN,radius=.08)
        self.add(dot)
        self.play(dot.animate.move_to(steps[-1].get_bottom()+DOWN*.23),run_time=1.2,rate_func=linear)
        self.wait(.8)


class MotionClose(Scene):
    def construct(self):
        self.add(bg())
        title=txt("Make learning usable.",55,WHITE,BOLD).to_edge(UP,buff=.7)
        self.play(Write(title),run_time=.9)
        rows=VGroup(card("PROJECT", "Trace the mechanism back to code", CYAN, 10.8,1),
                    card("RESEARCH", "Connect sources to a reproducible explanation", VIOLET,10.8,1),
                    card("CAREER", "Build a knowledge map you can revisit", GOLD,10.8,1)).arrange(DOWN,buff=.2).move_to(DOWN*.25)
        self.play(LaggedStart(*[FadeIn(r,shift=LEFT*.5) for r in rows],lag_ratio=.25),run_time=1.3)
        end=small("VIDEO KNOWLEDGE STUDIO   /   LOCAL WORKSPACE",MINT).to_edge(DOWN,buff=.55)
        self.play(FadeIn(end),run_time=.5)
        self.wait(1.4)
