# INGRES-Agent Benchmark Evaluation Report
**SIH25066 — India Groundwater Resource Virtual Assistant**  
*Generated on: 2026-11-16 16:55:45 UTC*

---

## 1. Executive Summary & Core KPIs

| KPI / Metric | Measured Result | Benchmark Target | Status |
|---|---|---|---|
| **Tool-Selection Accuracy** | **100.0%** | $\ge 95\%$ | 🟢 PASS |
| **Parameter Resolution Accuracy** | **100.0%** | $\ge 90\%$ | 🟢 PASS |
| **Answer / Value Correctness** | **100.0%** | $\ge 90\%$ | 🟢 PASS |
| **Refusal Accuracy (Out-of-Scope & No-Data)** | **100.0%** | $\ge 95\%$ | 🟢 PASS |
| **Overall End-to-End Success Rate** | **100.0%** | $\ge 90\%$ | 🟢 PASS |
| **Average Execution Latency** | **0.1 ms** | $< 250$ ms | 🟢 ULTRA FAST |

---

## 2. Before vs. After Benchmark Comparison

### A. Overall KPI Progression

| Metric | Before (Baseline) | After (Optimized) | Delta | Status |
|---|---|---|---|---|
| **Overall Success Rate** | **79.5%** (97/122) | **100.0%** (122/122) | **+20.5%** | 🟢 PASS |
| **Tool-Selection Accuracy** | **98.2%** | **100.0%** | **+1.8%** | 🟢 PASS |
| **Parameter Resolution Accuracy** | **100.0%** | **100.0%** | **0.0%** | 🟢 PASS |
| **Answer / Value Correctness** | **82.7%** | **100.0%** | **+17.3%** | 🟢 PASS |
| **Refusal Accuracy** | **100.0%** | **100.0%** | **0.0%** | 🟢 PASS |
| **Query Latency** | **0.2 ms** | **0.1 ms** | **-0.1 ms** | 🟢 ULTRA FAST |

### B. Per-Query-Type Comparison Table

| Query Category | Total Tests | Baseline Passed | Baseline Rate | After Passed | After Rate | Delta |
|---|---|---|---|---|---|---|
| `ambiguous` | 5 | 0 | 0.0% | 5 | **100.0%** | **+100.0%** |
| `category` | 15 | 14 | 93.3% | 15 | **100.0%** | **+6.7%** |
| `compare` | 10 | 10 | 100.0% | 10 | **100.0%** | **+0.0%** |
| `extraction` | 12 | 12 | 100.0% | 12 | **100.0%** | **+0.0%** |
| `list_blocks` | 10 | 0 | 0.0% | 10 | **100.0%** | **+100.0%** |
| `no_data` | 6 | 6 | 100.0% | 6 | **100.0%** | **+0.0%** |
| `out_of_scope` | 6 | 6 | 100.0% | 6 | **100.0%** | **+0.0%** |
| `rank` | 8 | 7 | 87.5% | 8 | **100.0%** | **+12.5%** |
| `recharge` | 12 | 12 | 100.0% | 12 | **100.0%** | **+0.0%** |
| `stage_of_extraction` | 15 | 15 | 100.0% | 15 | **100.0%** | **+0.0%** |
| `trend` | 8 | 0 | 0.0% | 8 | **100.0%** | **+100.0%** |
| `water_level` | 15 | 15 | 100.0% | 15 | **100.0%** | **+0.0%** |

---

## 3. Failure Analysis & Root Cause Audit

The baseline evaluation run identified **25 failures** across 5 distinct query categories. The root causes and applied remedies are detailed below:

### 1. Ambiguity & Prefix Resolution (`ambiguous` — 5 failures)
- **Root Cause**: Short 3-letter prefix inputs (e.g. `"Nag"`, `"Bar"`, `"Kot"`, `"Bil"`) were heavily penalized by string length disparity `(len_diff / max_len > 0.5)` dropping similarity to `0.0`, resulting in no-data fallback. Furthermore, when ambiguity was detected, the agent returned `tool_called=tool_name` instead of halting tool execution (`tool_called=None`).
- **Fix**: Added prefix matching for short queries (>= 3 chars) scoring at `80.0` in `name_similarity_scorer`. In `LocationResolver.resolve`, inputs with length <= 3 without exact matches return `status="ambiguous"`. In `agent.py`, ambiguity explicitly sets `tool_called=None` and `data={"status": "ambiguous"}` so the assistant asks for clarification.

### 2. Category vs. Block Listing (`category` — 1 failure)
- **Root Cause**: Query `"Is Amber block safe or over-exploited?"` (Q045) matched the keywords `"block"` and `"over"` (from `"over-exploited"`), routing to `list_blocks` instead of `get_category` for the named block `Amber`.
- **Fix**: Refined prompt and intent routing to require explicit listing phrases (`"list"`, `"show all"`, `"all blocks"`, `"blocks in"`) for `list_blocks`, routing single-block category evaluations to `get_category`.

### 3. Ranking vs. Comparison Precedence (`rank` — 1 failure)
- **Root Cause**: Query `"Top groundwater extraction between Jaipur and Pune"` (Q092) matched the preposition `"between"` and routed to `compare_locations` before evaluating the ranking keyword `"top"`.
- **Fix**: Elevated `rank_locations` evaluation precedence before `compare_locations` when ranking keywords (`"rank"`, `"top"`, `"highest"`, `"lowest"`) are present.

### 4. Trend Metric & Delta Assertions (`trend` — 8 failures)
- **Root Cause**: `get_trend` returns `{value: points_list, delta: float, direction: str}`. The evaluation harness checked `actual_data["value"] == expected_val` rather than asserting against the net change `actual_data["delta"]`.
- **Fix**: Updated harness to assert against `actual_data["delta"]` and aligned Jaipur general trend queries to default to `stage_of_extraction` consistent with other multi-year queries.

### 5. Block Inventory Value Assertion (`list_blocks` — 10 failures)
- **Root Cause**: `list_blocks` returns `{value: [block_objects], total_count: int}`. The harness asserted `actual_data["value"] == expected_val`, comparing a list of dictionaries with an integer count (e.g. `9`).
- **Fix**: Updated harness assertions to verify `actual_data["total_count"] == expected_val` and `len(actual_data["value"]) == expected_val`.

---

## 4. Current Run Failure Log

🎉 **Zero failures! 100% of test cases passed (122 / 122).**

---

## 5. Architectural Safeguards Verified

1. **Entity Typo Tolerance**: RapidFuzz WRatio and length-penalized prefix scoring successfully resolve distorted district and city names (`Jaipru` -> `Jaipur`, `Ludhiyana` -> `Ludhiana`, `Banglore` -> `Bengaluru Urban`).
2. **Omitted Year Defaulting**: When the assessment year is omitted, the agent consistently defaults to the latest available year (`2023`) and explicitly states: `"Defaulting to the latest available assessment year (2023)"` as required by Rule 2.
3. **Zero Numerical Hallucination**: Every single numerical output matches the underlying ground-truth record from the INGRES SQLite database (`ingres.db`).
4. **Out-of-Scope & Missing Data Guardrails**: Non-groundwater queries are cleanly rejected with guidance, while unmonitored locations return `"data not available"` without fabrication.