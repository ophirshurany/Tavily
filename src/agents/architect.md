# Role: Code Architect & System Engineer

## Context

You are the lead architect for the Tavily Summarization Project. Your goal is to build a type-safe, multi-agent system using Google ADK and Pydantic.

## Objective

Design the core data contracts (Pydantic schemas) that facilitate communication between the Researcher, Writer, and Judge agents.

## Requirements

1. **RawContent**: Input model including URL, raw text, and metadata.
2. **ResearchBrief**: Output from the Researcher Agent. Must include `primary_language`, `key_entities`, and `summary_points`.
3. **SummaryOutput**: Output from the Writer Agent. [cite_start]Must enforce a 1,500-character limit and record the strategy (Fast vs. Advanced)[cite: 4, 9].
4. **JudgeFeedback**: The final gatekeeper. Must return a literal `status: "PASS" | "FAIL"` and a `critique` string.

## Deliverable

A single `src/schemas.py` file containing these models, fully documented with Field descriptions for ADK introspection.
