from manim import (
    Arrow,
    Circle,
    DOWN,
    FadeIn,
    GrowArrow,
    LEFT,
    Line,
    ManimColor,
    RIGHT,
    RoundedRectangle,
    Scene,
    Text,
    UP,
    VGroup,
    Write,
)


class BatteryVoltage(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#F8F6FF")
        ink = ManimColor("#28233D")
        orange = ManimColor("#F0A24B")
        blue = ManimColor("#3E8EF7")
        green = ManimColor("#2F8B6D")

        title = Text("电池靠化学反应维持电势差", font="PingFang SC", font_size=34, color=ink)
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.0)

        body = RoundedRectangle(width=9.0, height=3.4, corner_radius=0.28, color=ManimColor("#D8D0EB"), stroke_width=2)
        body.move_to(DOWN * 0.45)
        anode = Line(LEFT * 3.0 + DOWN * 1.55, LEFT * 3.0 + UP * 0.65, color=orange, stroke_width=14)
        cathode = Line(RIGHT * 3.0 + DOWN * 1.55, RIGHT * 3.0 + UP * 0.65, color=blue, stroke_width=14)
        electrolyte = RoundedRectangle(width=5.2, height=0.75, corner_radius=0.35, color=green, fill_color=ManimColor("#E9F8F1"), fill_opacity=1)
        electrolyte.move_to(DOWN * 0.75)
        self.play(FadeIn(body, anode, cathode, electrolyte), run_time=0.9)

        labels = VGroup(
            Text("氧化：释放电子", font="PingFang SC", font_size=19, color=orange).next_to(anode, UP),
            Text("还原：接收电子", font="PingFang SC", font_size=19, color=blue).next_to(cathode, UP),
            Text("离子迁移", font="PingFang SC", font_size=18, color=green).move_to(electrolyte),
        )
        self.play(FadeIn(labels), run_time=0.7)

        circuit = Line(LEFT * 3.0 + UP * 0.65, LEFT * 3.0 + UP * 2.25, color=blue, stroke_width=3)
        circuit2 = Line(LEFT * 3.0 + UP * 2.25, RIGHT * 3.0 + UP * 2.25, color=blue, stroke_width=3)
        circuit3 = Line(RIGHT * 3.0 + UP * 2.25, RIGHT * 3.0 + UP * 0.65, color=blue, stroke_width=3)
        electron = Circle(radius=0.12, fill_color=blue, fill_opacity=1, stroke_width=0).move_to(LEFT * 2.5 + UP * 2.25)
        self.play(FadeIn(circuit, circuit2, circuit3, electron), run_time=0.7)
        self.play(electron.animate.move_to(RIGHT * 2.5 + UP * 2.25), run_time=2.3)

        ion = Circle(radius=0.10, fill_color=green, fill_opacity=1, stroke_width=0).move_to(LEFT * 1.8 + DOWN * 0.75)
        ion_arrow = Arrow(LEFT * 1.8 + DOWN * 1.1, RIGHT * 1.8 + DOWN * 1.1, color=green, buff=0)
        self.play(FadeIn(ion), GrowArrow(ion_arrow), run_time=0.6)
        self.play(ion.animate.move_to(RIGHT * 1.8 + DOWN * 0.75), run_time=1.8)

        result = Text("外电路电子流 + 内部离子迁移 → 维持电压", font="PingFang SC", font_size=25, color=ink)
        result.move_to(DOWN * 2.55)
        self.play(FadeIn(result), run_time=0.8)
        self.wait(1.2)
