# 🌊 Smart Urban Flooding & Drainage Management System
### Ahmedabad & Surat, Gujarat, India – Agentic AI Prototype

> ⚠ **DEMO DATA ONLY – Not official predictions. For academic/college project demonstration.**

---

## 📋 Project Overview

This is a fully functional prototype of an **Agentic AI-based Smart Urban Flooding & Drainage Management System** built for the cities of **Ahmedabad** and **Surat**, Gujarat, India.

Unlike a traditional dashboard that passively shows data, this system uses **6 collaborating AI agents** powered by **IBM Granite LLM** to autonomously analyse risks, schedule maintenance, dispatch response teams, validate citizen reports, and produce post-disaster assessments — all in a coordinated multi-agent workflow.

---

## 🏗 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  SMART URBAN FLOOD MANAGEMENT                   │
│                    AGENTIC AI ARCHITECTURE                      │
└─────────────────────────────────────────────────────────────────┘

  ┌─────────────────────┐
  │  Rainfall Sensors   │  (IoT / Simulated Data)
  │  Water Level Gauges │
  │  Drain Blockage IoT │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐         ┌─────────────────────────┐
  │  Agent 1            │──────►  │  Agent 2                │
  │  Flood Risk         │         │  Drainage Maintenance   │
  │  Prediction Agent   │         │  Scheduling Agent       │
  └──────────┬──────────┘         └────────────┬────────────┘
             │                                  │
             │         ┌────────────────────────┘
             ▼         ▼
  ┌─────────────────────────────────────────────┐
  │           Agent 3                           │
  │  Real-Time Civic Response Coordination      │
  │  Agent                                      │
  └──────────────────────┬──────────────────────┘
             ▲            │
             │            │
  ┌──────────┴──────────┐  │
  │  Agent 4            │  │
  │  Citizen Flood      │  │
  │  Reporting Agent    │  │
  └─────────────────────┘  │
                           ▼
  ┌─────────────────────────────────────────────┐
  │           Agent 5                           │
  │  Urban Resilience Dashboard Agent           │
  └──────────────────────┬──────────────────────┘
                         │
                         ▼
  ┌─────────────────────────────────────────────┐
  │           Agent 6                           │
  │  Post-Disaster Damage Assessment Agent      │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │  ORCHESTRATOR (orchestrator.py)             │
  │  Coordinates all 6 agents, manages message  │
  │  passing, triggers cascade workflows        │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │  FastAPI Backend (main.py)                  │
  │  REST API layer exposing agent outputs      │
  └─────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────┐
  │  Frontend (index.html)                      │
  │  Single-file dashboard (HTML+CSS+JS)        │
  │  Leaflet.js maps, Chart.js charts           │
  │  8 tabs: Dashboard, Map, Incidents,         │
  │  Drainage, Report, AI, Damage, Workflow     │
  └─────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
flood-management/
├── index.html                          # Main frontend dashboard (self-contained)
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── backend/
    ├── __init__.py
    ├── main.py                         # FastAPI REST API (10 endpoints)
    ├── orchestrator.py                 # Agent coordination & workflow
    ├── agents/
    │   ├── __init__.py
    │   ├── flood_risk_agent.py         # Agent 1: Risk prediction
    │   ├── drainage_agent.py           # Agent 2: Drain maintenance
    │   ├── civic_response_agent.py     # Agent 3: Response coordination
    │   ├── citizen_report_agent.py     # Agent 4: Report validation
    │   ├── dashboard_agent.py          # Agent 5: KPI aggregation
    │   └── damage_assessment_agent.py  # Agent 6: Post-disaster assessment
    └── data/
        ├── __init__.py
        ├── synthetic_data.py           # Demo datasets: zones, drains, incidents
        └── models.py                   # Pydantic data models
```

---

## 🤖 AI Agents Description

### Agent 1 — Flood Risk Prediction Agent (`flood_risk_agent.py`)
**Role:** Analyses 5 weighted risk factors to compute a zone-level flood risk score (0-100).

| Factor | Weight | Threshold |
|--------|--------|-----------|
| Rainfall Intensity (mm/hr) | 30% | Critical ≥ 45 mm/hr |
| Drainage Blockage (%) | 25% | Critical ≥ 70% |
| Historical Flood Frequency (0-10) | 20% | High ≥ 7/10 |
| Water Level (cm) | 15% | High ≥ 40 cm |
| Citizen Reports Count | 10% | High ≥ 8 reports |

**Outputs:** Risk score, risk level (Low/Medium/High/Critical), contributing factors with thresholds, early warning messages.

---

### Agent 2 — Drainage Maintenance Scheduling Agent (`drainage_agent.py`)
**Role:** Prioritises drain cleaning schedules based on blockage %, days since maintenance, and structural condition.

**Urgency formula:** `score = 0.5 × (blockage/100) + 0.3 × (days_old/365) + 0.2 × condition_score`

**Outputs:** Prioritised maintenance schedule, emergency cleaning orders for drains ≥75% blocked, preventive action recommendations.

---

### Agent 3 — Civic Response Coordination Agent (`civic_response_agent.py`)
**Role:** Acts as the command-and-control brain — sorts incidents by severity, recommends tailored response actions, assigns teams, and generates emergency protocols.

**Key differentiator:** Specialised team assignment (e.g., drain crews → Blocked Drain, rescue boats → Critical Flooding).

**Outputs:** Prioritised incident queue, team dispatch orders, Level 2-4 emergency protocols.

---

### Agent 4 — Citizen Flood Reporting Agent (`citizen_report_agent.py`)
**Role:** Validates and enriches citizen-submitted reports. Auto-upgrades severity when objective data (water level ≥ 70 cm) contradicts the user's selection. Detects duplicates within 30-minute windows.

**Forwarding rule:** Severity ≥ High (after validation) → automatic incident creation and forwarding to Agent 3.

**Outputs:** Validated reports, severity adjustments with explanations, new incident payloads.

---

### Agent 5 — Urban Resilience Dashboard Agent (`dashboard_agent.py`)
**Role:** Aggregates all other agent outputs into unified city-level KPIs. The "single pane of glass" for municipal officers.

**Outputs:** Dashboard metrics (6 KPI cards), active alerts (zone + incident based), city summaries, plain-text situation report.

---

### Agent 6 — Post-Disaster Damage Assessment Agent (`damage_assessment_agent.py`)
**Role:** Post-event assessment. Estimates infrastructure/property/economic damage per zone. Generates recovery priority plans and downloadable reports.

**Damage model:** Scales base estimates by risk level and water depth. Recovery timeline: 3 days (Low) → 30 days (Critical).

**Outputs:** Zone-wise damage estimates (₹ Crore), recovery priority plan, full downloadable assessment report.

---

## 🔗 Agent Orchestration (Agentic Workflow)

The [`orchestrator.py`](backend/orchestrator.py) coordinates all agents in a 5-step cascade:

```
Step 1: process_rainfall_event()    → Flood Risk Agent analyses updated sensor data
Step 2: coordinate_response()       → Drainage Agent + Civic Response Agent act on risk output
Step 3: process_citizen_reports()   → Citizen Agent validates and forwards reports
Step 4: update_dashboard()          → Dashboard Agent aggregates all results
Step 5: run_damage_assessment()     → Damage Agent produces post-event recovery plan
```

**Agent-to-agent message passing:** Every function exchange is logged as a structured `{from, to, message, timestamp}` record, visible in the UI's Scenario Event Log.

---

## 🤖 IBM Granite Integration

### Live Mode (requires IBM Cloud credentials)
Set the following environment variables before starting the backend:
```bash
export IBM_API_KEY="your-ibm-api-key"
export IBM_WATSONX_URL="https://us-south.ml.cloud.ibm.com"
export IBM_PROJECT_ID="your-project-id"
```

The [`/api/ai-assistant`](backend/main.py) endpoint will then call **granite-3-8b-instruct** via `ibm-watsonx-ai` SDK with a domain-specific system prompt:

```
You are an AI assistant for the Smart Urban Flood Management System for Ahmedabad and Surat, Gujarat.
You help municipal authorities make decisions about flood risk, drainage maintenance, and emergency response.
Provide concise, actionable recommendations based on the available data.
```

### Demo Mode (no API key required)
If IBM credentials are not set, the system automatically falls back to pre-built **domain-accurate simulated responses** clearly labeled `[DEMO – Simulated Granite Response]`. The frontend AI Assistant has 5 pre-built quick questions with detailed responses.

All AI responses include:
- ✅ Answer (structured, actionable)
- ✅ Reasoning (explainability)
- ✅ Recommended Actions (numbered list)
- ✅ Confidence score
- ✅ Clear source label (live or demo)

---

## ☁ IBM Cloud Integration Points

| IBM Service | Usage | Status |
|-------------|-------|--------|
| **IBM watsonx.ai** | IBM Granite LLM (granite-3-8b-instruct) for AI Assistant | Demo / Live with API key |
| **IBM Cloud Object Storage** | Store uploaded citizen photos | Future enhancement |
| **IBM Watson IoT Platform** | Real-time sensor data integration | Future enhancement |
| **IBM Cloud Databases (PostgreSQL)** | Replace in-memory synthetic data | Future enhancement |
| **IBM Event Streams (Kafka)** | Real-time agent message streaming | Future enhancement |

---

## 🚀 Setup Instructions

### 1. Clone / unzip the project
```
flood-management/
```

### 2. Install Python dependencies
```bash
cd flood-management
pip install -r requirements.txt
```

### 3. (Optional) Set IBM Granite credentials
```bash
# Windows PowerShell
$env:IBM_API_KEY = "your-key"
$env:IBM_WATSONX_URL = "https://us-south.ml.cloud.ibm.com"
$env:IBM_PROJECT_ID = "your-project-id"
```

### 4. Start the backend
```bash
uvicorn backend.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.
Interactive API docs: `http://localhost:8000/docs`

### 5. Open the frontend
Simply open `index.html` in any modern browser — **no build step required**.

The frontend works completely standalone (all data is embedded inline). When the backend is running, you can also point the frontend to `http://localhost:8000` for live API data.

---

## 🎬 Demo Workflow Guide

### Option A — Frontend only (no backend needed)
1. Open `index.html` in Chrome/Firefox/Edge
2. Explore the **Dashboard** tab (KPI cards, charts, alerts)
3. Click **Flood Risk Map** to see Leaflet map with colour-coded zones
4. Browse **Incidents** and use the filter controls
5. Go to **Drainage Mgmt** to see drain condition table
6. Try **Citizen Report** — submit a form with water level ≥ 70cm and watch the severity upgrade
7. Visit **AI Assistant** — click quick-question buttons to see Granite-style responses with reasoning
8. Go to **Agent Workflow** → click **🌧 Run Demo Scenario** to watch the 7-step agentic cascade animate in real-time
9. After the scenario completes, click **📋 Run Damage Assessment** to complete the cycle

### Option B — Full stack (backend + frontend)
1. Run `uvicorn backend.main:app --reload --port 8000`
2. Open `index.html` and use browser DevTools Network tab to observe API calls
3. The `/api/trigger-scenario` endpoint runs the full orchestrator workflow server-side

---

## 📊 Dataset Description

### Zones (20 total)
| City | Zones |
|------|-------|
| Ahmedabad | Satellite, Naroda, Vatva, Gota, Bopal, Naranpura, Maninagar, Chandkheda, Bapunagar, Thaltej |
| Surat | Rander Road, Adajan, Vesu, Katargam, Udhna, Althan, Piplod, Athwa, Pal, Sarthana |

Each zone includes: rainfall intensity, blockage level, water level, flood risk score, historical flood frequency, population density, citizen report count, maintenance status.

### Drains (20 total)
10 per city, ranging from Good (12% blocked) to Critical (88% blocked). The 6 critical drains are specifically located in high-risk zones.

### Incidents (15 total)
Mix of Flooding, Waterlogging, Blocked Drain, and Road Closure incidents across both cities. Severity distribution: 5 Critical, 4 High, 4 Medium, 2 Low (including 2 Resolved).

---

## 🛠 Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, Vanilla JavaScript (ES6+) |
| Maps | Leaflet.js 1.9.4 (OpenStreetMap tiles) |
| Charts | Chart.js 4.4.2 |
| Backend | Python 3.10+, FastAPI 0.111, Uvicorn |
| Data Models | Pydantic 2.7 |
| AI / LLM | IBM Granite (granite-3-8b-instruct) via ibm-watsonx-ai SDK |
| Data | Synthetic demo dataset (Python dictionaries) |

---

## 🔮 Future Enhancements

1. **Real sensor integration** — Connect to AMC/SMC IoT drainage sensors and IMD rainfall APIs
2. **Live Granite streaming** — Stream LLM tokens for real-time AI response display
3. **PostgreSQL backend** — Replace in-memory data with persistent database
4. **WhatsApp citizen reporting** — Integrate Twilio WhatsApp API with Citizen Agent
5. **NDRF/SDRF integration** — Direct API call to state disaster management authority
6. **Predictive flooding** — Train an LSTM model on 10-year historical flood data for 24-hr ahead prediction
7. **Mobile app** — React Native companion app for field officers
8. **Multi-city scaling** — Extend to Gandhinagar, Rajkot, Vadodara
9. **Satellite imagery analysis** — IBM watsonx + satellite images for damage assessment
10. **Blockchain audit trail** — Immutable log of all agent decisions for accountability

---

## 👥 Academic Project Information

**Project:** Agentic AI-based Smart Urban Flood Management System  
**Cities Covered:** Ahmedabad & Surat, Gujarat, India  
**LLM Platform:** IBM watsonx.ai (IBM Granite)  
**Demo Status:** Fully functional prototype with simulated data  

> All data in this project is synthetic demo data created for educational purposes.
> It does not represent actual flood risk assessments for Ahmedabad or Surat.
> Not for use in real emergency management decisions.

---

*Powered by IBM Granite LLM via watsonx.ai*
