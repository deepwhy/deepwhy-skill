from manim import (
    Arrow,
    Circle,
    Create,
    DOWN,
    FadeIn,
    FadeOut,
    Flash,
    GrowArrow,
    LaggedStart,
    LEFT,
    Line,
    ManimColor,
    ORANGE,
    RED,
    RIGHT,
    Scene,
    Text,
    UP,
    VGroup,
    Write,
)


class ElectronLatticeHeat(Scene):
    def construct(self):
        self.camera.background_color = ManimColor("#F8F6FF")
        ink = ManimColor("#28233D")
        violet = ManimColor("#7055D9")
        blue = ManimColor("#3E8EF7")
        heat = ManimColor("#F0A24B")

        title = Text("电子碰撞 → 晶格振动 → 发热", font="PingFang SC", font_size=34, color=ink)
        title.to_edge(UP, buff=0.55)
        self.play(Write(title), run_time=1.0)

        wire = Line(LEFT * 5.7 + DOWN * 0.2, RIGHT * 5.7 + DOWN * 0.2, color=ManimColor("#D8D0EB"), stroke_width=14)
        atoms = VGroup(
            *[
                Circle(radius=0.25, fill_color=ManimColor("#B8ADDD"), fill_opacity=1, stroke_width=0)
                .move_to(RIGHT * x + DOWN * 0.2)
                for x in (-2.0, 0.0, 2.0, 4.0)
            ]
        )
        self.play(Create(wire), LaggedStart(*[FadeIn(atom) for atom in atoms]), run_time=1.2)

        electron = Circle(radius=0.16, fill_color=blue, fill_opacity=1, stroke_width=0).move_to(LEFT * 5.0 + DOWN * 0.2)
        electron_label = Text("电子", font="PingFang SC", font_size=22, color=blue).next_to(electron, DOWN, buff=0.35)
        field = Arrow(LEFT * 5.0 + UP * 1.1, RIGHT * 1.2 + UP * 1.1, color=violet, buff=0)
        field_label = Text("电场推动", font="PingFang SC", font_size=22, color=violet).next_to(field, UP, buff=0.22)
        self.play(FadeIn(electron, electron_label), GrowArrow(field), FadeIn(field_label), run_time=1.0)
        self.play(electron.animate.move_to(LEFT * 2.0 + DOWN * 0.2), run_time=0.9)

        collision = Flash(atoms[0].get_center(), color=ORANGE, line_length=0.45, num_lines=12, flash_radius=0.55)
        impact = Text("碰撞：能量交给晶格", font="PingFang SC", font_size=24, color=heat)
        impact.move_to(RIGHT * 2.5 + UP * 1.5)
        self.play(collision, atoms[0].animate.set_fill(RED, opacity=0.9), FadeIn(impact), run_time=0.7)

        wave = VGroup(
            Circle(radius=0.35, stroke_color=heat, stroke_width=3),
            Circle(radius=0.55, stroke_color=heat, stroke_width=2),
        ).move_to(atoms[0].get_center())
        self.play(wave.animate.scale(2.2).set_opacity(0), run_time=0.9)

        for atom in atoms:
            self.play(atom.animate.shift(UP * 0.10).set_fill(RED, opacity=0.95), run_time=0.12)
            self.play(atom.animate.shift(DOWN * 0.10), run_time=0.12)

        wire.set_color(heat)
        result = Text("无规则热振动增强  →  温度升高", font="PingFang SC", font_size=27, color=heat)
        result.move_to(DOWN * 2.35)
        self.play(FadeOut(field_label), FadeOut(impact), FadeIn(result), run_time=0.8)
        self.wait(1.1)
