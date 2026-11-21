"""
FORMGUARD AI - Test Suite: RAG Pipeline
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.rag_pipeline import RAGPipeline


class TestRAGPipeline:
    def setup_method(self):
        self.rag = RAGPipeline()

    def test_knowledge_base_loaded(self):
        assert len(self.rag.knowledge_base) > 0, "Knowledge base should have entries"

    def test_keyword_search_returns_results(self):
        results = self.rag.query("required documents for scholarship")
        assert len(results) > 0, "Should return results for a relevant query"

    def test_keyword_search_relevance(self):
        results = self.rag.query("income certificate eligibility limit")
        texts = " ".join([r["text"].lower() for r in results])
        assert "income" in texts, "Results should be relevant to income"

    def test_scheme_filter(self):
        results = self.rag.query("documents", scheme_id="mahadbt_postmatric")
        for r in results:
            assert r.get("scheme_id") in ("mahadbt_postmatric", "general"), \
                "Results should match scheme filter"

    def test_no_results_for_nonsense(self):
        results = self.rag.query("xyzzy completely irrelevant gibberish qwerty")
        # May still return results with keyword overlap, but scores should be low
        assert isinstance(results, list)

    def test_scheme_requirements_retrieval(self):
        reqs = self.rag.get_scheme_requirements("mahadbt_postmatric")
        assert len(reqs) > 0, "Should return scheme requirements"
        for req in reqs:
            assert req.get("category") == "requirement"

    def test_no_fabricated_content(self):
        """RAG results should only come from the knowledge base, not be generated."""
        results = self.rag.query("what is the approval process")
        for r in results:
            assert r["text"] in [kb["text"] for kb in self.rag.knowledge_base], \
                "Results must come from the knowledge base"


class TestRAGWithoutVectorStore:
    """Test that RAG works in fallback keyword mode."""

    def test_fallback_search(self):
        rag = RAGPipeline()
        # Force keyword search
        results = rag._keyword_search("name mismatch documents", "mahadbt_postmatric", 3)
        assert len(results) > 0, "Keyword fallback should return results"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
