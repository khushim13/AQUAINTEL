# Evaluation & Benchmark Suite

This directory contains the golden evaluation dataset and test harness to measure the agent's success rate across the 6 supported query categories.

## Metric Goals
- **Tool Selection Accuracy**: Target $\ge 95\%$
- **Entity Resolution Accuracy (RapidFuzz)**: Target $\ge 95\%$
- **Numerical Value Exactness**: Target $\ge 90\%$
- **End-to-End Task Completion**: Target $\ge 90\%$

## Files
- `golden_queries.json`: Curated test queries with canonical ground-truth outputs.
- `run_eval.py`: Automated CLI benchmark runner generating precision and latency reports.
