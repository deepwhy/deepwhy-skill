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


class ElectronDrift(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#F8F6FF")
        ink = ManimColor("#28233D")
        violet = ManimColor("#7055D9")
        blue = ManimColor("#3E8EF7")

        title = Text("电子漂移：随机运动叠加整体方向", font="PingFang SC", font_size=34, color=ink)
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.0)

        wire = Line(LEFT * 5.8, RIGHT * 5.8, color=ManimColor("#D8D0EB"), stroke_width=14)
        atoms = VGroup(
            *[
                Circle(radius=0.20, fill_color=ManimColor("#B8ADDD"), fill_opacity=1, stroke_width=0)
                .move_to(RIGHT * x)
                for x in (-3.6, -1.8, 0.0, 1.8, 3.6)
            ]
        )
        electron = Circle(radius=0.15, fill_color=blue, fill_opacity=1, stroke_width=0).move_to(LEFT * 5.0)
        label = Text("没有电场：方向随机，平均位移≈0", font="PingFang SC", font_size=25, color=ink)
        label.move_to(DOWN * 2.25)
        self.play(FadeIn(wire), LaggedStart(*[FadeIn(atom) for atom in atoms]), FadeIn(electron), FadeIn(label), run_time=1.0)

        random_points = [
            LEFT * 4.0 + UP * 0.35,
            LEFT * 3.2 + DOWN * 0.35,
            LEFT * 2.5 + UP * 0.25,
            LEFT * 1.8 + DOWN * 0.28,
        ]
        for point in random_points:
            self.play(electron.animate.move_to(point), run_time=0.35)

        field = Arrow(LEFT * 5.0 + DOWN * 1.25, RIGHT * 2.0 + DOWN * 1.25, color=violet, buff=0)
        field_label = Text("电场 E", font="PingFang SC", font_size=23, color=violet)
        field_label.next_to(field, DOWN, buff=0.16)
        self.play(GrowArrow(field), FadeIn(field_label), FadeOut(label), run_time=0.8)

        drift_label = Text("有电场：随机热运动 + 缓慢漂移 = 电流", font="PingFang SC", font_size=25, color=ink)
        drift_label.move_to(DOWN * 2.25)
        self.play(FadeIn(drift_label), run_time=0.5)
        self.play(
            electron.animate.move_to(LEFT * 2.0 + UP * 0.15),
            run_time=0.8,
        )
        self.play(
            electron.animate.move_to(RIGHT * 2.0 + DOWN * 0.10),
            run_time=1.3,
        )
        self.play(
            electron.animate.move_to(RIGHT * 5.0),
            run_time=1.2,
        )
        self.wait(1.2)
