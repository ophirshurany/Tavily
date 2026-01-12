"""
Centralized configuration for Tavily Summarization Benchmark.
"""

# =============================================================================
# Model Configuration
# =============================================================================
MODEL_NAME = "gemini-2.0-flash"  # Stable version with 2K RPM

# =============================================================================
# Rate Limiting (Gemini 2.0 Flash Tier 1)
# =============================================================================
MAX_RPM = 2000      # Requests per minute
MAX_TPM = 4_000_000 # Tokens per minute

# Concurrent calls - set based on rate limits
# With 2K RPM, we can safely do ~30 concurrent calls
MAX_CONCURRENT_CALLS = 30

# =============================================================================
# Retry Configuration
# =============================================================================
MAX_RETRIES = 5
BASE_RETRY_DELAY = 0.5  # seconds (exponential backoff: 0.5, 1, 2, 4, 8s)

# =============================================================================
# Benchmark Defaults
# =============================================================================
DEFAULT_SAMPLE_LIMIT = 1000
STRATEGIES = ["fast", "advanced"]

# =============================================================================
# Content Limits
# =============================================================================
MAX_CONTENT_CHARS = 8000  # Max chars to send to LLM per request
MAX_SUMMARY_CHARS = 1500  # Target max summary length

# =============================================================================
# Quality Score Weights (must sum to 1.0)
# =============================================================================
WEIGHTS = {
    "bert_score": 0.60,   # Primary semantic measure
    "judge_score": 0.25,  # LLM quality confidence
    "length_compliance": 0.10,  # Length compliance
    "rouge_l": 0.05,      # Sanity check only
}
