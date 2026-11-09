# Fire AI — Rules vs LLMs Take-Home Assignment

An empirical and architectural investigation into **when deterministic rules are the right tool, when an LLM earns its cost, and when the answer is a combination of both**.

Built and evaluated across two real-world domains:
1. **Project A**: Indian Income-Tax Calculation Engine (Rupee-exact statutory compliance, FY 2024-25 vs FY 2025-26 Budget change).
2. **Project B**: NYC 311 Service Requests Data Quality Layer (12 corruption vectors, 36 detector configurations, and a 50M rows/day hybrid pipeline).

---

## 🚀 Quickstart & Reproduction

Reproduce every number, metric, and table reported in this repository with a **single command**:

```bash
# Run the master verification script
python run_all.py
```

Run the automated test suite across all 220 statutory test cases and 50 plain-language queries:

```bash
python -m pytest project_a/test_suite/test_tax_suite.py
```

---

## 📁 Repository Structure & Deliverables

| Deliverable | Location | Description |
| :--- | :--- | :--- |
| **Project A Code** | [`project_a/`](file:///project_a/) | Hand-coded rules, LLM-compiled rules, query-time LLM, natural language parser, and 220-case test suite. |
| **Project A Results** | [`RESULTS_A.md`](file:///RESULTS_A.md) | Comparison table (accuracy, determinism, latency, cost), Task 5 Budget 2025 change log, and final 2-page production architecture. |
| **Project B Code** | [`project_b/`](file:///project_b/) | NYC 311 2023 data profiler, 12-vector corruption injector, 36 detectors (Rules, Stats, LLM), and hybrid pipeline. |
| **Project B Results** | [`RESULTS_B.md`](file:///RESULTS_B.md) | Real 2023 NYC 311 defects found, 36-detector evaluation matrix, end-to-end hybrid performance, and 50M rows/day scale architecture. |
| **Decision Matrix** | [`DECISION_MATRIX.md`](file:///DECISION_MATRIX.md) | Exhaustive component-by-component architectural justification tied to concrete empirical measurements. |
| **AI Usage Note** | [`AI_USAGE.md`](file:///AI_USAGE.md) | Tools used, task breakdown, and two detailed retrospectives on where the AI made subtle errors and how we caught them. |
| **Master Runner** | [`run_all.py`](file:///run_all.py) | Single-command reproduction script. |

---

## 🎯 Key Takeaways & Defense Interview Highlights

### Project A: Income-Tax Engine
- **Winner**: **LLM-Compiled Deterministic Rules** (or Hand-Coded Rules).
- **Measurement**:
  - **100.0% accuracy** (220/220 test cases, 30 verified against the official Income Tax Department online calculator).
  - **0.023 ms p50 latency** (43,000 req/sec) at **$0.00 cost**, with **100% clause traceability** (Sections 16, 10(13A), 80C, 80D, 115BAC, 87A, 288A/B).
- **The Task 5 Silent Failure**:
  - When applying Finance Act 2025 amendments, the **query-time LLM suffered a catastrophic silent failure**: it missed the Section 87A marginal relief proviso between ₹12L and ₹12.70L, returning HTTP 200 with an unlawful overtaxation of **₹53,560** per taxpayer. The compiled rulebook caught this immediately during schema diff review with **zero silent failures**.

### Project B: Data-Quality Checks
- **Winner**: **Hybrid 3-Tier Pipeline** (Rules on 100% of rows $\rightarrow$ Batch Statistics $\rightarrow$ LLM Review on 0.8% of rows).
- **Measurement**:
  - Running an LLM on every row costs **$520 per million rows** ($26,000/day at 50M rows/day) and crawls at **1.5 rows/sec**.
  - Declarative rules catch 8 of 12 problems (schema, type, coordinate swap, exact duplicates, temporal inversion, zip-borough) at **140,000+ rows/sec** for **$0.00**.
  - Statistical detectors (Z-score tests and MinHash LSH) catch agency null spikes and near-duplicates at **25,000 rows/sec** for **$0.00**.
  - The LLM is restricted exclusively to ambiguous semantic contradictions (Resolution vs Status text), slashing costs by **99.2%** to **$4.16 per million rows** while maintaining **99.6% recall**.

