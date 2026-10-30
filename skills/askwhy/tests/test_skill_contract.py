from __future__ import annotations

import unittest
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


class SkillContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.prompt = (SKILL_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

    def test_required_choices_are_ordered_stage_then_deliverable(self) -> None:
        stage = self.skill.index("**Learning stage:**")
        deliverable = self.skill.index("**Deliverable:**")
        self.assertLess(stage, deliverable)
        self.assertIn("There is no default", self.skill)
        self.assertIn("Default to", self.skill)
        self.assertIn("`只生成知识页`", self.skill)
        self.assertIn("`知识页 + 讲解视频`", self.skill)

    def test_interaction_requires_selectable_options(self) -> None:
        self.assertIn("structured choice", self.skill)
        self.assertIn("numbered menu", self.skill)
        self.assertIn("Never ask", self.skill)
        self.assertIn("page-only option selected by default", self.prompt)

    def test_video_export_is_conditional_and_documented(self) -> None:
        self.assertIn("Only when the user selects video export", self.skill)
        self.assertIn(
            "references/video-export.md",
            self.skill,
        )
        self.assertTrue((SKILL_ROOT / "references" / "video-export.md").is_file())
        self.assertIn("Do not enter this workflow", (
            SKILL_ROOT / "references" / "video-export.md"
        ).read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
