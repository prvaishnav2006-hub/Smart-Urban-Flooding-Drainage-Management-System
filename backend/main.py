"""
FastAPI Backend – Smart Urban Flood Management System
======================================================
All API endpoints for the dashboard, agents, and AI assistant.

Run with:
  uvicorn backend.main:app --reload --port 8000

NOTE: All data returned is DEMO DATA – Not official predictions.
"""

from __future__ import annotations
import os
import json
from typing import Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Data layer ────────────────────────────────────────────────────────────────
from backend.data.synthetic_data import (
    AHMEDABAD_ZONES,
    SURAT_ZONES,
    DRAINS,
    INCIDENTS,
    get_all_zones,
    get_zones_by_city,
    get_dashboard_summary,
    get_rainfall_trend,
)
from backend.data.models import CitizenReport, AIAssistantQuery

# ── Agents ────────────────────────────────────────────────────────────────────
from backend.agents.flood_risk_agent      import analyze_zone_risk, generate_early_warning
from backend.agents.drainage_agent        import identify_critical_drains, generate_maintenance_schedule
from backend.agents.civic_response_agent  import prioritize_incidents, recommend_response_actions
from backend.agents.citizen_report_agent  import analyze_report, detect_duplicates, forward_to_civic_agent
from backend.agents.dashboard_agent       import (
    get_dashboard_metrics, get_alerts, generate_situation_report, get_city_summary,
)
from backend.agents.damage_assessment_agent import (
    create_post_disaster_report, generate_recovery_plan, categorize_damage, assess_damage,
)

# ── Orchestrator ──────────────────────────────────────────────────────────────
from backend.orchestrator import trigger_monsoon_scenario, run_damage_assessment

# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Urban Flood Management API",
    description="Agentic AI-based flood management system for Ahmedabad and Surat. DEMO DATA.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for citizen reports submitted during the session
_citizen_reports: list[dict] = []


# ─── Health check ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "system": "Smart Urban Flood Management System",
        "cities": ["Ahmedabad", "Surat"],
        "status": "operational",
        "demo": True,
        "note": "DEMO DATA – Not official predictions",
    }


# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.get("/api/dashboard")
def get_dashboard():
    """Return all KPIs for the dashboard home screen."""
    all_zones = get_all_zones()
    metrics   = get_dashboard_metrics(all_zones, INCIDENTS, DRAINS)
    summary   = get_dashboard_summary()
    rainfall  = get_rainfall_trend()

    # Risk distribution per city
    ahm_summary = get_city_summary("Ahmedabad", all_zones, INCIDENTS, DRAINS)
    srt_summary = get_city_summary("Surat",     all_zones, INCIDENTS, DRAINS)

    return {
        "metrics": metrics,
        "summary": summary,
        "rainfall_trend": rainfall,
        "ahmedabad_summary": ahm_summary,
        "surat_summary": srt_summary,
        "note": "DEMO DATA – Not official predictions",
    }


# ─── Zones ────────────────────────────────────────────────────────────────────

@app.get("/api/zones/{city}")
def get_zones(city: str):
    """Return all zones for a given city with risk assessments."""
    if city.lower() not in ("ahmedabad", "surat"):
        raise HTTPException(status_code=400, detail="City must be 'ahmedabad' or 'surat'")
    zones = get_zones_by_city(city)
    if not zones:
        raise HTTPException(status_code=404, detail=f"No zones found for city: {city}")
    # Enrich with agent risk assessment
    enriched = []
    for z in zones:
        assessment = analyze_zone_risk(z)
        enriched.append({**z, "agent_assessment": assessment})
    return {"city": city.title(), "zones": enriched, "count": len(enriched)}


@app.get("/api/zones")
def get_all_zones_endpoint():
    """Return all zones from both cities."""
    all_zones = get_all_zones()
    return {"zones": all_zones, "count": len(all_zones)}


# ─── Incidents ────────────────────────────────────────────────────────────────

@app.get("/api/incidents")
def get_incidents(city: Optional[str] = None, severity: Optional[str] = None):
    """Return all incidents, optionally filtered by city and/or severity."""
    incidents = list(INCIDENTS) + list(_citizen_reports)

    if city:
        incidents = [i for i in incidents if i.get("city", "").lower() == city.lower()]
    if severity:
        incidents = [i for i in incidents if i.get("severity", "").lower() == severity.lower()]

    prioritized = prioritize_incidents(incidents)
    return {"incidents": prioritized, "count": len(prioritized)}


@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id: str):
    """Return a single incident with response recommendations."""
    all_incidents = list(INCIDENTS) + list(_citizen_reports)
    match = next((i for i in all_incidents if i["incident_id"] == incident_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    response_plan = recommend_response_actions(match)
    return {**match, "response_plan": response_plan}


# ─── Drainage ─────────────────────────────────────────────────────────────────

@app.get("/api/drains")
def get_drains(city: Optional[str] = None):
    """Return all drain infrastructure, optionally filtered by city."""
    drains = list(DRAINS)
    if city:
        drains = [d for d in drains if d.get("city", "").lower() == city.lower()]
    critical = identify_critical_drains(drains)
    return {
        "drains": drains,
        "critical_drains": critical,
        "count": len(drains),
    }


@app.get("/api/drains/schedule/{city}")
def get_drain_schedule(city: str):
    """Return prioritised maintenance schedule for a city's drains."""
    if city.lower() not in ("ahmedabad", "surat"):
        raise HTTPException(status_code=400, detail="City must be 'ahmedabad' or 'surat'")
    schedule = generate_maintenance_schedule(city, DRAINS)
    return {"city": city.title(), "schedule": schedule}


# ─── Citizen Report ───────────────────────────────────────────────────────────

@app.post("/api/citizen-report")
def submit_citizen_report(report: CitizenReport):
    """Submit a citizen flood report. Returns enriched report and incident if forwarded."""
    report_dict = report.dict()
    if not report_dict.get("timestamp"):
        report_dict["timestamp"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    # Validate and analyse
    enriched  = analyze_report(report_dict)
    dup_check = detect_duplicates(report_dict, list(INCIDENTS) + _citizen_reports)
    forwarded = forward_to_civic_agent(report_dict)

    if forwarded.get("forwarded") and not dup_check["is_duplicate"]:
        incident = forwarded["incident_payload"]
        _citizen_reports.append(incident)

    return {
        "status": "received",
        "report": enriched,
        "duplicate_check": dup_check,
        "forwarded_to_civic_agent": forwarded.get("forwarded", False),
        "new_incident_id": forwarded.get("incident_payload", {}).get("incident_id") if forwarded.get("forwarded") else None,
        "note": "DEMO DATA – Not official predictions",
    }


# ─── AI Assistant ─────────────────────────────────────────────────────────────

# IBM Granite simulated responses keyed by topic keywords
_GRANITE_DEMOS = {
    "highest flood risk": {
        "answer": (
            "Based on current sensor data, the highest flood risk zones are:\n"
            "1. Rander Road, Surat – Risk Score: 95/100 (CRITICAL)\n"
            "2. Katargam, Surat – Risk Score: 93/100 (CRITICAL)\n"
            "3. Adajan, Surat – Risk Score: 91/100 (CRITICAL)\n"
            "4. Bapunagar, Ahmedabad – Risk Score: 85/100 (CRITICAL)\n"
            "5. Vatva, Ahmedabad – Risk Score: 88/100 (CRITICAL)"
        ),
        "reasoning": (
            "These zones exhibit concurrent elevation in all three primary risk indicators: "
            "rainfall intensity above 45 mm/hr, drainage blockage exceeding 75%, and water levels "
            "surpassing 70 cm. Historical flood frequency scores ≥7/10 confirm chronic vulnerability."
        ),
        "actions": [
            "Activate Level-4 emergency protocol for Rander Road and Katargam immediately",
            "Pre-position rescue boats and high-capacity pumps",
            "Issue mandatory evacuation advisory for low-lying sub-zones",
            "Alert NDRF and State Disaster Response Force",
        ],
        "confidence": 0.92,
    },
    "drains need urgent": {
        "answer": (
            "The following drains require urgent maintenance (blockage ≥75%):\n"
            "1. DR-SRT-01: Rander Road Canal – 88% blocked (CRITICAL)\n"
            "2. DR-SRT-02: Katargam Storm Sewer – 85% blocked (CRITICAL)\n"
            "3. DR-AHM-01: Naroda Industrial Estate – 82% blocked (CRITICAL)\n"
            "4. DR-AHM-03: Bapunagar Storm Drain – 79% blocked (CRITICAL)\n"
            "5. DR-SRT-03: Adajan Estuary Outlet – 76% blocked (CRITICAL)"
        ),
        "reasoning": (
            "Blockage levels above 75% effectively reduce drainage capacity to near-zero. "
            "During rainfall exceeding 40 mm/hr, these blocked drains cause drainage overflow "
            "within 15-20 minutes, directly leading to street flooding and waterlogging."
        ),
        "actions": [
            "Deploy jet-cleaning vehicles to Rander Road Canal and Katargam Storm Sewer within 1 hour",
            "Dispatch manual drain crew to Bapunagar Storm Drain",
            "Install temporary pump bypass for Naroda Industrial Estate drain",
            "Schedule structural inspection for Adajan Estuary Outlet",
        ],
        "confidence": 0.94,
    },
    "surat": {
        "answer": (
            "Surat Flood Situation Summary (DEMO DATA):\n\n"
            "Overall City Risk: CRITICAL\n"
            "• 4 zones at Critical risk (Rander Road, Katargam, Adajan, Sarthana)\n"
            "• 2 zones at High risk (Udhna, Athwa)\n"
            "• Peak rainfall: 52 mm/hr in Rander Road\n"
            "• 3 critical drains with 75%+ blockage\n"
            "• 5 active incidents including 2 Critical\n"
            "• 25+ citizen reports in last 2 hours\n"
            "• 3 response teams currently deployed"
        ),
        "reasoning": (
            "Surat's risk profile is driven by its low-lying topography and the Tapi River's "
            "proximity. The combination of high-density informal settlements (Rander, Katargam), "
            "aging drainage infrastructure last cleaned in 2024, and concentrated monsoon rainfall "
            "creates a high-probability flood scenario. Historical flooding in 2006 and 2013 "
            "confirm this vulnerability pattern."
        ),
        "actions": [
            "Maintain Level-4 emergency response in Rander Road and Katargam",
            "Begin resident evacuation from ground-floor units in Adajan",
            "Emergency drain cleaning for Rander Road Canal and Katargam Storm Sewer",
            "Coordinate with Surat Municipal Corporation and SDRF for reinforcement",
            "Issue city-wide public alert via SMS and loudspeaker systems",
        ],
        "confidence": 0.91,
    },
    "emergency teams": {
        "answer": (
            "Recommended actions for emergency teams in high-risk zones:\n\n"
            "IMMEDIATE (0-2 hours):\n"
            "• Deploy water pumps at all Critical zones\n"
            "• Establish incident command post at zone boundary\n"
            "• Conduct rapid building-by-building sweep for stranded persons\n\n"
            "SHORT-TERM (2-6 hours):\n"
            "• Maintain continuous dewatering operations\n"
            "• Coordinate relief material distribution\n"
            "• Set up temporary medical triage\n\n"
            "ONGOING:\n"
            "• Report water level readings every 30 minutes to EOC\n"
            "• Escalate immediately if water rises above 1 metre"
        ),
        "reasoning": (
            "High-risk zones with rainfall >35 mm/hr and blockage >60% can see water levels "
            "rise at 5-8 cm per hour during peak monsoon. The 2-hour action window is critical "
            "before conditions become life-threatening in ground-floor structures."
        ),
        "actions": [
            "Each team leader to check in with EOC every 30 minutes",
            "Priority: elderly, disabled, children for evacuation",
            "Do not enter structures with visible structural damage",
            "Mark cleared buildings with chalk code per protocol",
        ],
        "confidence": 0.89,
    },
    "rander road": {
        "answer": (
            "Rander Road is classified as HIGH RISK (Score: 95/100) due to:\n\n"
            "⚠ Rainfall: 52 mm/hr (Critical threshold: ≥45 mm/hr)\n"
            "⚠ Drainage Blockage: 80% (Critical: ≥70%)\n"
            "⚠ Historical Flood Frequency: 8.5/10 (Chronic flood zone)\n"
            "⚠ Water Level: 75 cm (High: ≥40 cm)\n"
            "⚠ Citizen Reports: 25 reports in 2 hours\n"
            "⚠ Primary drain (DR-SRT-01) last cleaned: December 2024"
        ),
        "reasoning": (
            "Rander Road sits in a topographic depression between the Tapi River basin and the "
            "urban stormwater channel. Its drainage infrastructure was designed for 35 mm/hr capacity "
            "but carries double that during peak monsoon. The Rander Road Canal (DR-SRT-01) has not "
            "been cleaned since December 2024 and is 88% blocked with solid waste and silt accumulation. "
            "This combination – high rainfall, near-zero drainage, and historical repeat flooding – "
            "produces the system's highest risk score of 95/100."
        ),
        "actions": [
            "Issue IMMEDIATE evacuation order for Rander Road residential pockets",
            "Deploy jet-cleaning vehicle to Rander Road Canal without delay",
            "Close Rander Road to vehicular traffic",
            "Deploy 2× high-capacity pumps (100,000 L/hr each)",
            "Escalate to municipal commissioner and district collector",
        ],
        "confidence": 0.96,
    },
}

def _get_granite_response(question: str, city: Optional[str]) -> dict:
    """
    Try IBM Granite watsonx.ai API. Fall back to demo responses if key unavailable.
    """
    api_key  = os.environ.get("IBM_API_KEY")
    url      = os.environ.get("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    proj_id  = os.environ.get("IBM_PROJECT_ID")

    if api_key and proj_id:
        try:
            from ibm_watsonx_ai import Credentials
            from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
            from ibm_watsonx_ai.foundation_models import ModelInference

            system_prompt = (
                "You are an AI assistant for the Smart Urban Flood Management System "
                "for Ahmedabad and Surat, Gujarat. You help municipal authorities make "
                "decisions about flood risk, drainage maintenance, and emergency response. "
                "Provide concise, actionable recommendations based on the available data. "
                "Always end responses with recommended actions as a numbered list."
            )

            creds = Credentials(url=url, api_key=api_key)
            model = ModelInference(
                model_id="ibm/granite-3-8b-instruct",
                credentials=creds,
                project_id=proj_id,
                params={
                    GenParams.MAX_NEW_TOKENS: 512,
                    GenParams.TEMPERATURE: 0.3,
                },
            )
            prompt = f"{system_prompt}\n\nUser question: {question}"
            result = model.generate_text(prompt=prompt)
            return {
                "answer": result,
                "reasoning": "Generated by IBM Granite 3-8B Instruct via watsonx.ai",
                "recommended_actions": ["See answer above for detailed recommendations"],
                "confidence": 0.85,
                "source": "IBM Granite LLM (granite-3-8b-instruct via watsonx.ai)",
                "agent_used": "AI Assistant – IBM Granite",
            }
        except Exception as exc:
            # Fall through to demo
            print(f"[Granite API fallback] {exc}")

    # ── Demo response selection ────────────────────────────────────────────
    q_lower = question.lower()
    demo_key = None
    for key in _GRANITE_DEMOS:
        if key in q_lower:
            demo_key = key
            break

    if demo_key is None:
        # Generic fallback
        all_zones   = get_all_zones()
        critical    = [z["zone_name"] for z in all_zones if z["risk_level"] == "Critical"]
        demo_resp   = {
            "answer": (
                f"[DEMO – IBM Granite Simulated Response]\n\n"
                f"Based on current system data for {city or 'Ahmedabad and Surat'}:\n"
                f"• Currently {len(critical)} zones at Critical risk: {', '.join(critical[:3])}\n"
                f"• 13 active incidents across both cities\n"
                f"• 3 critical drains requiring immediate attention\n\n"
                f"For more specific information, please use one of the quick-question buttons "
                f"or ask about a specific zone, drain, or incident."
            ),
            "reasoning": "Response generated using DEMO synthetic data from the flood management dataset.",
            "recommended_actions": [
                "Use the pre-built quick questions for detailed analysis",
                "Check the Flood Risk Map for zone-specific details",
                "Review the Drainage Management tab for drain status",
            ],
            "confidence": 0.70,
        }
    else:
        demo_resp = _GRANITE_DEMOS[demo_key]

    return {
        "answer": demo_resp["answer"],
        "reasoning": demo_resp["reasoning"],
        "recommended_actions": demo_resp["actions"] if "actions" in demo_resp else demo_resp.get("recommended_actions", []),
        "confidence": demo_resp["confidence"],
        "source": "[DEMO – Simulated Granite Response] (Set IBM_API_KEY env var for live Granite)",
        "agent_used": "AI Assistant – IBM Granite (DEMO)",
    }


@app.post("/api/ai-assistant")
def ai_assistant(query: AIAssistantQuery):
    """Query the IBM Granite AI assistant."""
    if not query.question or not query.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    response = _get_granite_response(query.question, query.city)
    return response


# ─── Scenario / Workflow ──────────────────────────────────────────────────────

@app.post("/api/trigger-scenario")
def trigger_scenario():
    """Trigger the demo monsoon scenario orchestrator."""
    result = trigger_monsoon_scenario()
    return result


@app.get("/api/agent-workflow")
def get_agent_workflow():
    """Return current agent workflow status and collaboration graph."""
    return {
        "agents": [
            {
                "id": 1,
                "name": "Flood Risk Prediction Agent",
                "role": "Analyses zone sensor data to compute flood risk scores and early warnings",
                "inputs": ["Rainfall sensor data", "Water level sensors", "Historical records"],
                "outputs": ["Risk scores", "Early warnings", "Contributing factors"],
                "status": "active",
                "color": "#ef4444",
            },
            {
                "id": 2,
                "name": "Drainage Maintenance Agent",
                "role": "Schedules drain cleaning and identifies critical blockages",
                "inputs": ["Drain condition data", "Blockage sensors", "Maintenance logs"],
                "outputs": ["Maintenance schedule", "Critical drain list", "Preventive actions"],
                "status": "active",
                "color": "#f59e0b",
            },
            {
                "id": 3,
                "name": "Civic Response Coordination Agent",
                "role": "Prioritises incidents and dispatches response teams",
                "inputs": ["Incident reports", "Risk assessments", "Team availability"],
                "outputs": ["Prioritised incident queue", "Team assignments", "Emergency protocols"],
                "status": "active",
                "color": "#3b82f6",
            },
            {
                "id": 4,
                "name": "Citizen Flood Reporting Agent",
                "role": "Validates citizen reports and creates new incidents",
                "inputs": ["Citizen form submissions", "Mobile reports"],
                "outputs": ["Validated reports", "New incidents", "Duplicate flags"],
                "status": "active",
                "color": "#8b5cf6",
            },
            {
                "id": 5,
                "name": "Urban Resilience Dashboard Agent",
                "role": "Aggregates all agent outputs into KPIs and alerts",
                "inputs": ["Risk assessments", "Incident statuses", "Drain reports"],
                "outputs": ["Dashboard metrics", "Active alerts", "Situation reports"],
                "status": "active",
                "color": "#10b981",
            },
            {
                "id": 6,
                "name": "Post-Disaster Damage Assessment Agent",
                "role": "Assesses post-flood damage and generates recovery priorities",
                "inputs": ["Zone water levels", "Incident history", "Infrastructure reports"],
                "outputs": ["Damage estimates", "Recovery plan", "Full assessment report"],
                "status": "standby",
                "color": "#6366f1",
            },
        ],
        "workflow": [
            {"from": "Rainfall Sensors", "to": "Agent 1 – Flood Risk"},
            {"from": "Agent 1 – Flood Risk", "to": "Agent 2 – Drainage"},
            {"from": "Agent 1 – Flood Risk", "to": "Agent 3 – Civic Response"},
            {"from": "Agent 2 – Drainage", "to": "Agent 3 – Civic Response"},
            {"from": "Agent 4 – Citizen Reports", "to": "Agent 3 – Civic Response"},
            {"from": "Agent 3 – Civic Response", "to": "Agent 5 – Dashboard"},
            {"from": "Agent 1 – Flood Risk", "to": "Agent 5 – Dashboard"},
            {"from": "Agent 5 – Dashboard", "to": "Agent 6 – Damage Assessment"},
        ],
        "note": "DEMO DATA – Not official predictions",
    }


# ─── Damage Assessment ────────────────────────────────────────────────────────

@app.post("/api/damage-assessment")
def run_damage_assessment_endpoint():
    """Run the post-disaster damage assessment across all affected zones."""
    result = run_damage_assessment()
    return result


# ─── Alerts ───────────────────────────────────────────────────────────────────

@app.get("/api/alerts")
def get_active_alerts():
    """Return all active alerts from zone risks and incidents."""
    all_zones = get_all_zones()
    alerts    = get_alerts(all_zones, INCIDENTS)
    return {
        "alerts": alerts,
        "count": len(alerts),
        "critical_count": len([a for a in alerts if a["severity"] == "Critical"]),
    }
