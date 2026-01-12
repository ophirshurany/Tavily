from typing import Any
from google_adk import LlmAgent
from src.schema import RawContent, ResearchBrief

class ResearcherAgent:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        with open("src/agents/researcher.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
            
        self.agent = LlmAgent(
            model=model_name,
            system_prompt=system_prompt,
            output_type=ResearchBrief
        )

    async def async_analyze(self, content: RawContent) -> ResearchBrief:
        """
        Analyzes raw content to produce a research brief asynchronously.
        """
        response = await self.agent.async_run(
            f"Content URL: {content.url}\n\nContent:\n{content.text}\n\nMetadata:\n{content.metadata}"
        )
        return response

    def analyze(self, content: RawContent) -> ResearchBrief:
        """
        Analyzes raw content to produce a research brief.
        """
        # We pass the raw text and metadata to the model
        response = self.agent.run(
            f"Content URL: {content.url}\n\nContent:\n{content.text}\n\nMetadata:\n{content.metadata}"
        )
        return response
