# 60-Minute Defense Interview Preparation Guide

This guide is specifically designed to help you ace the **60-minute live defense interview** with the Fire AI engineering team.

---

## 1. Core Architectural Thesis (Your 60-Second Elevator Pitch)

> *"In this assignment, my guiding principle was: **Never use an LLM for deterministic math or syntax, never use a static rule for ambiguous semantics, and use compiled intermediate representations to get the speed of AI authoring with the safety of code.**
> 
> In **Project A**, a query-time LLM was 13,000× slower, cost \$300/1M queries, and suffered a critical silent failure in Budget 2025 by overtaxing citizens by ₹53,560. Compiling rules into a verified declarative schema gave 100% rupee-exact accuracy in 0.023 milliseconds at \$0 cost.
> 
> In **Project B**, running an LLM on 50M rows/day would cost \$26,000/day. Our 3-tier hybrid pipeline cascades cheap rules (140k rows/sec) and batch statistics (25k rows/sec), routing only 0.8% of ambiguous semantic rows to the LLM. This slashed costs by 99.2% while achieving 99.6% recall."*

---

## 2. Walkthrough of the Codebase

- [`run_all.py`](file:///run_all.py): Master reproduction command that runs all benchmarks and prints verified comparison tables in ~0.3s.
- [`interactive_demo.py`](file:///interactive_demo.py): Live interactive CLI to test any custom tax query or data quality record on the fly.
- [`project_a/hand_coded/calculator.py`](file:///project_a/hand_coded/calculator.py): Deterministic rules engine with exact statutory clause attribution.
- [`project_a/llm_compiled/compiler.py`](file:///project_a/llm_compiled/compiler.py): Pure Python interpreter executing declarative JSON rulebooks (`COMPILED_RULES_FY24_25` and `COMPILED_RULES_FY25_26`).
- [`project_a/parser/free_text_parser.py`](file:///project_a/parser/free_text_parser.py): Robust plain-language entity extractor that halts and clarifies on missing/ambiguous/contradictory queries.
- [`project_b/injector.py`](file:///project_b/injector.py): Controlled corruption generator for all 12 problem types (A through L).
- [`project_b/detectors/`](file:///project_b/detectors/): 36 detector implementations across Rules, Statistics, and LLMs.
- [`project_b/hybrid_pipeline.py`](file:///project_b/hybrid_pipeline.py): Production 3-tier cascade combining the winners.

---

## 3. Live Interview Curveballs & How to Modify Your Code Live

During the interview, the interviewers will intentionally change requirements on the spot to test your understanding. Here is how to handle each scenario:

### Curveball 1 (Tax): "The government just announced a new 35% slab above ₹30 Lakhs in the New Regime. Update your code now."
1. Open [`project_a/llm_compiled/compiler.py`](file:///project_a/llm_compiled/compiler.py#L90-L105) (or `COMPILED_RULES_FY25_26`).
2. Update the `slabs` array:
   ```python
   # Replace: {"low": 2400000.0, "high": None, "rate": 0.30, "label": "> 24L @ 30%"}
   # With:
   {"low": 2400000.0, "high": 3000000.0, "rate": 0.30, "label": "24L - 30L @ 30%"},
   {"low": 3000000.0, "high": None, "rate": 0.35, "label": "> 30L @ 35%"}
   ```
3. Re-run `python run_all.py` to prove the compiled interpreter instantly absorbs the change with zero code rewrites!

### Curveball 2 (Tax): "What if the user says rent is paid quarterly instead of monthly?"
1. Open [`project_a/parser/free_text_parser.py`](file:///project_a/parser/free_text_parser.py).
2. Point out that `_normalize_amount` and the rent regex identify periodicity keywords (`monthly`, `per month`, `annual`, `quarterly`).
3. Add `elif "quarterly" in raw_rent: rent_paid = amt * 4.0`.

### Curveball 3 (Data Quality): "The CFO demands zero external LLM calls due to strict privacy compliance. How does your pipeline adapt?"
1. Point to [`project_b/detectors/stat_detectors.py`](file:///project_b/detectors/stat_detectors.py#L170-L185):
   ```python
   detect_k_status_contradiction_classifier()
   ```
2. Explain that Stage 3 can fall back from the Gemini LLM to a local distilled NLI model (e.g. 6-layer DeBERTa-v3 or fine-tuned Logistic Regression with TF-IDF n-grams) running entirely in-process on CPU at 5,000 inferences/sec with zero external network calls.

### Curveball 4 (Data Quality): "A new customer has service requests for Chicago or London instead of NYC."
1. Show how `BOROUGH_ZIP_MAP` and geographic bounding boxes in [`project_b/detectors/rules_detectors.py`](file:///project_b/detectors/rules_detectors.py#L15-L25) are decoupled into configuration mappings.
2. In production, these parameters are loaded dynamically from a **Customer Schema Registry** keyed by `tenant_id`.

---

## 4. Key Metrics to Memorize for the Interview

- **Project A Accuracy**: 100.0% (220/220 cases, 30 golden benchmarks verified against official calculator).
- **Project A Latency**: **0.023 ms** (Compiled) vs **480 ms** (LLM).
- **Project A Query-Time LLM Silent Failure**: Overtaxed by **₹53,560** on ₹12.1L salary by missing 87A marginal relief proviso.
- **Project B Profiling**: 37 negative durations, 72 zip mismatches, 23 swapped coordinates, 50 PII leaks found in raw 2023 NYC 311 data.
- **Project B Hybrid Savings**: **$4.16 / 1M rows** vs **$520.00 / 1M rows** (a **99.2% cost reduction** at 4,000+ rows/sec).

