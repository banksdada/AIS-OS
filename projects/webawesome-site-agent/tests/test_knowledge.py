from __future__ import annotations

import unittest

from app.knowledge import _boost, build_context, search


class KnowledgeSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.docs = {
            "ai-services.md": "# AI services\nWe run AI readiness audits and set up an AIOS for clients. " * 3,
            "site/pages/services.md": "# Services\nStrategy, product and engineering. " * 3,
            "site/posts/ai-ai-ai-long.md": "# AI post\nAI AI AI " + "filler words here. " * 2000,
        }

    def test_curated_doc_beats_long_post_repeating_term(self) -> None:
        results = search("AIOS audit", docs=self.docs)
        self.assertTrue(results)
        self.assertEqual(results[0][0], "ai-services.md")

    def test_pages_outrank_posts(self) -> None:
        results = search("engineering", docs=self.docs)
        names = [name for name, _ in results]
        self.assertEqual(names[0], "site/pages/services.md")

    def test_boost_ordering(self) -> None:
        self.assertGreater(_boost("services.md"), _boost("site/pages/about.md"))
        self.assertGreater(_boost("site/pages/about.md"), _boost("site/posts/x.md"))

    def test_build_context_uses_curated_docs(self) -> None:
        context = build_context("AI readiness audit")
        self.assertIn("AI readiness", context)


if __name__ == "__main__":
    unittest.main()
