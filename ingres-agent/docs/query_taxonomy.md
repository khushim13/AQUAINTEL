# Supported Query Taxonomy & Metrics

| Category ID | Query Type | Purpose | Example Citizen/Official Query | Underlying INGRES Metric |
|-------------|------------|---------|--------------------------------|--------------------------|
| `CAT-1` | **Extraction Stage & Category** | Check vulnerability status of a district/block | *"Is Jaipur over-exploited or safe?"* | Stage of GW Extraction (`SOE %`), Category (`Safe`, `Semi-Critical`, `Critical`, `Over-Exploited`) |
| `CAT-2` | **Water Level Depth (mbgl)** | Retrieve depth to groundwater table | *"What was the pre-monsoon water level in Pune in 2022?"* | Depth to Water Level (meters below ground level, `mbgl`) |
| `CAT-3` | **Annual Recharge & Extraction** | Quantitative resource estimation in ham/bcm | *"How much groundwater was extracted for irrigation in Jodhpur in 2023?"* | Total Extraction, Irrigation vs Domestic/Industrial, Total Annual Recharge |
| `CAT-4` | **Stressed Unit Identification** | Identify critical & over-exploited blocks | *"List all over-exploited blocks in Ludhiana"* | Assessment Unit level status aggregation |
| `CAT-5` | **Comparative Analysis** | Contrast two or more districts | *"Compare groundwater recharge between Nagpur and Nashik in 2023"* | Multi-entity cross comparison |
| `CAT-6` | **Historical Trend** | Analyze multi-year temporal trends | *"How has the groundwater level changed in Ajmer from 2020 to 2023?"* | Multi-year delta analysis |
