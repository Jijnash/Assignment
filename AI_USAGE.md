# AI Usage Note & Post-Incident Reflection

This document details the AI tools used during the development of this assignment, their respective workflows, and an honest retrospective on places where the AI generated incorrect logic and how it was caught and remediated.

---

## 1. AI Tools & Models Used

| Tool / Model | Primary Purpose & Scope |
| :--- | :--- |
| **Google Antigravity AI Agent** | Autonomous architecture scaffolding, code generation, refactoring, and test automation runner. |
| **Google Gemini 2.5 Flash** (`google-genai` SDK) | Query-time tax calculations, few-shot NLI contradiction detection in Project B, and plain-language linguistic extraction. |
| **Python Tooling** | `pydantic` v2 (type validation), `pytest` (automated testing), `scikit-learn` & `pandas` (statistical baselines). |

---

## 2. Breakdown of AI-Assisted Tasks

1. **Project A (Statutory Tax Engine)**:
   - Used AI to compile the statutory text of the Income Tax Act (Finance Act 2024 and Finance Act 2025) into structured JSON rulebooks (`COMPILED_RULES_FY24_25` and `COMPILED_RULES_FY25_26`).
   - Generated a 220-case test grid spanning micro-incomes, senior citizens, HRA limits, and surcharge thresholds.
   - Synthesized a 50-description natural language corpus including Indian colloquialisms, Hinglish, incomplete queries, and contradictory constraints.

2. **Project B (Data Quality Layer)**:
   - Profiled 6,000 NYC 311 2023 service requests to uncover historical quality defects.
   - Built the 12-vector corruption injector and implemented the 36 detector variants across Rules, Statistics, and LLMs.
   - Benchmarked end-to-end latency, false-alarm rates, and cost per million rows.

---

## 3. Case Studies: Where the AI was Wrong & How We Caught It

### Case Study 1: The "Package" Regex Substring Bug
* **The Error**: When generating the plain-language parser for tax queries, the AI wrote an age extraction regex as:
  ```python
  age_match = re.search(r"(?:age|umar|saal)\s*(?:is|of|hai)?\s*[:\s-]*([0-9]{1,3})\b", text_lower)
  ```
* **The Symptom**: When evaluating query PL_06:
  > *"Annual package is 10 LPA. Basic salary is 5 LPA. Rent paid in Delhi is Rs. 20,000 monthly..."*
  The parser halted with an unexpected clarification request:
  `"Please confirm your age (received 10). Salaried tax rules apply to legal working age (18-110)."`
* **Root Cause**: The English word `"package"` ends with the substring `"age"`. Because the AI had omitted leading word boundaries (`\b`), `"package is 10"` matched `"age is 10"`, incorrectly inferring the taxpayer was a 10-year-old child earning a 10 LPA salary.
* **How We Caught It**: Running our automated test suite (`python -m pytest project_a/test_suite/test_tax_suite.py`) failed assertion `test_plain_language_parser` with an explicit diff.
* **The Fix**: Replaced the greedy match with strict word boundary tokenization:
  ```python
  age_match = re.search(r"\b(?:age|umar|saal|years\s*old)\b\s*(?:is|of|hai)?\s*[:\s-]*([0-9]{1,3})\b", text_lower)
  ```
  Added regression test cases covering words with `"age"` roots (*package*, *mortgage*, *manage*, *advantage*).

---

### Case Study 2: The Section 87A Marginal Relief Formula Confusion
* **The Error**: During initial drafting of the New Tax Regime calculator, the AI attempted to calculate Section 87A marginal relief using the traditional **surcharge marginal relief** template:
  $$\text{Max Tax} = \text{BaseTax}(\text{Threshold}) + (\text{TaxableIncome} - \text{Threshold})$$
  At the ₹7,00,000 threshold (where slab tax is ₹20,000), this formula produced a cap of:
  $$\text{Max Tax} = ₹20,000 + (\text{Income} - ₹7,00,000)$$
* **The Symptom**: For a salary with net taxable income of ₹7,00,010 (just ₹10 above the ₹7L rebate threshold), the AI formula calculated tax payable as:
  $$\text{Tax} = ₹20,000 + ₹10 = ₹20,010$$
  This completely destroyed the benefit of the Section 87A rebate for anyone earning even ₹1 above ₹7 Lakhs!
* **How We Caught It**: We audited our calculations against the **official Income Tax Department portal calculator** using our 30 Golden Reference cases. The official calculator returned:
  - Taxable Income: ₹7,00,010 $\rightarrow$ **Tax Payable: ₹10** (plus ₹0.40 cess rounded to **₹10**).
* **The Correction**: Under the statutory proviso to Section 87A for Section 115BAC, the tax payable after rebate cannot exceed the excess of income over ₹7,00,000:
  $$\text{Tax Payable} = \min(\text{BaseTax}, \text{TaxableIncome} - ₹7,00,000)$$
  We updated the implementation to explicitly compute `marginal_relief_87a = base_tax - (net_taxable_income - rebate_threshold)`, guaranteeing rupee-exact alignment with the official government tax portal.

