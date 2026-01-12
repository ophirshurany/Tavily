import unittest
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.llm_client import LlmAgent

class TestGeminiConnection(unittest.IsolatedAsyncioTestCase):
    async def test_api_connection(self):
        """
        Integration test to verify Gemini API connection and model availability.
        Requires GOOGLE_API_KEY to be set.
        """
        print("\nTesting Gemini 2.0 Flash connection via LlmAgent...")
        try:
            agent = LlmAgent(model="gemini-2.0-flash")
            
            # Simple "ping" test
            response = await agent.async_run("Hello, simply reply 'OK'.")
            print(f"[generic] Response: {response}")
            
            # Basic validation
            self.assertIsNotNone(response, "Response should not be None")
            # We can't strictly assert content because LLMs vary, but we know we got *something*
            
        except ValueError as e:
            if "GOOGLE_API_KEY" in str(e):
                self.skipTest("Skipping integration test: GOOGLE_API_KEY not found.")
            else:
                self.fail(f"Configuration error: {e}")
        except Exception as e:
            self.fail(f"API Connection failed: {e}")

if __name__ == "__main__":
    unittest.main()
