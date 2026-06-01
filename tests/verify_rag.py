import sys
import os
import unittest

# Adjust path to import backend app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.ingestion import recursive_chunk_text, ingest_document
from app.retrieval import retrieve_relevant_chunks
from app.generation import generate_answer_with_citations
from app.observability import calculate_citation_coverage, get_observability_dashboard_stats

class TestRAGPipeline(unittest.TestCase):
    
    def setUp(self):
        self.sample_text = (
            "Antigravity AI is an advanced agentic coding system built by the Google DeepMind team. "
            "It runs on specialized container environments and supports directPair Programming with users. "
            "The primary objective of Antigravity is to solve complex software engineering tasks with complete "
            "accuracy and high-performance glassmorphic UI dashboards. "
            "\n\n"
            "Langfuse is used as the primary open-source observability framework for the Antigravity project. "
            "It captures full LLM traces, tracks cost percentiles, and monitors groundedness of system prompts."
        )
        self.filename = "test_deepmind_specs.txt"

    def test_recursive_chunking(self):
        chunks = recursive_chunk_text(self.sample_text, chunk_size=150, chunk_overlap=20)
        self.assertTrue(len(chunks) >= 2)
        # Ensure chunks overlap or cover the text
        self.assertIn("Antigravity AI", chunks[0])

    def test_e2e_ingestion_and_retrieval(self):
        # 1. Test Ingestion
        ingest_res = ingest_document(self.filename, self.sample_text)
        self.assertEqual(ingest_res["status"], "success")
        self.assertEqual(ingest_res["filename"], self.filename)
        self.assertTrue(ingest_res["chunks_count"] > 0)
        
        # 2. Test Retrieval
        retrieved = retrieve_relevant_chunks("Who built Antigravity AI?", top_k=2)
        self.assertTrue(len(retrieved) > 0)
        self.assertEqual(retrieved[0]["metadata"]["source"], self.filename)

    def test_generation_and_citation_parsing(self):
        # Retrieve chunks
        chunks = retrieve_relevant_chunks("Who built Antigravity AI?", top_k=2)
        
        # Generate answer with citations
        res = generate_answer_with_citations("Who built Antigravity?", chunks)
        
        self.assertIn("answer", res)
        self.assertIn("citations", res)
        self.assertTrue(res["tokens_used"] > 0)
        self.assertTrue(res["cost"] >= 0.0)
        
        # Verify coverage metric calculation
        coverage = calculate_citation_coverage(res["answer"], res["citations"], chunks)
        self.assertTrue(0.0 <= coverage <= 100.0)
        
        # Print results for manual inspection during run
        print("\n=== VERIFICATION TEST RESULTS ===")
        print(f"Generated Answer:\n{res['answer']}")
        print(f"Citations Extracted: {res['citations']}")
        print(f"Citation Groundedness Score: {coverage}%")
        print("=================================\n")

if __name__ == '__main__':
    unittest.main()
