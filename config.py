"""
Centralized configuration for Tavily Summarization Benchmark.
"""

# =============================================================================
# Model Configuration
# =============================================================================
MODEL_NAME = "gemini-2.0-flash"

# =============================================================================
# Rate Limiting (Optimized for Stability)
# =============================================================================
# We use 80% of actual limits to create a safety buffer
MAX_RPM = 1600      # Actual limit 2000
MAX_TPM = 3_200_000 # Actual limit 4,000,000

# Lowering concurrency prevents "bursting" past the TPM limit
MAX_CONCURRENT_CALLS = 15 

# =============================================================================
# Retry Configuration (More patient backoff)
# =============================================================================
MAX_RETRIES = 5
# Starting at 2s gives the 60-second rolling window time to recover
BASE_RETRY_DELAY = 2.0

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
