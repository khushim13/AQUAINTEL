# INGRES-Agent: Supported Query Types & Benchmark Accuracy
**Smart India Hackathon Problem SIH25066**
*Authoritative Conversational AI for CGWB / IIT Hyderabad INGRES Open Data*

---

## 1. Overview & Benchmark Summary

INGRES-Agent supports **12 distinct query categories** spanning descriptive groundwater statistics, comparative analyses, historical trends, administrative block inventories, and strict refusal guardrails.

All 12 categories have been rigorously validated against the ground-truth SQLite database using the automated evaluation harness ([eval/run_eval.py](file:///Users/khushimadan/GroundWater/ingres-agent/eval/run_eval.py)) across 122 questions.

| Category | Description | Primary Tool | Eval Tests | Pass Rate |
|---|---|---|---|---|
| `water_level` | Depth to groundwater table (mbgl) | `get_groundwater_level` | 15 / 15 | **100.0%** |
| `stage_of_extraction` | Groundwater extraction percentage (SOE %) | `get_stage_of_extraction` | 15 / 15 | **100.0%** |
| `category` | Assessment category (Safe, Semi-Critical, Critical, Over-Exploited) | `get_category` | 15 / 15 | **100.0%** |
| `recharge` | Annual Extractable Groundwater Resource (ham) | `get_recharge` | 12 / 12 | **100.0%** |
| `extraction` | Volumetric draft / water pumped (ham) | `get_extraction` | 12 / 12 | **100.0%** |
| `compare` | Cross-location side-by-side metric comparison | `compare_locations` | 10 / 10 | **100.0%** |
| `rank` | Top, highest, or lowest locations by metric | `rank_locations` | 8 / 8 | **100.0%** |
| `trend` | Historical multi-year trajectory & net delta | `get_trend` | 8 / 8 | **100.0%** |
| `list_blocks` | Assessment block inventory & category filtering | `list_blocks` | 10 / 10 | **100.0%** |
| `ambiguous` | Partial or ambiguous entity disambiguation | Clarification Solicited | 5 / 5 | **100.0%** |
| `no_data` | Graceful refusal for unmonitored / fictional locations | Refusal Handler | 6 / 6 | **100.0%** |
| `out_of_scope` | Deflection of non-groundwater inquiries | Shield Handler | 6 / 6 | **100.0%** |
| **Total** | | | **122 / 122** | **100.0%** |

---

## 2. Detailed Query Taxonomy

---

### 1. `water_level` (Groundwater Table Depth)
- **Description**: Depth to the water table in meters below ground level (`mbgl`) for pre-monsoon or post-monsoon seasons.
- **Tool**: `get_groundwater_level(location, year, season)`
- **Success Rate**: **100.0%** (15/15 passed)
- **Unit**: `mbgl` (meters below ground level)
- **Example Queries**:
  - *"What is the groundwater level in Jaipur in 2023?"*
  - *"Pre-monsoon water table in Varanasi in 2023"*
  - *"Depth to water in Pune post-monsoon"*
  - *"पुणे में भूजल स्तर क्या है?"*
- **Response Shape**: Formatted statement citing depth, season, year, canonical location, and official INGRES source.

---

### 2. `stage_of_extraction` (Extraction Ratio %)
- **Description**: Ratio of annual groundwater extraction to annual extractable recharge, expressed as a percentage (`SOE %`).
- **Tool**: `get_stage_of_extraction(location, year)`
- **Success Rate**: **100.0%** (15/15 passed)
- **Unit**: `%`
- **Example Queries**:
  - *"What is the stage of extraction in Ludhiana in 2023?"*
  - *"Groundwater extraction percentage in Bengaluru Urban"*
  - *"SOE percentage in Amritsar"*
  - *"लुधियाना में भूजल दोहन का प्रतिशत क्या है?"*
- **Response Shape**: Numeric percentage with category context and official citation.

---

### 3. `category` (Aquifer Assessment Classification)
- **Description**: CGWB categorization based on stage of extraction and long-term water level decline: `Safe` ($\le 70\%$), `Semi-Critical` ($70-90\%$), `Critical` ($90-100\%$), or `Over-Exploited` ($>100\%$).
- **Tool**: `get_category(location, year)`
- **Success Rate**: **100.0%** (15/15 passed)
- **Unit**: `category`
- **Example Queries**:
  - *"What is the groundwater category of Jaipur in 2023?"*
  - *"Is Amber block safe or over-exploited?"*
  - *"Category of Coimbatore"*
  - *"जयपुर किस भूजल श्रेणी में आता है?"*
- **Response Shape**: Status badge string (`Safe`, `Semi-Critical`, `Critical`, `Over-Exploited`) with standard source citation.

---

### 4. `recharge` (Annual Extractable Resource)
- **Description**: Total dynamic groundwater recharge available for annual development, measured in hectare-meters (`ham`).
- **Tool**: `get_recharge(location, year)`
- **Success Rate**: **100.0%** (12/12 passed)
- **Unit**: `ham` (hectare-meters; $1\text{ ham} = 10,000\text{ m}^3$)
- **Example Queries**:
  - *"What is the annual groundwater recharge in Jodhpur in 2023?"*
  - *"Total extractable groundwater resource in Pune"*
  - *"Recharge in Varanasi in 2022"*
  - *"जोधपुर में वार्षिक भूजल पुनर्भरण कितना है?"*
- **Response Shape**: Volumetric integer/float formatted with thousands separators and unit `ham`.

---

### 5. `extraction` (Annual Water Draft / Usage)
- **Description**: Total volumetric groundwater pumped annually, broken down by irrigation, domestic, or industrial usage.
- **Tool**: `get_extraction(location, year, usage)`
- **Success Rate**: **100.0%** (12/12 passed)
- **Unit**: `ham`
- **Example Queries**:
  - *"How much groundwater was extracted in Jaipur in 2023?"*
  - *"Irrigation water draft in Ludhiana"*
  - *"Domestic groundwater usage in Pune in 2023"*
  - *"जयपुर में कुल भूजल निकासी कितनी हुई?"*
- **Response Shape**: Volumetric figure citing the specified usage type (`total`, `irrigation`, `domestic`).

---

### 6. `compare` (Multi-Location Side-by-Side Comparison)
- **Description**: Comparative analysis between two or more districts or blocks for any metric.
- **Tool**: `compare_locations(locations, metric, year)`
- **Success Rate**: **100.0%** (10/10 passed)
- **UI Widget**: **Recharts Responsive Bar Chart** + Toggleable Summary Table
- **Example Queries**:
  - *"Compare groundwater level between Jaipur and Pune in 2023"*
  - *"Ludhiana vs Amritsar extraction rate"*
  - *"Compare recharge of Jaipur, Jodhpur, and Pune"*
  - *"जयपुर और पुणे के भूजल स्तर की तुलना करें"*
- **Response Shape**: Tabular and graphical representation with values for each requested entity.

---

### 7. `rank` (Top / Highest / Lowest Ordering)
- **Description**: Ordering and ranking multiple districts or blocks by a groundwater statistic.
- **Tool**: `rank_locations(locations, metric, year, ascending)`
- **Success Rate**: **100.0%** (8/8 passed)
- **UI Widget**: **Recharts Bar Chart** + Ordered Numerical Roster
- **Example Queries**:
  - *"Rank Jaipur, Jodhpur, and Pune by stage of extraction in 2023"*
  - *"Top groundwater extraction between Jaipur and Pune"*
  - *"Lowest extraction among Ludhiana, Amritsar, and Jodhpur"*
- **Response Shape**: 1-indexed leaderboard with ranks, entity names, values, and ordering direction.

---

### 8. `trend` (Multi-Year Trajectories & Net Change)
- **Description**: Historical progression across available assessment years (2021, 2022, 2023) showing trajectory, net change delta, and trend direction.
- **Tool**: `get_trend(location, metric, start_year, end_year)`
- **Success Rate**: **100.0%** (8/8 passed)
- **UI Widget**: **Recharts Multi-Year Area Chart** with net delta pills (`+14.7% Increasing`)
- **Example Queries**:
  - *"What is the historical trend of groundwater in Jaipur?"*
  - *"Groundwater trend in Jaipur over time"*
  - *"Historical trend for Pune groundwater"*
  - *"जयपुर में भूजल का ऐतिहासिक रुझान क्या है?"*
- **Response Shape**: Yearly points array, net delta calculation, and qualitative direction (`increasing`, `decreasing`, `stable`).

---

### 9. `list_blocks` (District Block Inventories & Filtering)
- **Description**: Enumerate all administrative blocks within a district, with optional filtering by assessment category.
- **Tool**: `list_blocks(district, category, year)`
- **Success Rate**: **100.0%** (10/10 passed)
- **UI Widget**: **Interactive Filterable Block Table** with category pills, SOE %, and pre/post water levels
- **Example Queries**:
  - *"List all blocks in Jaipur in 2023"*
  - *"Show all blocks in Pune"*
  - *"List all over-exploited blocks in Jaipur"*
  - *"List semi-critical blocks in Pune in 2023"*
  - *"पुणे के सभी सुरक्षित ब्लॉकों की सूची दिखाएं"*
- **Response Shape**: Total block count and structured array of blocks with water levels and extraction stages.

---

### 10. `ambiguous` (Disambiguation Protocol)
- **Description**: When an incomplete or prefix string matches multiple geographic entities, the agent asks for clarification rather than executing an erroneous tool.
- **Tool**: `None` (`status="ambiguous"`)
- **Success Rate**: **100.0%** (5/5 passed)
- **Example Queries**:
  - *"Water level in Nag"* $\rightarrow$ Solicits clarification: *Nagpur (district)* vs *Nagpur Rural (block)*
  - *"Status of Bar"* $\rightarrow$ Solicits clarification: *Baramati (block, Pune)* vs *Barauli Ahir (block, Agra)*
  - *"Groundwater category in Bil"* $\rightarrow$ Solicits clarification: *Bilara (block, Jodhpur)*
  - *"Water level in Kot"* $\rightarrow$ Solicits clarification: *Kotputli (block, Jaipur)*
  - *"Groundwater status in Ban"* $\rightarrow$ Solicits clarification: *Bangalore North* vs *Bangalore South*
- **Response Shape**: Polite clarification message enumerating matching candidate options with their parent districts and states.

---

### 11. `no_data` (Unmonitored / Fictional Entities)
- **Description**: If a user queries a fictional, non-existent, or unmonitored location, the agent refuses to hallucinate and indicates that data is unavailable.
- **Tool**: `None` or Tool returns `{"error": "data_not_available"}`
- **Success Rate**: **100.0%** (6/6 passed)
- **Example Queries**:
  - *"groundwater level in Atlantis12345 in 2023"*
  - *"What is the extraction stage of Wakanda?"*
  - *"Is ElDorado over-exploited or safe?"*
  - *"Recharge of FakeCityXYZ"*
- **Response Shape**: Explicit statement: *"Data not available for the requested query."*

---

### 12. `out_of_scope` (Non-Hydrological Shield)
- **Description**: Queries unrelated to Indian groundwater resources (general knowledge, coding, sports, cooking) are gracefully deflected.
- **Tool**: `None` (`data={"error": "out_of_scope_refusal"}`)
- **Success Rate**: **100.0%** (6/6 passed)
- **Example Queries**:
  - *"What is the capital of France?"*
  - *"Who won the cricket world cup?"*
  - *"Write me a poem about water"*
  - *"What is the recipe for masala chai?"*
  - *"How to install Python on mac?"*
- **Response Shape**: Informative deflection message explaining that INGRES-Agent is dedicated exclusively to India's groundwater resource assessments.
