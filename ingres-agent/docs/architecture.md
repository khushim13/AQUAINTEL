# INGRES-Agent: System Architecture & Technical Specifications
**Smart India Hackathon Problem SIH25066**
*Authoritative Conversational AI for CGWB / IIT Hyderabad INGRES Open Data*

---

## 1. High-Level Architecture Overview

INGRES-Agent is designed around a **grounded tool-calling architecture** that decouples conversational comprehension from factual data retrieval. Language models alone frequently hallucinate critical hydrological metrics; INGRES-Agent eliminates numerical hallucination by guaranteeing that every quantitative statistic returned to the user originates directly from verified CGWB assessment records in SQLite.

```mermaid
flowchart TD
    User(["User (Citizen / Hydrologist / Official)"])
    
    subgraph Frontend ["Frontend Layer (Next.js 16 + Tailwind CSS)"]
        UI["Conversational Chat UI (page.tsx)"]
        LangToggle["Bilingual Toggle (English / Hindi)"]
        Cards["Data Inspection Card (DataCard.tsx)"]
        RechartsComp["Comparison Bar Chart (ComparisonChart.tsx)"]
        RechartsTrend["Multi-Year Area Chart (TrendChart.tsx)"]
        BlockTbl["Filterable Block Table (BlockTable.tsx)"]
    end

    subgraph Backend ["Backend Gateway (FastAPI)"]
        ChatEndpoint["POST /api/chat"]
        HealthEndpoint["GET /api/health"]
        Translator["Devanagari Detector & Bidirectional Translator (translator.py)"]
    end

    subgraph AgentCore ["Agent & Decision Engine (agent.py)"]
        GeminiOrchestrator["Gemini Function Calling (gemini-2.5-flash)"]
        HeuristicFallback["Heuristic Semantic Intent Dispatcher"]
        SystemRules["Strict System Prompt Rules (1 to 7)"]
    end

    subgraph ResolutionLayer ["Entity Normalization (resolver.py)"]
        RapidFuzz["RapidFuzz WRatio Scorer"]
        PrefixScorer["Length-Penalized Prefix Scorer"]
        AliasIndex["Geographic Alias & Hindi City Mapping"]
        AmbiguityDetector["Ambiguity Detection Engine (Threshold: 70, Margin: 5)"]
    end

    subgraph ToolLayer ["Typed Data Tools (tools.py)"]
        T1["get_groundwater_level"]
        T2["get_stage_of_extraction"]
        T3["get_category"]
        T4["get_recharge"]
        T5["get_extraction"]
        T6["compare_locations"]
        T7["get_trend"]
        T8["rank_locations"]
        T9["list_blocks"]
    end

    subgraph DatabaseLayer ["Data Tier (SQLite / ingres.db)"]
        DB[(INGRES SQLite DB)]
        TblLoc["locations"]
        TblAssess["assessments"]
        TblAlias["name_aliases"]
    end

    User -->|Natural Language Query| UI
    LangToggle -.-> UI
    UI -->|JSON Request| ChatEndpoint
    ChatEndpoint --> Translator
    Translator -->|Normalized Query| AgentCore
    AgentCore --> GeminiOrchestrator
    GeminiOrchestrator -.->|Fallback if no API Key| HeuristicFallback
    AgentCore -->|Resolve Location| ResolutionLayer
    ResolutionLayer --> RapidFuzz
    RapidFuzz --> AliasIndex
    ResolutionLayer -->|Canonical Entity / Ambiguous| AgentCore
    AgentCore -->|Execute Typed Tool| ToolLayer
    ToolLayer -->|SQL Query| DB
    DB --> TblLoc & TblAssess & TblAlias
    DB -->|Exact Row Data| ToolLayer
    ToolLayer -->|Structured Payload| AgentCore
    AgentCore -->|Grounded Answer Synthesis| ChatEndpoint
    ChatEndpoint -->|Translate Response if Hindi| Translator
    Translator -->|JSON Response| UI
    UI --> Cards & RechartsComp & RechartsTrend & BlockTbl
```

---

## 2. End-to-End Query Execution Sequence

The diagram below details the sequence of events from when a citizen submits a natural query (e.g. in Hindi or English) to the rendering of interactive visualization widgets.

```mermaid
sequenceDiagram
    autonumber
    actor User as Citizen / Official
    participant UI as Next.js Chat UI
    participant API as FastAPI (/api/chat)
    participant Trans as Translator
    participant Agent as Agent Engine
    participant Res as RapidFuzz Resolver
    participant Tools as DB Tools (tools.py)
    participant DB as SQLite (ingres.db)

    User->>UI: "What is the groundwater trend in Jaipur?"
    UI->>API: POST /api/chat {message: "...", language: "en"}
    API->>Trans: detect_language(message)
    Trans-->>API: English (no translation required)
    API->>Agent: run_agent(user_message)
    
    Note over Agent: Intent & Tool Selection
    Agent->>Agent: Match intent -> get_trend
    
    Note over Agent,Res: Entity Normalization
    Agent->>Res: resolve("Jaipur")
    Res->>Res: Check exact match & RapidFuzz WRatio
    Res-->>Agent: ResolutionResult(status="resolved", canonical_name="Jaipur", entity_type="district")

    Note over Agent,DB: Tool Execution
    Agent->>Tools: get_trend(location="Jaipur", metric="stage_of_extraction")
    Tools->>DB: SELECT year, stage_of_extraction_pct FROM assessments WHERE location_id=1
    DB-->>Tools: 2021: 188.2%, 2022: 194.7%, 2023: 202.9%
    Tools->>Tools: Compute delta (+14.7%), direction="increasing"
    Tools-->>Agent: {value: [...], unit: "%", delta: 14.7, direction: "increasing"}

    Note over Agent: Grounded Answer Synthesis
    Agent->>Agent: Compose answer adhering to Rule 1 (Zero Hallucination) & Rule 4 (Citations)
    Agent-->>API: AgentOutput(answer="...", tool_called="get_trend", params={...}, data={...})
    
    API-->>UI: 200 OK {answer, tool_called, params, data}
    UI->>UI: Render Message + DataCard + TrendChart (Recharts Area Chart)
    UI-->>User: Visual grounded response with historical graph
```

---

## 3. Core Subsystems

### 3.1. Entity Resolution Pipeline ([resolver.py](file:///Users/khushimadan/GroundWater/ingres-agent/backend/app/resolver.py))

User inputs regularly contain spelling variations, colloquial terms, or Devanagari transliterations. The resolver operates a tiered matching pipeline:

1. **Query Sanitization**: Strips administrative affixes (`district`, `block`, `tehsil`, `city`) and punctuation.
2. **Alias Lookup**: Direct mapping for historical and Devanagari city names (`Poona` $\rightarrow$ `Pune`, `Banaras`/`Kashi` $\rightarrow$ `Varanasi`, `जयपुर` $\rightarrow$ `Jaipur`).
3. **Exact Database Match**: Scans state, district, and block corpora for verbatim matches.
4. **Length-Penalized RapidFuzz WRatio**: Scans eligible entities with token sort and ratio scorers. Disparities where $(|len_1 - len_2| / \max(len_1, len_2)) > 0.5$ are penalized.
5. **Short Prefix Scorer**: Inputs with length $\ge 3$ matching candidate prefixes receive a calibrated `80.0` score.
6. **Ambiguity Gate**:
   - If multiple candidates fall within the ambiguity margin ($\Delta score \le 5.0$), or if an un-aliased query of length $\le 3$ matches candidates, the status is flagged as `ambiguous`.
   - The agent interrupts tool execution (`tool_called=None`) and prompts the user with candidate options (e.g. `Nagpur` vs `Nagpur Rural`).

---

### 3.2. Strict Anti-Hallucination Guardrails ([agent.py](file:///Users/khushimadan/GroundWater/ingres-agent/backend/app/agent.py))

To ensure complete adherence to Smart India Hackathon reliability guidelines, the agent strictly enforces seven system instructions:

| Rule # | Guardrail Name | Enforcement Mechanism |
|---|---|---|
| **Rule 1** | **Zero Numerical Hallucination** | No statistical digits may appear in prose unless passed in `tool_data`. |
| **Rule 2** | **Omitted Year Defaulting** | If the user omits the assessment year, the agent defaults to `2023` and prepends: *"Defaulting to the latest available assessment year (2023)."* |
| **Rule 3** | **Refusal on Missing Data** | If the requested entity is unmonitored or missing from CGWB data, returns: *"Data not available for the requested query."* |
| **Rule 4** | **Mandatory Citations** | Every answer must explicitly list: **Value**, **Unit**, **Year**, **Location**, and **Source** (`INGRES (ingres.iith.ac.in) / CGWB Open Data`). |
| **Rule 5** | **Tool Scope Separation** | Strict boundary separating block inventory (`list_blocks`) from single-block categorization (`get_category`), and ranking (`rank_locations`) from comparison (`compare_locations`). |
| **Rule 6** | **Disambiguation Solicitation** | Ambiguous entities pause tool execution and return structured candidate options. |
| **Rule 7** | **Out-of-Scope Shield** | Non-groundwater queries (sports, coding, recipes) are politely deflected with guidance back to hydrological topics. |

---

### 3.3. Database Schema ([ingres.db](file:///Users/khushimadan/GroundWater/ingres-agent/backend/data/ingres.db))

The database schema is normalized into three relational tables in SQLite:

```mermaid
erDiagram
    LOCATIONS ||--o{ ASSESSMENTS : contains
    LOCATIONS ||--o{ NAME_ALIASES : mapped_by

    LOCATIONS {
        INTEGER id PK
        TEXT state
        TEXT district
        TEXT block "('All' for district-level summaries)"
        TIMESTAMP created_at
    }

    ASSESSMENTS {
        INTEGER id PK
        INTEGER location_id FK
        INTEGER year "Assessment year (2021, 2022, 2023)"
        REAL annual_extractable_resources_ham "Recharge in hectare-meters"
        REAL current_extraction_irrigation_ham
        REAL current_extraction_domestic_ham
        REAL current_extraction_total_ham "Total draft in ham"
        REAL stage_of_extraction_pct "SOE % (Extraction / Recharge * 100)"
        TEXT category "'Safe', 'Semi-Critical', 'Critical', 'Over-Exploited'"
        REAL pre_monsoon_water_level_mbgl "Depth to water table in mbgl"
        REAL post_monsoon_water_level_mbgl "Depth to water table in mbgl"
    }

    NAME_ALIASES {
        INTEGER id PK
        INTEGER location_id FK
        TEXT alias "Colloquial, misspelled, or Hindi name"
        TEXT alias_type "'colloquial', 'hindi', 'historical', 'misspelling'"
    }
```

---

### 3.4. Generative UI Component Architecture ([frontend](file:///Users/khushimadan/GroundWater/ingres-agent/frontend))

The Next.js 16 frontend inspects the returned `tool_called` and `data` payload to dynamically render interactive visual components under each conversational answer:

```mermaid
flowchart TD
    Payload["Backend JSON Response {tool_called, params, data}"]
    
    CheckTool{"tool_called"}
    
    Payload --> CheckTool
    Payload --> Card["DataCard.tsx (Collapsible JSON & Param Inspector)"]
    
    CheckTool -->|"compare_locations"| Comp["ComparisonChart.tsx (Recharts Responsive Bar Chart)"]
    CheckTool -->|"rank_locations"| Comp
    CheckTool -->|"get_trend"| Trend["TrendChart.tsx (Recharts Multi-Year Area Chart + Delta Badge)"]
    CheckTool -->|"list_blocks"| Table["BlockTable.tsx (Filterable Table + Category Status Badges)"]
    CheckTool -->|"Single metric (get_category, get_groundwater_level, etc.)"| TextOnly["Prose Answer with Formatted Key-Value Highlights"]
```

- **[DataCard.tsx](file:///Users/khushimadan/GroundWater/ingres-agent/frontend/src/components/DataCard.tsx)**: Provides auditability for judges and researchers by revealing the exact Python tool executed, resolved arguments, and raw database record.
- **[ComparisonChart.tsx](file:///Users/khushimadan/GroundWater/ingres-agent/frontend/src/components/ComparisonChart.tsx)**: Displays comparative bar visualisations with tooltip hover states and a toggleable data table.
- **[TrendChart.tsx](file:///Users/khushimadan/GroundWater/ingres-agent/frontend/src/components/TrendChart.tsx)**: Displays historical curves with positive/negative net change badges and year-by-year points.
- **[BlockTable.tsx](file:///Users/khushimadan/GroundWater/ingres-agent/frontend/src/components/BlockTable.tsx)**: Supports block-level exploration with search filtering and color-coded status pills (`Over-Exploited` in red, `Critical` in amber, `Safe` in green).
