from __future__ import annotations

import unittest
from pathlib import Path

from app.config import _dotenv_paths


class DotEnvPathTests(unittest.TestCase):
    def test_container_layout_does_not_raise(self) -> None:
        paths = _dotenv_paths(Path("/app/app/config.py"))
        self.assertTrue(paths)
        self.assertTrue(all(path.name == ".env" for path in paths))

    def test_repo_layout_includes_root_env(self) -> None:
        repo = Path(__file__).resolve().parents[3]
        paths = _dotenv_paths(repo / "projects/webawesome-site-agent/app/config.py")
        self.assertIn(repo / ".env", paths)


if __name__ == "__main__":
    unittest.main()
