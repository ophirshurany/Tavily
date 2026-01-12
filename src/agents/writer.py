from google_adk import LlmAgent
from src.schema import ResearchBrief, SummaryOutput
import time

class WriterAgent:
    def __init__(self, model_name: str = "gpt-4o-mini"):
        with open("src/agents/writer.md", "r", encoding="utf-8") as f:
            system_prompt = f.read()
            
        self.agent = LlmAgent(
            model=model_name,
            system_prompt=system_prompt,
            output_type=SummaryOutput
        )

    async def async_write_summary(self, brief: ResearchBrief, strategy: str = "fast") -> SummaryOutput:
        """
        Generates a summary based on the brief and strategy asynchronously.
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()} (Focus on latency/quality trade-off as defined)\n"
            f"Primary Language: {brief.primary_language}\n"
            f"Key Entities: {brief.key_entities}\n"
            f"Core Themes: {brief.core_themes}\n"
            f"Critical Facts: {brief.critical_facts}\n"
        )
        
        if strategy == "advanced":
            prompt += "\nUse your advanced thinking process."
            
        summary_output = await self.agent.async_run(prompt)
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy
        
        return summary_output

    def write_summary(self, brief: ResearchBrief, strategy: str = "fast") -> SummaryOutput:
        """
        Generates a summary based on the brief and strategy.
        Tracks simple latency internally, though benchmarks might measure wrapper time.
        """
        start_time = time.time()
        
        prompt = (
            f"Strategy: {strategy.upper()} (Focus on latency/quality trade-off as defined)\n"
            f"Primary Language: {brief.primary_language}\n"
            f"Key Entities: {brief.key_entities}\n"
            f"Core Themes: {brief.core_themes}\n"
            f"Critical Facts: {brief.critical_facts}\n"
        )
        
        if strategy == "advanced":
            # Just a hint to the model, or we could chain differently.
            # The prompt already instructs to use 'multi-step' for advanced.
            prompt += "\nUse your advanced thinking process."
            
        summary_output = self.agent.run(prompt)
        
        # Ensure latency and char_count are accurate if the model hallucinated them
        # We overwrite them with actual measured values for the system's truth
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Update the object with real measurements
        summary_output.latency_ms = latency_ms
        summary_output.char_count = len(summary_output.content)
        summary_output.strategy = strategy # Ensure it matches requested
        
        return summary_output
