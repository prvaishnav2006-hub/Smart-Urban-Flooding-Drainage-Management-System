"""
Agent Orchestrator – Smart Urban Flood Management System
=========================================================
Coordinates all 6 agents in a multi-step agentic workflow:

  Rainfall Event
       │
       ▼
  [1] Flood Risk Agent   ──►  Zone risk assessments + early warnings
       │
       ├──► [2] Drainage Agent      ──►  Critical drain identification + maintenance schedule
       │
       └──► [3] Civic Response Agent ──► Incident prioritisation + team dispatch
                   ▲
                   │
  [4] Citizen Report Agent ──► Validated + forwarded reports
                   │
                   ▼
  [5] Dashboard Agent   ──►  Aggregated KPIs + alerts
       │
       ▼
  [6] Damage Assessment Agent ──► Post-event recovery plan

Each function logs agent-to-agent "messages" for UI workflow visualisation.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime

# Agent imports
from backend.agents.flood_risk_agent      import analyze_zone_risk, generate_early_warning
from backend.agents.drainage_agent        import (
    identify_critical_drains,
    generate_maintenance_schedule,
    recommend_preventive_action,
)
from backend.agents.civic_response_agent  import (
    prioritize_incidents,
    recommend_response_actions,
    assign_response_team,
    generate_emergency_protocol,
)
from backend.agents.citizen_report_agent  import (
    analyze_report,
    detect_duplicates,
    validate_severity,
    forward_to_civic_agent,
)
from backend.agents.dashboard_agent       import (
    get_city_summary,
    get_dashboard_metrics,
    generate_situation_report,
    get_alerts,
)
from backend.agents.damage_assessment_agent import (
    create_post_disaster_report,
    generate_recovery_plan,
    categorize_damage,
    assess_damage,
)

# Synthetic data
from backend.data.synthetic_data import (
    AHMEDABAD_ZONES,
    SURAT_ZONES,
    DRAINS,
    INCIDENTS,
    get_all_zones,
)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _msg(sender: str, receiver: str, payload_summary: str) -> dict:
    """Create an agent-to-agent message log entry."""
    return {
        "timestamp": _now_str(),
        "from": sender,
        "to": receiver,
        "message": payload_summary,
    }


# ─── Step 1: Process a rainfall event ────────────────────────────────────────

def process_rainfall_event(rainfall_data: dict[str, Any]) -> dict[str, Any]:
    """
    Trigger the Flood Risk Agent with fresh rainfall data.

    Parameters
    ----------
    rainfall_data : dict with keys `city` and `zone_overrides`
      zone_overrides is a dict mapping zone_id → new rainfall_intensity

    Returns risk assessments for all zones in the affected city, plus warnings.
    """
    city           = rainfall_data.get("city", "Surat")
    zone_overrides = rainfall_data.get("zone_overrides", {})
    messages: list[dict] = []

    all_zones = get_all_zones()
    # Apply overrides
    updated_zones = []
    for z in all_zones:
        z = dict(z)
        if z["zone_id"] in zone_overrides:
            z.update(zone_overrides[z["zone_id"]])
        updated_zones.append(z)

    city_zones = [z for z in updated_zones if z["city"].lower() == city.lower()]

    # Run Flood Risk Agent on each zone
    risk_assessments = [analyze_zone_risk(z) for z in city_zones]
    warnings = [generate_early_warning(z) for z in city_zones if analyze_zone_risk(z)["risk_level"] in ("High", "Critical")]

    critical_zones = [r for r in risk_assessments if r["risk_level"] in ("Critical", "High")]

    messages.append(_msg(
        "Rainfall Sensor Network",
        "Flood Risk Prediction Agent",
        f"New rainfall data received for {city}. "
        f"{len(zone_overrides)} zone(s) have elevated readings.",
    ))
    messages.append(_msg(
        "Flood Risk Prediction Agent",
        "Drainage Maintenance Agent",
        f"Identified {len(critical_zones)} critical/high-risk zones in {city}. "
        f"Requesting drain assessment.",
    ))
    messages.append(_msg(
        "Flood Risk Prediction Agent",
        "Civic Response Coordination Agent",
        f"Sending risk assessments for {len(critical_zones)} zones. "
        f"Requesting response team dispatch.",
    ))

    return {
        "step": "process_rainfall_event",
        "city": city,
        "zones_assessed": len(city_zones),
        "risk_assessments": risk_assessments,
        "early_warnings": warnings,
        "critical_zone_count": len(critical_zones),
        "agent_messages": messages,
        "timestamp": _now_str(),
    }


# ─── Step 2: Coordinate drain + civic response ────────────────────────────────

def coordinate_response(risk_results: dict[str, Any]) -> dict[str, Any]:
    """
    Feed risk assessment results to Drainage Agent + Civic Response Agent.

    Returns drain schedule and incident response plan.
    """
    city     = risk_results.get("city", "Surat")
    messages : list[dict] = []

    # Drainage Agent
    critical_drains = identify_critical_drains(DRAINS)
    drain_schedule  = generate_maintenance_schedule(city, DRAINS)

    messages.append(_msg(
        "Drainage Maintenance Agent",
        "Civic Response Coordination Agent",
        f"Found {len(critical_drains)} critical drains. "
        f"Maintenance schedule generated. Sharing with Response Agent.",
    ))

    # Civic Response Agent
    city_incidents = [i for i in INCIDENTS if i["city"].lower() == city.lower()]
    prioritized    = prioritize_incidents(city_incidents)
    response_plans = [recommend_response_actions(inc) for inc in prioritized[:5]]
    team_assignments = [assign_response_team(inc, city_incidents) for inc in prioritized[:5]]

    messages.append(_msg(
        "Civic Response Coordination Agent",
        "Dashboard Agent",
        f"Dispatched teams to {len(team_assignments)} incidents. "
        f"Sending status update to Dashboard.",
    ))

    return {
        "step": "coordinate_response",
        "city": city,
        "critical_drains": critical_drains[:5],
        "drain_schedule": drain_schedule[:5],
        "prioritized_incidents": prioritized,
        "response_plans": response_plans,
        "team_assignments": team_assignments,
        "agent_messages": messages,
        "timestamp": _now_str(),
    }


# ─── Step 3: Process citizen reports ─────────────────────────────────────────

def process_citizen_reports(reports: list[dict]) -> dict[str, Any]:
    """
    Run each citizen report through Citizen Report Agent and forward critical ones.

    Returns list of processed reports and any newly generated incidents.
    """
    messages: list[dict] = []
    processed: list[dict] = []
    forwarded: list[dict] = []
    existing: list[dict]  = list(INCIDENTS)

    for report in reports:
        # Validate
        validation = validate_severity(report)
        if validation["adjusted"]:
            report["flood_severity"] = validation["validated_severity"].lower()

        # Check duplicate
        dup_check = detect_duplicates(report, existing)
        if dup_check["is_duplicate"]:
            processed.append({**analyze_report(report), "duplicate": True, "duplicate_reason": dup_check["reason"]})
            continue

        # Analyse
        enriched = analyze_report(report)
        processed.append(enriched)

        # Forward if needed
        fwd = forward_to_civic_agent(report)
        if fwd["forwarded"]:
            forwarded.append(fwd)
            existing.append(fwd["incident_payload"])

    messages.append(_msg(
        "Citizen Report Agent",
        "Civic Response Coordination Agent",
        f"Processed {len(processed)} citizen reports. "
        f"Forwarded {len(forwarded)} as new incidents.",
    ))
    messages.append(_msg(
        "Civic Response Coordination Agent",
        "Dashboard Agent",
        f"Added {len(forwarded)} citizen-reported incidents to the active queue.",
    ))

    return {
        "step": "process_citizen_reports",
        "reports_processed": len(processed),
        "reports_forwarded": len(forwarded),
        "processed_reports": processed,
        "new_incidents": [f["incident_payload"] for f in forwarded if "incident_payload" in f],
        "agent_messages": messages,
        "timestamp": _now_str(),
    }


# ─── Step 4: Update dashboard ─────────────────────────────────────────────────

def update_dashboard() -> dict[str, Any]:
    """
    Dashboard Agent aggregates current state from all agents.
    """
    all_zones = get_all_zones()
    metrics   = get_dashboard_metrics(all_zones, INCIDENTS, DRAINS)
    ahm_summary = get_city_summary("Ahmedabad", all_zones, INCIDENTS, DRAINS)
    srt_summary = get_city_summary("Surat",     all_zones, INCIDENTS, DRAINS)
    alerts    = get_alerts(all_zones, INCIDENTS)
    sit_report = generate_situation_report(all_zones, INCIDENTS, DRAINS)

    messages = [
        _msg("Dashboard Agent", "All Agents", "Dashboard refreshed. All KPIs updated."),
    ]

    return {
        "step": "update_dashboard",
        "metrics": metrics,
        "ahmedabad_summary": ahm_summary,
        "surat_summary": srt_summary,
        "active_alerts": alerts[:10],
        "situation_report": sit_report,
        "agent_messages": messages,
        "timestamp": _now_str(),
    }


# ─── Step 5: Run damage assessment ────────────────────────────────────────────

def run_damage_assessment() -> dict[str, Any]:
    """
    Post-event: Damage Assessment Agent evaluates all affected zones.
    """
    all_zones      = get_all_zones()
    affected_zones = [z for z in all_zones if z["risk_level"] in ("Critical", "High")]
    damage_reports = [assess_damage(z) for z in affected_zones]
    categories     = categorize_damage(INCIDENTS)
    recovery_plan  = generate_recovery_plan(affected_zones)
    full_report    = create_post_disaster_report(all_zones, INCIDENTS, DRAINS)

    messages = [
        _msg(
            "Damage Assessment Agent",
            "Dashboard Agent",
            f"Post-flood assessment complete. {len(affected_zones)} zones affected. "
            f"Full report generated.",
        ),
        _msg(
            "Damage Assessment Agent",
            "Civic Response Coordination Agent",
            f"Recovery plan with {len(recovery_plan)} zone priorities sent for implementation.",
        ),
    ]

    return {
        "step": "run_damage_assessment",
        "affected_zones": len(affected_zones),
        "damage_reports": damage_reports,
        "damage_categories": categories,
        "recovery_plan": recovery_plan[:8],
        "full_report": full_report,
        "agent_messages": messages,
        "timestamp": _now_str(),
    }


# ─── Full Demo Monsoon Scenario ───────────────────────────────────────────────

def trigger_monsoon_scenario() -> dict[str, Any]:
    """
    Trigger a full end-to-end demo monsoon scenario for Surat.

    Simulates:
      1. Heavy rainfall spike in Rander Road + Katargam
      2. Flood Risk Agent identifies 3 critical zones
      3. Drainage Agent finds 5 blocked drains
      4. Civic Response Agent deploys 2 emergency teams
      5. 4 citizen reports filed automatically
      6. Dashboard updates
      7. Damage assessment ready

    Returns a full step-by-step workflow dict for the frontend animation.
    """
    all_messages: list[dict] = []

    # ── Step 1: Rainfall spike ───────────────────────────────────────────────
    rainfall_data = {
        "city": "Surat",
        "zone_overrides": {
            "SRT-01": {"rainfall_intensity": 68.0, "drainage_blockage_level": 90.0, "water_level": 92.0, "risk_level": "Critical", "flood_risk_score": 98.0},
            "SRT-04": {"rainfall_intensity": 62.0, "drainage_blockage_level": 88.0, "water_level": 85.0, "risk_level": "Critical", "flood_risk_score": 96.0},
            "SRT-10": {"rainfall_intensity": 55.0, "drainage_blockage_level": 82.0, "water_level": 78.0, "risk_level": "Critical", "flood_risk_score": 92.0},
        },
    }
    step1 = process_rainfall_event(rainfall_data)
    all_messages.extend(step1["agent_messages"])

    # ── Step 2: Coordinate response ──────────────────────────────────────────
    step2 = coordinate_response(step1)
    all_messages.extend(step2["agent_messages"])

    # ── Step 3: Auto-filed citizen reports ───────────────────────────────────
    demo_reports = [
        {
            "city": "Surat",
            "zone": "Rander Road",
            "flood_severity": "critical",
            "water_level_cm": 95.0,
            "blocked_drain": True,
            "description": "Street completely flooded. Car swept away near railway bridge.",
            "timestamp": _now_str(),
        },
        {
            "city": "Surat",
            "zone": "Katargam",
            "flood_severity": "critical",
            "water_level_cm": 88.0,
            "blocked_drain": True,
            "description": "Textile market flooded 3 feet deep. Drain completely blocked.",
            "timestamp": _now_str(),
        },
        {
            "city": "Surat",
            "zone": "Sarthana",
            "flood_severity": "severe",
            "water_level_cm": 72.0,
            "blocked_drain": False,
            "description": "Ground floor apartments under water near nature park approach.",
            "timestamp": _now_str(),
        },
        {
            "city": "Surat",
            "zone": "Adajan",
            "flood_severity": "severe",
            "water_level_cm": 65.0,
            "blocked_drain": True,
            "description": "Colony road submerged. Residents need help evacuating.",
            "timestamp": _now_str(),
        },
    ]
    step3 = process_citizen_reports(demo_reports)
    all_messages.extend(step3["agent_messages"])

    # ── Step 4: Dashboard update ─────────────────────────────────────────────
    step4 = update_dashboard()
    all_messages.extend(step4["agent_messages"])

    # Build structured workflow steps for frontend animation
    workflow_steps = [
        {
            "step": 1,
            "agent": "Rainfall Sensor Network → Flood Risk Agent",
            "status": "complete",
            "detail": f"Heavy rainfall detected in Surat. Peak: 68 mm/hr in Rander Road. {step1['critical_zone_count']} critical zones identified.",
            "icon": "🌧",
        },
        {
            "step": 2,
            "agent": "Flood Risk Agent",
            "status": "complete",
            "detail": f"{step1['zones_assessed']} zones analysed. {step1['critical_zone_count']} classified Critical/High. Early warnings issued.",
            "icon": "⚠",
        },
        {
            "step": 3,
            "agent": "Drainage Maintenance Agent",
            "status": "complete",
            "detail": f"{len(step2['critical_drains'])} critical drains identified in Surat. Emergency cleaning schedule generated.",
            "icon": "🔧",
        },
        {
            "step": 4,
            "agent": "Civic Response Coordination Agent",
            "status": "complete",
            "detail": f"{len(step2['team_assignments'])} response teams dispatched. Emergency protocols activated.",
            "icon": "🚨",
        },
        {
            "step": 5,
            "agent": "Citizen Report Agent",
            "status": "complete",
            "detail": f"{step3['reports_processed']} citizen reports received. {step3['reports_forwarded']} forwarded as new incidents.",
            "icon": "📱",
        },
        {
            "step": 6,
            "agent": "Urban Resilience Dashboard Agent",
            "status": "complete",
            "detail": f"Dashboard refreshed. {len(step4['active_alerts'])} active alerts. Situation report generated.",
            "icon": "📊",
        },
        {
            "step": 7,
            "agent": "Post-Disaster Damage Assessment Agent",
            "status": "pending",
            "detail": "Awaiting flood event stabilisation. Click 'Run Damage Assessment' to complete the cycle.",
            "icon": "📋",
        },
    ]

    return {
        "scenario": "Surat Monsoon Surge – Demo Scenario",
        "status": "running",
        "workflow_steps": workflow_steps,
        "affected_zones": ["Rander Road", "Katargam", "Sarthana"],
        "triggered_agents": [
            "Flood Risk Prediction Agent",
            "Drainage Maintenance Agent",
            "Civic Response Coordination Agent",
            "Citizen Report Agent",
            "Dashboard Agent",
        ],
        "step1_rainfall": step1,
        "step2_response": step2,
        "step3_citizen": step3,
        "step4_dashboard": step4,
        "all_agent_messages": all_messages,
        "timestamp": _now_str(),
        "note": "[DEMO DATA – Not official predictions]",
    }
