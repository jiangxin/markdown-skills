"""ensure_venv.py creates .venv and installs requirements.txt."""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
ENSURE = SKILL_ROOT / "scripts" / "ensure_venv.py"
REQUIREMENTS = SKILL_ROOT / "requirements.txt"


class TestEnsureVenv(unittest.TestCase):
    def test_requirements_lists_markdown(self):
        text = REQUIREMENTS.read_text(encoding="utf-8")
        self.assertIn("markdown", text)

    def test_ensure_venv_creates_interpreter_with_markdown(self):
        with tempfile.TemporaryDirectory(prefix="pages-venv-") as raw:
            skill = Path(raw)
            (skill / "scripts").mkdir()
            script = skill / "scripts" / "ensure_venv.py"
            script.write_text(ENSURE.read_text(encoding="utf-8"), encoding="utf-8")
            (skill / "requirements.txt").write_text("markdown>=3.5\n", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(skill),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            reported = Path(result.stdout.strip())
            expected = skill / ".venv" / "bin" / "python"
            self.assertTrue(expected.exists(), expected)
            self.assertEqual(reported.resolve(), expected.resolve())
            stamp = skill / ".venv" / ".requirements.sha256"
            self.assertTrue(stamp.is_file())
            digest = hashlib.sha256((skill / "requirements.txt").read_bytes()).hexdigest()
            self.assertEqual(stamp.read_text(encoding="utf-8").strip(), digest)
            probe = subprocess.run(
                [str(expected), "-c", "import markdown; print(markdown.__version__)"],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertTrue(probe.stdout.strip())

            again = subprocess.run(
                [sys.executable, str(script)],
                cwd=str(skill),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(Path(again.stdout.strip()).resolve(), expected.resolve())


if __name__ == "__main__":
    unittest.main()
