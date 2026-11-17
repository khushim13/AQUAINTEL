# INGRES-Agent: India Groundwater Resource Virtual Assistant
**Smart India Hackathon Problem SIH25066**
*Authoritative Conversational AI for CGWB / IIT Hyderabad INGRES Open Data*

---

## 1. Project Overview

**INGRES-Agent** is an intelligent, bilingual conversational assistant built for the **Smart India Hackathon (SIH25066)**. It democratizes access to India's national groundwater assessment database published by the **Central Ground Water Board (CGWB)** and **IIT Hyderabad** at [ingres.iith.ac.in](https://ingres.iith.ac.in).

Farmers, researchers, hydrologists, and government policymakers can query complex aquifer statistics in natural English or Hindi. The agent parses the intent, resolves geographic entities despite misspellings and colloquial names via RapidFuzz, executes typed database functions directly over SQLite, and generates strictly grounded answers with verifiable numerical citations, interactive Recharts visualizations, and transparent data inspection cards.

---

## 2. Key Capabilities & Innovations

- **Zero Numerical Hallucination**: Strict system prompt constraints ensure no quantitative statistics are uttered without being returned directly by a database tool.
- **Default Latest Year Policy**: Automatically defaults omitted years to the latest assessment (`2023`) and explicitly discloses the default to the user.
- **Robust Fuzzy Geographic Disambiguation**: Uses RapidFuzz WRatio and length-penalized prefix scoring to match typos (e.g., `Ludhiyana` -> `Ludhiana`, `Jaipru` -> `Jaipur`), aliases (`Banaras` -> `Varanasi`, `Poona` -> `Pune`), and detects ambiguous prefixes (`Nag`, `Bar`, `Kot`) to ask for user clarification.
- **Bilingual Support (English & Hindi)**: Detects Devanagari script, translates intent to English for tool execution, and synthesizes answers back in Hindi while strictly preserving place names, numbers, and hydrological units.
- **Rich Generative UI & Visualizations**:
  - **Data Card**: Collapsible inspector displaying tool called, execution parameters, and raw JSON payload.
  - **Comparison Bar Charts**: Multi-location side-by-side metric comparison via Recharts.
  - **Multi-Year Trend Area Charts**: Historical trajectories with net change delta and direction indicator.
  - **Filterable Block Tables**: Dynamic table with category status badges (`Safe`, `Semi-Critical`, `Critical`, `Over-Exploited`).
- **Comprehensive Benchmark Evaluation**: Includes 122 automated test questions with an end-to-end **100% pass rate** across all 12 query types at **0.1 ms** latency.

---

## 3. Repository Structure

```
ingres-agent/
├── backend/                  # FastAPI Application Service
│   ├── app/
│   │   ├── main.py           # FastAPI entrypoint, CORS, route handlers (/api/chat, /api/health)
│   │   ├── agent.py          # Gemini function calling agent + heuristic intent dispatcher
│   │   ├── tools.py          # 9 typed database query tools over SQLite
│   │   ├── resolver.py       # RapidFuzz entity resolver & geographic alias index
│   │   ├── translator.py     # Devanagari detector & bidirectional Hindi translation
│   │   ├── config.py         # App settings & environment variable loaders
│   │   └── models/
│   │       └── schemas.py    # Pydantic schemas for chat requests, responses, and tools
│   ├── data/
│   │   ├── ingres.db         # Seeded SQLite database (locations, assessments, aliases)
│   │   └── raw/              # Raw CSV source records from CGWB assessments
│   ├── scripts/
│   │   └── ingest.py         # CSV ingestion pipeline into SQLite
│   ├── tests/                # 40 Pytest unit & integration tests
│   ├── requirements.txt      # Python dependencies
│   └── Dockerfile            # Backend container configuration
├── frontend/                 # Next.js 16 (App Router) + Tailwind CSS + Recharts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx    # Root layout with responsive viewport & fonts
│   │   │   └── page.tsx      # Interactive chat UI with chips, input, and message history
│   │   ├── components/
│   │   │   ├── DataCard.tsx  # Collapsible inspection card
│   │   │   ├── ComparisonChart.tsx # Recharts bar chart & toggleable data table
│   │   │   ├── TrendChart.tsx      # Recharts historical area chart with net delta
│   │   │   └── BlockTable.tsx      # Block status table with category badges
│   │   └── lib/
│   │       └── translations.ts     # UI strings & example prompt chips (EN / HI)
│   ├── package.json          # Node dependencies
│   └── Dockerfile            # Frontend container configuration
├── eval/                     # Automated Evaluation Suite
│   ├── generate_questions.py # Synthesizes 122 ground-truth questions from DB
│   ├── test_questions.json   # 122 benchmark test questions across 12 query types
│   ├── run_eval.py           # Evaluation runner computing accuracy KPIs
│   └── report.md             # Benchmark evaluation report (100% pass rate)
├── docs/                     # Detailed Documentation
│   ├── README.md             # This comprehensive guide
│   ├── ARCHITECTURE.md       # Technical architecture with Mermaid diagrams
│   ├── QUERY_TYPES.md        # Query taxonomy, examples, and success rates
│   └── DEMO_SCRIPT.md        # 5-minute judge pitch & demonstration walkthrough
├── docker-compose.yml        # Multi-container orchestration (backend + frontend)
└── README.md                 # Root quickstart pointer
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- (Optional) Gemini API Key from [Google AI Studio](https://aistudio.google.com/)

### Method 1: Local Development

#### 1. Backend Setup
```bash
cd ingres-agent/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the FastAPI server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The backend will be available at `http://127.0.0.1:8000`.
- Health endpoint: `http://127.0.0.1:8000/api/health`
- Swagger OpenAPI documentation: `http://127.0.0.1:8000/docs`

#### 2. Frontend Setup
```bash
cd ../frontend
npm install
npm run dev
```
The frontend UI will be available at `http://127.0.0.1:3000`.

---

### Method 2: Docker Compose (One-Click)

To spin up both services in isolated containers:
```bash
cd ingres-agent
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## 5. Running Tests & Benchmarks

### Backend Unit Tests
Execute the 40 unit and integration tests covering tools, entity resolution, Hindi translation, and agent responses:
```bash
cd ingres-agent
PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/ -v
```

### Evaluation Benchmark Suite
Run the 122-question automated benchmark evaluation:
```bash
cd ingres-agent
PYTHONPATH=backend backend/.venv/bin/python eval/run_eval.py
```
This evaluates tool-selection accuracy, parameter accuracy, value correctness, and refusal accuracy, generating [eval/report.md](file:///Users/khushimadan/GroundWater/ingres-agent/eval/report.md).

---

## 6. Documentation Index

- [ARCHITECTURE.md](file:///Users/khushimadan/GroundWater/ingres-agent/docs/ARCHITECTURE.md): Component diagrams, sequence diagrams, database schemas, and guardrail rules.
- [QUERY_TYPES.md](file:///Users/khushimadan/GroundWater/ingres-agent/docs/QUERY_TYPES.md): Complete taxonomy of 12 query types, parameter extraction, and benchmark results.
- [DEMO_SCRIPT.md](file:///Users/khushimadan/GroundWater/ingres-agent/docs/DEMO_SCRIPT.md): 5-minute scripted presentation for Smart India Hackathon evaluators.
