# Tavily Summarization Agent Squad

## 🎯 Goal
Develop a production-grade web content summarization system that balances **Latency**, **Accuracy**, and **Cost**.

## 🏗️ Solution Structure
The solution uses a **2-Agent Architecture** for optimal latency-quality balance.

### Core Agents (`src/agents/`)
1. **Summarizer (`summarizer.py`)**: 
    - **Role**: Combines research and writing into a single LLM call.
    - **Input**: Raw web content (URL, text, metadata).
    - **Output**: Structured `SummaryOutput` (summary, char_count, latency).
    - **Strategies**:
        - **Fast Strategy** (`fast`): Direct extraction, 1 LLM call, no Judge.
        - **Advanced Strategy** (`advanced`): Chain-of-thought reasoning + Judge validation.

2. **Judge (`judge.py`)**: 
    - **Role**: Quality gatekeeper (optional, used for "Advanced" strategy only).
    - **Loop Logic**: Validates length < 1500 chars. Triggers 1 retry if needed.

> **Note on Previous Architecture**: 
> We initially used a 3-Agent flow (Researcher → Writer → Judge) for explainability.
> However, for production URL summarization, we consolidated to 2 Agents to halve latency.
> The old agents (`researcher.py`, `writer.py`) are preserved for research/debugging.

### Infrastructure
- **LLM Adapter (`google_adk.py`)**: Async-first wrapper using OpenAI `gpt-4o-mini`.
- **Benchmark Pipeline (`src/benchmark.py`)**: Async parallel processing with `Semaphore` rate limiting.

---

## 📊 Evaluation & Metrics Justification

To provide a holistic view of performance, we selected a mix of deterministic and semantic metrics:

### 1. Latency (ms)
- **Why**: Crucial for Tavily's "Quick" promise.
- **Goal**: "Fast" strategy must be significantly faster than "Advanced".

### 2. ROUGE-L (Recall)
- **Why**: Measures the longest common subsequence between the generated summary and the baseline.
- **Justification**: Good proxy for structure preservation and ensuring critical phrases from the baseline are retained.

### 3. BERTScore (Semantic Similarity)
- **Why**: ROUGE fails to capture paraphrasing. BERTScore uses contextual embeddings to measure if the *meaning* matches the baseline, even if words differ.
- **Justification**: Essential for evaluating the "Advanced" strategy, which may rewrite content more fluently.

### 4. Judge Pass Rate & Length Compliance
- **Why**: Production reliability.
- **Justification**: A summary is useless if it consumes too many tokens or fails basic formatting rules.

---

## 🚀 Production Feasibility (Millions of Requests)
Scaling this architecture to millions of requests/day requires addressing three bottlenecks:

### 1. Cost & Token Economy
- **Current**: `gpt-4o-mini` is cost-effective.
- **Scale**: For 1M requests, even cheap models add up.
- **Optimization**: 
    - **Caching**: 40-50% of web queries are repetitive. Cache `ResearchBrief` results.
    - **Distillation**: Fine-tune a smaller model (e.g., Llama-3-8B) on the "Advanced" outputs to run locally or cheaply.

### 2. Latency & Concurrency
- **bottleneck**: Sequential Agent Hops (Researcher -> Writer -> Judge).
- **Optimization**:
    - **Speculative Decoding**: Run "Fast" and "Advanced" in parallel; return "Fast" immediately if "Advanced" takes too long.
    - **Streaming**: Stream the Writer's output directly to the user before the Judge finishes (optimistic UI), retracting only if Judge fails (rare).

### 3. Reliability (The "Judge" Loop)
- **Risk**: Infinite loops if the Writer keeps failing.
- **Mitigation**: 
    - Strict `max_retries=2`.
    - Fallback to a rigid heuristic extraction (non-LLM) if the LLM squad fails repeatedly.

---

## 🏃‍♂️ Running the Benchmark
1. Install dependencies: `pip install -r requirements.txt` (ensure openai, rouge-score, bert-score, pydantic)
2. Run schema verification: `python -m src.benchmark --limit 10`
3. View results: `results.csv`

### ⚠️ Usage Note: Rate Limiting
The benchmark script includes a **1-second sleep** (`time.sleep(1)`) between samples.
- **Reason**: To prevent hitting OpenAI's `Tokens Per Minute (TPM)` or `Requests Per Minute (RPM)` limits during high-concurrency runs.
- **Optimization**: If you have a High-Tier OpenAI account, you can reduce this delay in `src/benchmark.py` for faster execution.

---

## ⚡ The "Speed" Solution: Asynchronous Concurrency

Since LLM API calls are "I/O bound" (your code spends 99% of its time waiting for the server), you can use Python's `asyncio` to fire off multiple requests at once. Instead of waiting for Call 1 to finish before starting Call 2, you start both simultaneously.

To avoid hitting your Rate Limits (RPM/TPM) too hard, you should use a `Semaphore` to act as a gatekeeper.

### 🛠️ Implementation Example (Python)

```python
import asyncio
import os
from src.schemas import SummaryOutput

# Set this based on your API tier (e.g., 5-10 for free tier)
MAX_CONCURRENT_CALLS = 10 
semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)

async def process_row(agent, row_data):
    async with semaphore:
        # Assuming your agent has an 'async_run' method
        return await agent.async_run(row_data)

async def run_benchmark_parallel(agent, dataset):
    tasks = [process_row(agent, row) for row in dataset]
    # This fires all tasks and waits for them to gather back
    results = await asyncio.gather(*tasks)
    return results
```

### 🏭 Production Recommendation
For a "production environment handling millions of requests," we recommend:
- **Batch API**: For non-urgent background summarization.
- **Async Parallel**: For real-time user requests.

---

## 📈 Performance SLOs vs. User Expectations (2026 Standards)

| Strategy | Tier | Target Latency | Quality (ROUGE-L) | Justification |
|----------|------|----------------|-------------------|---------------|
| **Fast (Local/SLM)** | Local GPU (mT5 / Llama-3.2-1B) | **< 1.5s** | ~0.15 - 0.25 | Sub-2-second responses are essential for synchronous web experiences (e.g., hover-previews, real-time search results). This reflects a "Zero-Network" architecture where latency is bounded only by local inference speed. |
| **Fast (API)** | GPT-4o-mini (Zero-shot) | **2 - 4s** | ~0.20 - 0.30 | Includes network round-trip and shared-tenant API latency. Acceptable for standard "summarize this page" button-click user actions. |
| **Advanced (Multi-Agent)** | GPT-4o-mini (Researcher → Writer → Judge) | **8 - 15s** | ~0.25 - 0.40 | This is a "Research Task." Users accept longer waits (**Deliberate Latency**) for high-accuracy, judge-verified content. In production, this would be handled via an async "Job ID" or a streaming status bar. |

> [!TIP]
> **Balancing Act**: The "Fast (API)" strategy offers the best latency-to-quality ratio for most production use cases. Reserve "Advanced" for high-stakes summarization where accuracy is paramount.
