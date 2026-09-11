import tempfile
import unittest
from pathlib import Path

from code_x_agent.skills import catalog, get_skill, resolve


class SkillsTests(unittest.TestCase):
    def test_catalog_and_get(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_dir = root / "skills" / "demo"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text('---\ndescription: "demo coding"\n---\n# Demo\n', encoding="utf-8")
            self.assertEqual(catalog(root)[0]["name"], "demo")
            self.assertTrue(get_skill(root, "demo")["ok"])
            matches = resolve(root, "demo coding", 5)
            self.assertEqual(matches[0]["name"], "demo")
