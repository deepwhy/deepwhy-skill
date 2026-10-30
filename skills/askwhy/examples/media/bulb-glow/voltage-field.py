from manim import (
    Arrow,
    Circle,
    DOWN,
    FadeIn,
    FadeOut,
    GrowArrow,
    LaggedStart,
    LEFT,
    Line,
    ManimColor,
    RIGHT,
    Scene,
    Text,
    UP,
    VGroup,
    Write,
)


class VoltageField(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#F8F6FF")
        ink = ManimColor("#28233D")
        violet = ManimColor("#7055D9")
        orange = ManimColor("#F0A24B")
        blue = ManimColor("#3E8EF7")

        title = Text("电压建立电场，电场对电荷做功", font="PingFang SC", font_size=34, color=ink)
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.0)

        positive = Line(LEFT * 4.2 + UP * 2.0, LEFT * 4.2 + DOWN * 2.0, color=orange, stroke_width=16)
        negative = Line(RIGHT * 4.2 + UP * 2.0, RIGHT * 4.2 + DOWN * 2.0, color=blue, stroke_width=16)
        plus = Text("+", font="PingFang SC", font_size=30, color=orange).next_to(positive, UP)
        minus = Text("−", font="PingFang SC", font_size=34, color=blue).next_to(negative, UP)
        self.play(FadeIn(positive, negative, plus, minus), run_time=0.8)

        fields = VGroup(
            *[
                Arrow(LEFT * 3.5 + UP * y, RIGHT * 3.5 + UP * y, color=violet, buff=0)
                for y in (-1.3, 0.0, 1.3)
            ]
        )
        field_label = Text("电势差 → 电场 E", font="PingFang SC", font_size=25, color=violet)
        field_label.move_to(DOWN * 2.45)
        self.play(LaggedStart(*[GrowArrow(item) for item in fields]), FadeIn(field_label), run_time=1.1)

        charge = Circle(radius=0.23, fill_color=blue, fill_opacity=1, stroke_width=0).move_to(LEFT * 3.4 + UP * 0.15)
        charge_label = Text("q", font="PingFang SC", font_size=24, color=blue).next_to(charge, DOWN, buff=0.18)
        work = Text("电场做功 qΔV", font="PingFang SC", font_size=28, color=orange)
        work.move_to(DOWN * 2.45)
        self.play(FadeIn(charge, charge_label), FadeOut(field_label), FadeIn(work), run_time=0.8)
        self.play(charge.animate.move_to(RIGHT * 3.4 + DOWN * 0.15), run_time=2.6)
        self.wait(1.1)
