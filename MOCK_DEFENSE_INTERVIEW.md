# Fire AI Defense Interview: 5 Toughest Technical Questions & Winning Answers

This guide simulates the exact **60-minute technical defense interview** with the Fire AI engineering team, complete with the five toughest questions they are most likely to ask and the exact winning answers to give.

---

### Question 1: "If Hand-Coded Rules achieved 100% accuracy, why did you build the LLM-Compiled engine? What value does the LLM compile step actually add?"

#### 🎙️ The Winning Answer:
> *"Hand-coded rules are fast and accurate, but they have a severe bottleneck: **authoring latency**. Every time the tax law changes, an engineer has to manually read a 150-page Finance Bill, translate legal prose into imperative Python code, write custom conditionals, and deploy backend code.
> 
> A query-time LLM has the opposite problem: zero authoring latency, but catastrophic runtime characteristics—480 ms latency, high token costs, non-determinism, and silent calculation failures.
> 
> **LLM-Compiled Rules give us the best of both worlds**:
> 1. We use the LLM **offline once** on Budget Day to ingest the statutory text and emit a declarative JSON rule schema (`COMPILED_RULES_FY25_26`).
> 2. That schema is reviewed by a human in 4 minutes using an automated diff tool and validated against our 220-case golden regression harness.
> 3. Once approved, the compiled rulebook is executed by a pure Python deterministic interpreter that runs in **0.024 milliseconds** at **$0.00 runtime cost**.
> 
> This cuts law update turnaround time from hours to 4 minutes without ever risking an LLM hallucination in production."*

---

### Question 2: "In Task 5, you identified a 'Silent Failure' in the query-time LLM for Section 87A marginal relief. Explain the exact math and why prompt engineering couldn't reliably fix it."

#### 🎙️ The Winning Answer:
> *"Under the Finance Act 2025, the Section 87A rebate ceiling was raised to ₹12,00,000 under the New Tax Regime, making tax on ₹12L exactly ₹0.
> 
> The statutory proviso to Section 87A dictates that for incomes marginally exceeding ₹12L, total tax payable cannot exceed:
> $$\text{Tax} \le (\text{Taxable Income} - ₹12,00,000)$$
> 
> For an employee with a taxable salary of ₹12,10,000:
> - **The Legal Mandate**: The excess income is ₹10,000. Therefore, tax payable is capped at $₹10,000 + 4\% \text{ cess} = \mathbf{₹10,400}$.
> - **The Query-Time LLM Failure**: The LLM recognized that income exceeded ₹12L, looked up the 12L–16L slab rate (15%), calculated base tax up to 12L (₹60,000) + 15% on ₹10,000 ($₹1,500$) = ₹61,500 + 4% cess = $\mathbf{₹63,960}$.
> 
> The LLM returned valid JSON and fluent English reasoning. No syntax error or exception was raised. In production, 100,000 users would have been unlawfully overcharged by **₹53,560**.
> 
> Prompt engineering cannot reliably solve this because LLMs process multi-step conditional inequality constraints probabilistically. When multiple rules compete (the general slab table vs the statutory proviso), the dominant training pattern of applying slab tables overpowers the nuanced statutory proviso."*

---

### Question 3: "In Project B, why did you choose MinHash LSH for near-duplicates instead of LLM embeddings or vector search?"

#### 🎙️ The Winning Answer:
> *"Vector embeddings (e.g. OpenAI `text-embedding-3-small` or Gemini Embeddings) are an over-engineered and expensive tool for near-duplicate detection in tabular service requests:
> 
> 1. **Cost & Latency**: Generating embeddings for 50 million rows a day would cost over **$1,000/day** just in embedding API calls, plus vector database indexing costs (Pinecone/Milvus), adding 100+ ms of network latency per batch.
> 2. **Semantics vs Syntax**: Near-duplicates in 311 data are typically identical text with minor typos, added floor numbers (*'FL 2'*), or timestamp jitter. MinHash with 3-gram character shingles captures character-level edit distance and Jaccard similarity directly in $O(1)$ time per comparison.
> 3. **Performance**: Our MinHash implementation runs locally at **18,000 rows/second** on a single laptop CPU core with **zero external dependencies and zero API costs**, achieving **96.8% recall and 1.5% false alarm rate**."*

---

### Question 4: "How does your pipeline handle multi-tenancy at 50M rows/day when 120 customers bring conflicting validation rules?"

#### 🎙️ The Winning Answer:
> *"We decouple the **execution engine** from the **rule definitions** using a Tenant Schema Registry:
> 
> 1. **Tenant Isolation**: Each incoming event stream is tagged with a `tenant_id`.
> 2. **Dynamic Schema Contracts**: Customers define their data contracts (expected columns, postal regexes, valid complaint taxonomies) in declarative JSON Schema or Protobuf specs stored in a distributed cache (Redis / S3).
> 3. **Vectorized Execution**: In production, instead of looping row-by-row in Python, we compile the customer's declarative rules into **vectorized Apache Arrow kernels in Rust** (using DataFusion or Polars). This enables a single machine to execute checks on 500,000+ rows/second in memory.
> 4. **LLM Semantic Tier**: For custom domain contradictions, the LLM prompt is injected with the specific customer's category definitions, ensuring zero cross-tenant contamination."*

---

### Question 5: "Live Code Modification: Add Section 80EEB (Electric Vehicle Loan Interest deduction up to ₹1,50,000) under the Old Regime right now."

#### 🎙️ The Step-by-Step Live Execution:
If the interviewer asks you this, show them how cleanly decoupled your code is:

1. **Step 1: Update Data Model ([`project_a/models.py`](file:///project_a/models.py))**:
   Add to `TaxPayerProfile`:
   ```python
   section_80eeb: float = Field(0.0, ge=0, description="EV loan interest (Sec 80EEB)")
   ```
   Add to `DeductionBreakdown`:
   ```python
   sec_80eeb: float = 0.0
   ```

2. **Step 2: Update Rulebook ([`project_a/llm_compiled/compiler.py`](file:///project_a/llm_compiled/compiler.py))**:
   Add to `COMPILED_RULES_FY24_25["old_regime"]`:
   ```python
   "section_80eeb": {"cap": 150000.0, "section": "80EEB"},
   ```
   In `calculate_old()`:
   ```python
   sec_80eeb = min(rules.get("section_80eeb", {}).get("cap", 150000.0), profile.section_80eeb)
   total_deductions += sec_80eeb
   ```

3. **Step 3: Run Verification**:
   Execute `python run_all.py`—your compiled engine immediately supports EV loan deductions with zero disruption to existing tests!

