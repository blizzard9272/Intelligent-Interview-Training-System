from __future__ import annotations

import unittest

from app.rag.query_router import build_query_plan, classify_query_route


class QueryRouterTests(unittest.TestCase):
    def test_classify_concept_question(self) -> None:
        route = classify_query_route("什么是 RAG？它和微调有什么区别？")

        self.assertEqual(route.intent, "concept")
        self.assertIn("concept_explanation", route.preferred_content_types)
        self.assertIn("concept_guide", route.preferred_document_kinds)

    def test_classify_interview_question(self) -> None:
        route = classify_query_route("面试中如果被问到依赖注入，你会怎么回答？")

        self.assertEqual(route.intent, "interview")
        self.assertTrue(route.prefer_question_opening)
        self.assertIn("question_answer", route.preferred_content_types)

    def test_build_query_plan_appends_general_fallback(self) -> None:
        route = classify_query_route("怎么实现一个简单的登录接口？")
        plan = build_query_plan(route)

        self.assertGreaterEqual(len(plan), 2)
        self.assertEqual(plan[-1], {})
        self.assertIn({"content_type_hint": "implementation_detail"}, plan)


if __name__ == "__main__":
    unittest.main()
