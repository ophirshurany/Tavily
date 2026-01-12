import time
from google_adk import LlmAgent
from src.schema import RawContent, SummaryOutput, JudgeFeedback
from config import MODEL_NAME, MAX_CONTENT_CHARS


class SummarizerAgent:
    """
    Consolidated agent that combines Researcher + Writer into a single LLM call.
    Produces a summary directly from raw content.
    """
    
    def __init__(self, model_name: str = MODEL_NAME):
        with open("src/agents/summarizer.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
            
        self.agent = LlmAgent(
            model=model_name,
            system_prompt=system_prompt,
            output_type=SummaryOutput
        )

    def summarize(self, content: RawContent, strategy: str = "fast") -> SummaryOutput:
        """
        Generates a summary directly from raw content in a single LLM call.
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()}\n"
            f"URL: {content.url}\n"
            f"Title: {content.metadata.get('title', 'N/A')}\n\n"
            f"Content:\n{content.text[:8000]}\n"  # Limit input to avoid token overflow
        )
        
        if strategy == "advanced":
            prompt += "\nUse your advanced chain-of-thought reasoning."
            
        summary_output = self.agent.run(prompt)
        
        # Overwrite with actual measurements
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy
        
        return summary_output

    async def async_summarize(self, content: RawContent, strategy: str = "fast") -> SummaryOutput:
        """
        Generates a summary asynchronously in a single LLM call.
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()}\n"
            f"URL: {content.url}\n"
            f"Title: {content.metadata.get('title', 'N/A')}\n\n"
            f"Content:\n{content.text[:8000]}\n"
        )
        
        if strategy == "advanced":
            prompt += "\nUse your advanced chain-of-thought reasoning."
            
        summary_output = await self.agent.async_run(prompt)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy
        
    async def async_refine_summary(self, content: RawContent, strategy: str, feedback: JudgeFeedback, original_summary: str) -> SummaryOutput:
        """
        Refines a summary based on Judge feedback.
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()}\n"
            f"URL: {content.url}\n"
            f"Title: {content.metadata.get('title', 'N/A')}\n\n"
            f"Original Content:\n{content.text[:8000]}\n\n"
            f"PREVIOUS SUMMARY:\n{original_summary}\n\n"
            f"CRITIQUE (Why it failed):\n{feedback.critique}\n\n"
            f"INSTRUCTIONS:\n"
            f"Rewrite the summary to address the critique above. "
            f"Ensure you still follow the original constraints (max 1500 chars, same language as source)."
        )
        
        summary_output = await self.agent.async_run(prompt)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy
        
        return summary_output

    def refine_summary(self, content: RawContent, strategy: str, feedback: JudgeFeedback, original_summary: str) -> SummaryOutput:
        """
        Refines a summary based on Judge feedback (sync version).
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()}\n"
            f"URL: {content.url}\n"
            f"Title: {content.metadata.get('title', 'N/A')}\n\n"
            f"Original Content:\n{content.text[:8000]}\n\n"
            f"PREVIOUS SUMMARY:\n{original_summary}\n\n"
            f"CRITIQUE (Why it failed):\n{feedback.critique}\n\n"
            f"INSTRUCTIONS:\n"
            f"Rewrite the summary to address the critique above. "
            f"Ensure you still follow the original constraints (max 1500 chars, same language as source)."
        )
        
        summary_output = self.agent.run(prompt)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy
        
        return summary_output
