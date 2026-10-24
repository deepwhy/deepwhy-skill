from manim import (
    DOWN,
    LEFT,
    RIGHT,
    UP,
    Circle,
    FadeIn,
    Line,
    Scene,
    Text,
    VGroup,
    always_redraw,
)


class SharedPullScene(Scene):
    def construct(self):
        self.camera.background_color = "#F7F8FC"
        ink = "#1F2937"
        violet = "#5B5BD6"
        apple_red = "#D95C4B"

        earth = Circle(
            radius=1.18,
            color=violet,
            fill_color="#E7E7FF",
            fill_opacity=0.9,
        ).move_to(LEFT * 4.1 + DOWN * 0.25)
        apple = Circle(
            radius=0.38,
            color=apple_red,
            fill_color="#FFE2DD",
            fill_opacity=1,
        ).move_to(RIGHT * 3.7 + DOWN * 0.25)
        earth_label = Text("EARTH / GIANT", font_size=24, color=ink).next_to(
            earth, DOWN, buff=0.42
        )
        apple_label = Text("APPLE / CHILD", font_size=24, color=ink).next_to(
            apple, DOWN, buff=0.28
        )
        rope = always_redraw(
            lambda: Line(
                earth.get_right(),
                apple.get_left(),
                color="#7C8CF8",
                stroke_width=5,
            )
        )
        pull_label = Text("SAME PULL", font_size=30, color=ink).to_edge(
            UP, buff=0.34
        )

        self.play(
            FadeIn(VGroup(earth, apple, earth_label, apple_label), shift=UP * 0.2),
            FadeIn(rope),
            run_time=1.2,
        )
        self.play(FadeIn(pull_label), run_time=0.6)
        self.play(
            earth.animate.shift(RIGHT * 0.32),
            earth_label.animate.shift(RIGHT * 0.32),
            apple.animate.shift(LEFT * 2.2),
            apple_label.animate.shift(LEFT * 2.2),
            run_time=2.2,
        )
        result = Text(
            "LIGHT OBJECT MOVES MORE",
            font_size=28,
            color=apple_red,
        ).to_edge(DOWN, buff=0.32)
        self.play(FadeIn(result, shift=UP * 0.15), run_time=0.8)
        self.wait(0.5)
