# INGRES-Agent Architecture

## Overview
INGRES-Agent is an AI-powered conversational virtual assistant designed for Smart India Hackathon problem **SIH25066**. It allows citizens, researchers, and government officials to query India's groundwater database (INGRES - India-Groundwater Resource Estimation System, IIT Hyderabad / CGWB open data) in natural language.

## System Components

1. **Frontend (Next.js + Tailwind CSS)**:
   - Citizen View: Conversational interface, quick-select prompt chips, intuitive classification badges (Safe 🟢, Semi-critical 🟡, Critical 🟠, Over-exploited 🔴).
   - Official View: Direct query inspect, tool trace view, metric tables, and live evaluation benchmark dashboard.

2. **Backend (FastAPI + Python)**:
   - **Gemini Function Calling Engine**: Uses Gemini 2.5 Flash with structured function schemas.
   - **Entity Resolution (RapidFuzz)**: Matches district, block, and state names against canonical lists, tolerating misspellings and common regional aliases (e.g., "Bangalore" -> "Bengaluru Urban").
   - **Data Store (DuckDB / SQLite)**: In-process column-oriented analytical database storing historical CGWB assessment data (2020-2024).

3. **Evaluation Harness (`eval/`)**:
   - Automated benchmark with 50+ golden test queries across 6 query categories measuring tool selection accuracy, entity resolution accuracy, and exact answer verification.
