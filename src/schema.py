from pydantic import BaseModel, Field, HttpUrl
from typing import List, Literal, Optional

class RawContent(BaseModel):
    """Initial input provided to the multi-agent system."""
    url: Optional[HttpUrl] = Field(None, description="The source URL of the content")
    text: str = Field(..., description="The raw, unformatted web content to be summarized")
    metadata: dict = Field(default_factory=dict, description="Additional context like page title or scrape date")

class ResearchBrief(BaseModel):
    """Structured insights extracted by the Researcher Agent."""
    primary_language: str = Field(..., description="ISO 639-1 language code (e.g., 'en', 'he', 'pl')")
    key_entities: List[str] = Field(..., description="Critical names, places, or technical terms")
    core_themes: List[str] = Field(..., description="The main topics identified in the source content")
    critical_facts: List[str] = Field(..., description="Non-negotiable data points to include in the summary")

class SummaryOutput(BaseModel):
    """The final draft produced by the Writer Agent."""
    content: str = Field(..., max_length=1500, description="The summary text (capped at 1,500 chars)")
    strategy: Literal["fast", "advanced"] = Field(..., description="The strategy used for generation")
    char_count: int = Field(..., description="The length of the summary content")
    latency_ms: float = Field(..., description="Time taken to generate the summary in milliseconds")
    tokens_input: Optional[int] = Field(0, description="Number of input tokens")
    tokens_output: Optional[int] = Field(0, description="Number of output tokens")
    language: Optional[str] = Field("unknown", description="ISO 639-1 language code detected from content")

class JudgeFeedback(BaseModel):
    """Validation and critique provided by the Judge Agent."""
    status: Literal["PASS", "FAIL"] = Field(..., description="Whether the summary meets all requirements")
    score_accuracy: float = Field(..., ge=0, le=1.0, description="Confidence score in the summary's accuracy")
    critique: Optional[str] = Field(None, description="Required feedback if status is FAIL to guide the Writer's rewrite")