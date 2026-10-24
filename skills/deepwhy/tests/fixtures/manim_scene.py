from manim import BLUE, Create, DOWN, Scene, Square


class DeepWhyDemo(Scene):
    def construct(self):
        block = Square(color=BLUE)
        self.play(Create(block), run_time=0.4)
        self.play(block.animate.shift(DOWN), run_time=0.7)
