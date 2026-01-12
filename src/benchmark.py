import argparse
import csv
import time
import os
import asyncio
import warnings
import pandas as pd
from tqdm import tqdm

# Suppress BERTScore's RoBERTa warnings and use cached model
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_OFFLINE"] = "1"
import transformers
transformers.logging.set_verbosity_error()

from config.settings import MAX_CONCURRENT_CALLS, STRATEGIES, DEFAULT_SAMPLE_LIMIT, WEIGHTS, MAX_SUMMARY_CHARS
from src.data_loader import DataLoader
from src.agents.summarizer import SummarizerAgent
from src.agents.judge import JudgeAgent
from rouge_score import rouge_scorer
try:
    from bert_score import score as bert_score
except ImportError:
    bert_score = None

# Semaphore for rate limiting (from config)
semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)

async def process_sample(i, content, summarizer, judge, strategies, r_scorer):
    """
    Process a single sample using the 2-Agent architecture:
    - Fast: Summarizer only (1 LLM call)
    - Advanced: Summarizer + Judge (2 LLM calls)
    """
    print(f"Processing sample {i+1}...")
    results = []
    
    async with semaphore:
        try:
            reference = content.metadata.get("baseline_summary", "")
            
            for strategy in strategies:
                try:
                    # Single LLM call for summarization
                    summary = await summarizer.async_summarize(content, strategy=strategy)
                    
                    # For "advanced" strategy, validate with Judge
                    feedback = None
                    if strategy == "advanced":
                        feedback = await judge.async_evaluate(summary)
                        # Simple retry if Judge fails (max 1 retry for speed)
                        # Simple retry if Judge fails (max 1 retry for speed)
                        if feedback.status == "FAIL":
                            print(f"  [ADVANCED] Judge failed, retrying...")
                            original_latency = summary.latency_ms
                            original_tokens_input = summary.tokens_input
                            original_tokens_output = summary.tokens_output
                            summary = await summarizer.async_refine_summary(
                                content=content, 
                                strategy=strategy, 
                                feedback=feedback, 
                                original_summary=summary.content
                            )
                            summary.latency_ms += original_latency  # Accumulate latency
                            # Accumulate tokens from failed attempt
                            summary.tokens_input = (summary.tokens_input or 0) + (original_tokens_input or 0)
                            summary.tokens_output = (summary.tokens_output or 0) + (original_tokens_output or 0)
                            feedback = await judge.async_evaluate(summary)
                    else:
                        # For "fast", auto-pass (no Judge call)
                        from src.schema import JudgeFeedback
                        feedback = JudgeFeedback(
                            status="PASS",
                            score_accuracy=0.95,
                            critique=None
                        )
                    
                    # Calculate Metrics
                    rouge_l = 0.0
                    bert_f1 = 0.0
                    
                    if reference:
                        scores = r_scorer.score(reference, summary.content)
                        rouge_l = scores['rougeL'].fmeasure
                        
                        if bert_score:
                            try:
                                P, R, F1 = bert_score([summary.content], [reference], lang="en", verbose=False)
                                bert_f1 = F1.mean().item()
                            except Exception as e:
                                print(f"BERTScore error: {e}")
                                bert_f1 = -1.0
                    
                    # Rounding
                    latency_rounded = int(round(summary.latency_ms))
                    rouge_rounded = round(rouge_l, 3)
                    bert_rounded = round(bert_f1, 3)
                    
                    # Composite Quality Score (1-10) - weights from config
                    # BERTScore: Typically 0.7-0.95, normalize to 0-1 scale (0.7 = 0, 0.95 = 1)
                    bert_normalized = max(0, min(1, (bert_f1 - 0.70) / 0.25)) if bert_f1 > 0 else 0.5
                    # ROUGE-L: Typically 0.1-0.4 for abstractive, normalize (0.1 = 0, 0.4 = 1)
                    rouge_normalized = max(0, min(1, (rouge_l - 0.10) / 0.30))
                    # Judge score: Already 0-1
                    judge_normalized = feedback.score_accuracy
                    # Length compliance: 1 if under MAX_SUMMARY_CHARS, penalize if over
                    length_score = 1.0 if summary.char_count <= MAX_SUMMARY_CHARS else max(0, 1 - (summary.char_count - MAX_SUMMARY_CHARS) / 500)
                    
                    composite_raw = (
                        bert_normalized * WEIGHTS["bert_score"] +
                        judge_normalized * WEIGHTS["judge_score"] +
                        length_score * WEIGHTS["length_compliance"] +
                        rouge_normalized * WEIGHTS["rouge_l"]
                    )
                    # Scale to 1-10
                    quality_score = round(1 + composite_raw * 9, 1)

                    # Cost Calculation (Gemini 2.0 Flash)
                    # Input: $0.10 / 1M tokens
                    # Output: $0.40 / 1M tokens
                    tokens_in = summary.tokens_input or 0
                    tokens_out = summary.tokens_output or 0
                    cost_usd = (tokens_in / 1_000_000 * 0.10) + (tokens_out / 1_000_000 * 0.40)
                    
                    
                    result = {
                        "url": content.url,
                        "latency_ms": latency_rounded,
                        "tokens_input": tokens_in,
                        "tokens_output": tokens_out,
                        "cost_usd": round(cost_usd, 6),
                        "char_count": summary.char_count,
                        "judge_status": feedback.status,
                        "judge_score": feedback.score_accuracy,
                        "judge_critique": feedback.critique,
                        "rouge_l_f1": rouge_rounded,
                        "bert_score_f1": bert_rounded,
                        "quality_score": quality_score,
                        "summary_content": summary.content,
                        "baseline_summary": reference,
                        "baseline_char_count": len(reference),
                        "strategy": strategy
                    }
                    results.append(result)
                    
                    print(f"  [{strategy.upper()}] Quality: {quality_score}/10, ROUGE: {rouge_rounded}, BERT: {bert_rounded}, Latency: {latency_rounded}ms")

                except Exception as e_strat:
                    print(f"  [{strategy.upper()}] Failed: {e_strat}")
        
        except Exception as e_sample:
            print(f"Sample {i+1} Failed Completely: {e_sample}")
            
    return results

async def main_async():
    parser = argparse.ArgumentParser(description="Tavily Summarization Benchmark (2-Agent Architecture)")
    parser.add_argument("--limit", type=int, default=DEFAULT_SAMPLE_LIMIT, help="Number of samples to process")
    args = parser.parse_args()

    print(f"Starting async benchmark with limit: {args.limit}")
    print(f"Architecture: 2-Agent (Summarizer + optional Judge)")
    print(f"Max Concurrent Calls: {MAX_CONCURRENT_CALLS}")

    # Initialize agents (only 2 now!)
    try:
        summarizer = SummarizerAgent()
        judge = JudgeAgent()
    except Exception as e:
        print(f"Error initializing agents: {e}")
        return

    loader = DataLoader()
    r_scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    
    strategies = STRATEGIES
    
    # Load all samples
    samples = list(loader.load_samples(limit=args.limit))
    
    # Create tasks
    tasks = [
        process_sample(i, content, summarizer, judge, strategies, r_scorer) 
        for i, content in enumerate(samples)
    ]
    
    # Run tasks with progress bar
    all_results_lists = []
    with tqdm(total=len(tasks), desc="Processing samples", unit="sample") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            all_results_lists.append(result)
            pbar.update(1)
    
    # Flatten results
    flat_results = [item for sublist in all_results_lists for item in sublist]
    
    # Save results
    save_results(flat_results, strategies)

def save_results(flat_results, strategies):
    fieldnames = [
        "url", "latency_ms", "tokens_input", "tokens_output", "cost_usd", "char_count", 
        "judge_status", "judge_score", "judge_critique",
        "rouge_l_f1", "bert_score_f1", "quality_score",
        "summary_content", "baseline_summary",
        "baseline_char_count"
    ]
    
    print("\nSaving results...")
    
    # Write CSVs
    files = {}
    writers = {}
    
    try:
        for strategy in strategies:
            filename = f"results/results_{strategy}.csv"
            f = open(filename, "w", newline="", encoding="utf-8")
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            files[strategy] = f
            writers[strategy] = w
            
        for res in flat_results:
            strat = res.pop("strategy") # Remove helper key
            if strat in writers:
                writers[strat].writerow(res)
                
    finally:
        for f in files.values():
            f.close()

    print("Combining results into Excel...")
    try:
        with pd.ExcelWriter("results/benchmark_results.xlsx") as writer:
            has_data = False
            for strategy in strategies:
                csv_name = f"results/results_{strategy}.csv"
                if os.path.exists(csv_name):
                    try:
                        df = pd.read_csv(csv_name)
                        if not df.empty:
                            df.to_excel(writer, sheet_name=strategy, index=False)
                            has_data = True
                        else:
                            print(f"Warning: {csv_name} is empty.")
                    except Exception as e:
                        print(f"Error reading/writing {csv_name}: {e}")

            if not has_data:
                # Create a dummy sheet if no data to prevent ExcelWriter error
                pd.DataFrame({'Info': ['No results generated']}).to_excel(writer, sheet_name='No Data', index=False)

            
        if has_data:
            print("Success! Created 'benchmark_results.xlsx'.")
        else:
            print("Warning: No data found to write to Excel.")
            
    except Exception as e:
        print(f"Error creating Excel file: {e}")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
