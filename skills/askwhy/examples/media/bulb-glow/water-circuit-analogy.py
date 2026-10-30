from manim import (
    Arrow,
    Circle,
    DOWN,
    FadeIn,
    GrowArrow,
    LaggedStart,
    LEFT,
    Line,
    ManimColor,
    RIGHT,
    RoundedRectangle,
    Scene,
    Text,
    Triangle,
    UP,
    VGroup,
    Write,
)


class WaterCircuitAnalogy(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#F4FBF7")
        ink = ManimColor("#285D4B")
        water = ManimColor("#4E9DDA")
        pump = ManimColor("#7055D9")
        heat = ManimColor("#E98545")

        title = Text(
            "熟悉的水路：泵维持压差，水沿管循环",
            font="PingFang SC",
            font_size=32,
            color=ink,
        )
        title.to_edge(UP, buff=0.5)
        self.play(Write(title), run_time=1.0)

        pipe = RoundedRectangle(
            width=9.2,
            height=4.0,
            corner_radius=0.55,
            stroke_color=ManimColor("#B7D8E8"),
            stroke_width=26,
        ).shift(DOWN * 0.35)
        self.play(FadeIn(pipe), run_time=0.8)

        pump_ring = Circle(
            radius=0.68,
            color=pump,
            stroke_width=6,
            fill_color=ManimColor("#EEE9FF"),
            fill_opacity=1,
        ).move_to(LEFT * 4.6 + DOWN * 0.35)
        pump_arrow = Triangle(color=pump, fill_opacity=1).scale(0.28).rotate(-90 * 3.14159265 / 180)
        pump_arrow.move_to(pump_ring.get_center() + UP * 0.05)
        pump_label = Text("水泵", font="PingFang SC", font_size=22, color=pump)
        pump_label.next_to(pump_ring, LEFT, buff=0.35)
        self.play(FadeIn(pump_ring, pump_arrow), Write(pump_label), run_time=0.9)

        drops = VGroup(
            *[
                Circle(radius=0.10, fill_color=water, fill_opacity=1, stroke_width=0)
                .move_to(LEFT * (3.6 - index * 1.15) + UP * 1.65)
                for index in range(6)
            ]
        )
        flow = Arrow(
            LEFT * 3.6 + UP * 2.25,
            RIGHT * 2.6 + UP * 2.25,
            color=water,
            buff=0,
        )
        flow_label = Text("水流绕闭合管路前进", font="PingFang SC", font_size=21, color=water)
        flow_label.next_to(flow, UP, buff=0.16)
        self.play(FadeIn(drops), GrowArrow(flow), FadeIn(flow_label), run_time=0.8)

        narrow = Line(
            RIGHT * 1.6 + UP * 1.65,
            RIGHT * 3.4 + UP * 1.65,
            color=heat,
            stroke_width=34,
        )
        narrow_label = Text("窄而粗糙的管段", font="PingFang SC", font_size=21, color=heat)
        narrow_label.next_to(narrow, DOWN, buff=0.28)
        self.play(FadeIn(narrow, narrow_label), run_time=0.7)

        pressure = VGroup(
            Text("压力高", font="PingFang SC", font_size=19, color=pump),
            Text("压力低", font="PingFang SC", font_size=19, color=water),
        )
        pressure[0].move_to(LEFT * 3.7 + DOWN * 2.1)
        pressure[1].move_to(RIGHT * 3.7 + DOWN * 2.1)
        self.play(FadeIn(pressure), run_time=0.5)

        self.play(
            LaggedStart(
                *[
                    drop.animate.shift(RIGHT * 3.8)
                    for drop in drops
                ],
                lag_ratio=0.18,
            ),
            run_time=2.2,
        )
        self.play(narrow.animate.set_stroke(width=42), run_time=0.6)
        self.play(narrow.animate.set_stroke(width=34), run_time=0.6)

        result = Text(
            "泵推动水流  →  窄管阻力让管壁升温",
            font="PingFang SC",
            font_size=25,
            color=heat,
        )
        result.to_edge(DOWN, buff=0.35)
        self.play(FadeIn(result), run_time=0.8)
        self.wait(1.2)
