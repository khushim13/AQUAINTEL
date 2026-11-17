# INGRES-Agent: 5-Minute Judge Demonstration Script
**Smart India Hackathon Problem SIH25066**
*Authoritative Conversational AI for CGWB / IIT Hyderabad INGRES Open Data*

---

## Presentation Checklist & Timing Breakdown

| Section | Target Duration | Focus Area |
|---|---|---|
| **Part 1: The Problem & The Solution** | 00:00 – 01:00 (60s) | The CGWB data access bottleneck & LLM hallucination risk |
| **Part 2: Architecture & Anti-Hallucination** | 01:00 – 02:00 (60s) | Function-calling pipeline, RapidFuzz normalization, strict rules |
| **Part 3: Live Interactive Demonstration** | 02:00 – 03:30 (90s) | Query flow, Data Card, Bar Charts, Trend Charts, Block Tables |
| **Part 4: Bilingual Hindi Support** | 03:30 – 04:15 (45s) | Devanagari translation with numerical & entity preservation |
| **Part 5: Benchmark KPIs & Closing** | 04:15 – 05:00 (45s) | 122-question benchmark, 100% accuracy, deployment readiness |

---

## 🎙️ Verbatim Demo Walkthrough

### Part 1: The Problem & The Solution (00:00 – 01:00)

> **Speaker:**
> *"Respected judges, India is the largest groundwater extractor in the world, pumping over 250 billion cubic meters annually—more than the United States and China combined.*
> 
> *The Central Ground Water Board (CGWB) and IIT Hyderabad maintain a massive, authoritative open-data portal called INGRES. But for the average farmer in Punjab, a district magistrate in Rajasthan, or an urban planner in Maharashtra, this data is trapped behind complex nested tables, technical jargon, and multi-step PDF reports.*
> 
> *If you ask ChatGPT or generic AI chatbots about local groundwater statistics, they hallucinate numbers, cite outdated years, or conflate extraction percentages with total water table depth.*
> 
> *Today, we present **INGRES-Agent**—an authoritative, zero-hallucination conversational AI that empowers anyone to query India's groundwater database in natural English and Hindi, backed by typed database functions over verified CGWB records."*

---

### Part 2: Architecture & Anti-Hallucination Pipeline (01:00 – 02:00)

*(Point to the architectural diagram on screen or in [ARCHITECTURE.md](file:///Users/khushimadan/GroundWater/ingres-agent/docs/ARCHITECTURE.md))*

> **Speaker:**
> *"To solve the hallucination challenge, we designed a **grounded tool-calling architecture** with five decoupled stages:*
> 
> 1. ***Intent Parsing**: Uses Gemini 2.5 Flash function calling (with an instant heuristic fallback engine).*
> 2. ***RapidFuzz Entity Resolution**: Geographic names are normalized using token-sort and length-penalized prefix scoring. It seamlessly handles typos like 'Ludhiyana' and colloquial aliases like 'Poona' or 'Banaras'.*
> 3. ***Typed Pure Python Tools**: 9 typed functions execute exact SQL queries against the local SQLite database (`ingres.db`).*
> 4. ***Grounded Synthesis**: Adheres to strict system rules: zero statistical hallucination, mandatory defaulting to the latest year (2023) if omitted, and standard CGWB citations.*
> 5. ***Generative UI**: Responses dynamically render interactive Recharts visualizations and audit inspection cards.*

---

### Part 3: Live Interactive Demonstration (02:00 – 03:30)

*(Switch browser window to `http://localhost:3000`)*

#### Demo Step 1: Default Year Handling & The Audit Data Card
> **Action:** Type into chat:
> `What is the groundwater level in Jaipur?`
> 
> **Speaker:**
> *"Notice two critical details in the response:*
> *First, the user didn't specify a year. Per **Rule 2**, the agent defaults to the latest assessment year (2023) and explicitly tells the user: 'Defaulting to the latest available assessment year (2023)'.*
> *Second, look at this collapsible **Data Card** under the message. If we open it, judges and auditors can verify the exact Python tool executed (`get_groundwater_level`), the normalized parameters, and the raw database row showing 35.4 mbgl. Every number is 100% verifiable."*

---

#### Demo Step 2: Typo Tolerance & Disambiguation
> **Action:** Type into chat:
> `Stage of extraction in Ludhiyana` *(deliberate misspelling of Ludhiana)*
> 
> **Speaker:**
> *"Here, the user misspelled Ludhiana as 'Ludhiyana'. Our RapidFuzz WRatio resolver matches it with 90%+ confidence to canonical Ludhiana, Punjab, returning the real stage of extraction: 203.6% (Over-Exploited).*
> 
> *Now, what if the input is ambiguous? Let's type:*
> `Water level in Nag`
> 
> *Notice that instead of guessing, the agent stops tool execution and prompts the user: 'The location Nag is ambiguous. Did you mean Nagpur (district) or Nagpur Rural (block)?' This prevents catastrophic administrative misdirection."*

---

#### Demo Step 3: Comparative Analysis & Interactive Bar Chart
> **Action:** Type into chat or click chip:
> `Compare groundwater level between Jaipur and Pune in 2023`
> 
> **Speaker:**
> *"For multi-location queries, the agent routes to `compare_locations`. The UI immediately renders a responsive **Recharts Bar Chart**. We can hover over bars to inspect values—35.4 mbgl in Jaipur versus 9.8 mbgl in Pune—or toggle to a structured summary table."*

---

#### Demo Step 4: Multi-Year Historical Trend & Area Chart
> **Action:** Type into chat or click chip:
> `What is the historical trend of groundwater in Jaipur?`
> 
> **Speaker:**
> *"Policymakers need to know whether aquifers are recovering or depleting. Here, the agent retrieves multi-year records across 2021, 2022, and 2023, rendering a historical **Area Chart** with an automatic trend badge: `Increasing (+14.70% Net Change)`."*

---

#### Demo Step 5: Granular Administrative Block Inventory
> **Action:** Type into chat:
> `List all over-exploited blocks in Jaipur`
> 
> **Speaker:**
> *"Drilling down to grassroots governance, the agent lists all 9 blocks in Jaipur—Amber, Bassi, Chaksu, Jhotwara—rendered in an interactive **Block Table** complete with color-coded status badges and pre/post monsoon water levels."*

---

### Part 4: Multilingual Support (Hindi) (03:30 – 04:15)

> **Action:** Click the language toggle button in the top-right header to switch from **English** to **हिन्दी**.
> 
> **Action:** Type into chat or click chip:
> `पुणे में भूजल स्तर क्या है?`
> 
> **Speaker:**
> *"A primary barrier for Indian farmers is English-only interfaces. We built an automated Devanagari translation layer. The agent detects Hindi input, translates the query intent to English for tool execution, and synthesizes the response in fluent Hindi—while strictly preserving numbers, units, and place names: 'पुणे में 2023 के लिए भूजल स्तर 9.8 mbgl था' with complete INGRES citations."*

---

### Part 5: Benchmark KPIs & Closing (04:15 – 05:00)

*(Switch to screen showing [eval/report.md](file:///Users/khushimadan/GroundWater/ingres-agent/eval/report.md))*

> **Speaker:**
> *"Finally, we didn't just build a prototype—we built an enterprise-grade evaluation benchmark. In our test suite of **122 diverse questions** across all 12 query types:*
> 
> - ***Tool-Selection Accuracy**: **100.0%***
> - ***Parameter Accuracy**: **100.0%***
> - ***Value / Answer Correctness**: **100.0%***
> - ***Refusal Accuracy (Out-of-Scope & Fake Entities)**: **100.0%***
> - ***Average Execution Latency**: **0.1 milliseconds***
> 
> *The entire application is containerized with Docker and Docker Compose, ready for immediate deployment on government cloud infrastructure, state water portal embeds, or WhatsApp bot integrations.*
> 
> *INGRES-Agent turns India's national groundwater data into an accessible, reliable, and conversational reality for every Indian citizen. Thank you, and we welcome your questions!"*
