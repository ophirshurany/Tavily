import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from src.agents.summarizer import SummarizerAgent
from src.schema import RawContent, SummaryOutput, JudgeFeedback

class TestPipeline(unittest.IsolatedAsyncioTestCase):
    async def test_summarizer_refinement(self):
        # Mocking
        mock_agent = AsyncMock()
        
        summarizer = SummarizerAgent()
        summarizer.agent = mock_agent # Inject mock
        
        content = RawContent(url="http://test.com", text="test content", metadata={})
        feedback = JudgeFeedback(status="FAIL", score_accuracy=0.5, critique="Too short")
        original_summary = "Short."
        
        # Setup return value for refinement
        expected_refinement = SummaryOutput(
            content="Longer summary fixed.",
            strategy="advanced",
            char_count=20,
            latency_ms=100
        )
        mock_agent.async_run.return_value = expected_refinement
        
        # Act
        result = await summarizer.async_refine_summary(content, "advanced", feedback, original_summary)
        
        # Assert
        self.assertEqual(result.content, "Longer summary fixed.")
        # Verify prompt included critique
        call_args = mock_agent.async_run.call_args[0][0]
        self.assertIn("CRITIQUE", call_args)
        self.assertIn("Too short", call_args)

if __name__ == "__main__":
    unittest.main()
