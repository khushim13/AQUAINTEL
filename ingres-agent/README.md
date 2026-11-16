# INGRES-Agent: Groundwater Virtual Assistant
**Smart India Hackathon Problem SIH25066**

INGRES-Agent is an AI-powered groundwater assistant that translates citizen and official natural language queries into exact database queries against India's Groundwater Resource Estimation System (INGRES / CGWB open data) using Gemini function calling and returns verified real statistics.

---

## Monorepo Architecture

```
ingres-agent/
├── backend/            # FastAPI backend service
│   ├── app/            # Application code (Agent, Tools, DB services, Config)
│   ├── scripts/        # Data ingestion and seed scripts
│   ├── data/           # DuckDB database and raw data files
│   ├── tests/          # Pytest unit and integration test suite
│   ├── requirements.txt# Backend Python dependencies
│   └── .venv/          # Virtual environment
├── frontend/           # Next.js 14+ with Tailwind CSS & TypeScript
│   └── src/app/        # App router, Chat UI, and Benchmark views
├── eval/               # Evaluation benchmark suite (golden queries & success rate runner)
├── docs/               # System architecture and query taxonomy documentation
├── .env.example        # Environment variable template
├── .gitignore          # Repository git ignore rules
└── README.md           # Getting started guide
```

---

## Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Gemini API Key ([Google AI Studio](https://aistudio.google.com/))

### 2. Environment Setup
Copy the `.env.example` file and configure your API key:
```bash
cp .env.example backend/.env
```
Edit `backend/.env` and insert your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DB_PATH=data/ingres_db.duckdb
```

### 3. Backend Setup & Run
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The backend will be running at `http://localhost:8000`.
- Health Check: `http://localhost:8000/api/health`
- Interactive Swagger API Docs: `http://localhost:8000/docs`

### 4. Frontend Setup & Run
```bash
cd ../frontend
npm install
npm run dev
```
The frontend UI will be running at `http://localhost:3000`.

### 5. Running Tests & Benchmarks
```bash
# Backend unit tests
cd backend
PYTHONPATH=. .venv/bin/pytest tests/

# Benchmark evaluation harness
cd ../eval
# python run_eval.py
```
