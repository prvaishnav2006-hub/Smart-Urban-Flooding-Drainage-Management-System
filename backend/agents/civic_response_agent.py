"""
Agent 3 – Real-Time Civic Response Coordination Agent
======================================================
Prioritises incidents, recommends response actions, assigns response teams,
and generates emergency protocols for affected zones.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any


# ─── Severity order for sorting ───────────────────────────────────────────────
SEVERITY_ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

# ─── Team pool (static demo roster) ──────────────────────────────────────────
TEAM_POOL = {
    "Ahmedabad": [
        "Rapid Response Team Alpha",
        "Pump Unit Delta",
        "Industrial Emergency Team",
        "Relief & Evacuation Team",
        "Traffic Management Unit",
        "Drain Cleaning Crew A2",
    ],
    "Surat": [
        "Rescue Team Gamma",
        "Pump Unit Beta",
        "Response Team Epsilon",
        "Drain Cleaning Crew D2",
        "Area Response Team Z",
        "Maintenance Crew P1",
    ],
}


# ─── Public API ───────────────────────────────────────────────────────────────

def prioritize_incidents(incidents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort incidents by severity (Critical first) then by reported_time (earliest first).

    Returns the sorted list with an added `priority_rank` field.
    """
    sorted_inc = sorted(
        incidents,
        key=lambda i: (
            SEVERITY_ORDER.get(i.get("severity", "Low"), 3),
            i.get("reported_time", ""),
        ),
    )
    for rank, inc in enumerate(sorted_inc, start=1):
        inc = dict(inc)          # avoid mutating the original
        inc["priority_rank"] = rank
        sorted_inc[rank - 1] = inc
    return sorted_inc


def recommend_response_actions(incident: dict[str, Any]) -> dict[str, Any]:
    """
    Produce a tailored list of response actions for a given incident.

    Returns dict with: incident_id, severity, type, recommended_actions,
    escalation_required (bool), estimated_resolution_hours, agent.
    """
    severity = incident.get("severity", "Low")
    inc_type = incident.get("type", "Flooding")
    city     = incident.get("city", "")
    zone     = incident.get("zone", "")

    # Base action set from incident's own recommended_actions (if present)
    actions: list[str] = list(incident.get("recommended_actions", []))

    # Augment based on type
    if inc_type == "Flooding":
        if severity in ("Critical", "High"):
            actions += [
                f"Deploy rescue boats to {zone}",
                "Establish safe evacuation corridor",
                "Coordinate with SDRF/NDRF if water exceeds 1m",
            ]
        else:
            actions.append("Deploy portable pump units")
    elif inc_type == "Blocked Drain":
        actions += [
            "Send jet-cleaning vehicle to site within 2 hours",
            "Post caution signage at drain inlets",
        ]
    elif inc_type == "Waterlogging":
        actions += [
            "Deploy surface water suction pumps",
            "Check and unblock nearby storm drain grates",
        ]
    elif inc_type == "Road Closure":
        actions += [
            "Coordinate with city traffic control for alternate routes",
            "Update public navigation apps via API",
            "Install temporary dewatering pump at road low-point",
        ]

    # Severity-specific escalation
    if severity == "Critical":
        actions.append("Escalate to district collector / municipal commissioner immediately")
        escalation = True
        est_hours  = 6
    elif severity == "High":
        actions.append("Notify ward councillor and zone officer")
        escalation = True
        est_hours  = 12
    elif severity == "Medium":
        escalation = False
        est_hours  = 24
    else:
        escalation = False
        est_hours  = 48

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_actions: list[str] = []
    for a in actions:
        if a not in seen:
            seen.add(a)
            unique_actions.append(a)

    return {
        "incident_id": incident.get("incident_id"),
        "zone": zone,
        "city": city,
        "severity": severity,
        "type": inc_type,
        "recommended_actions": unique_actions,
        "escalation_required": escalation,
        "estimated_resolution_hours": est_hours,
        "agent": "Civic Response Coordination Agent",
    }


def assign_response_team(incident: dict[str, Any], all_incidents: list[dict] | None = None) -> dict[str, Any]:
    """
    Assign the best available response team for an incident.

    Uses a simple availability heuristic: teams already assigned to Critical
    incidents are considered busy; others rotate through the pool.

    Returns dict with: incident_id, assigned_team, team_status, rationale.
    """
    city     = incident.get("city", "Ahmedabad")
    severity = incident.get("severity", "Low")
    inc_type = incident.get("type", "Flooding")

    # Determine already-busy teams from concurrent incidents
    busy_teams: set[str] = set()
    if all_incidents:
        for inc in all_incidents:
            if (
                inc.get("incident_id") != incident.get("incident_id")
                and inc.get("severity") in ("Critical", "High")
                and inc.get("status") != "Resolved"
            ):
                t = inc.get("assigned_team", "")
                if t:
                    busy_teams.add(t)

    pool = TEAM_POOL.get(city, TEAM_POOL["Ahmedabad"])
    available = [t for t in pool if t not in busy_teams]

    # Specialised assignment logic
    if inc_type == "Road Closure":
        preferred = [t for t in available if "Traffic" in t or "Highway" in t]
    elif inc_type == "Blocked Drain":
        preferred = [t for t in available if "Drain" in t or "Maintenance" in t or "Crew" in t]
    elif inc_type in ("Flooding", "Waterlogging") and severity in ("Critical", "High"):
        preferred = [t for t in available if "Rapid" in t or "Rescue" in t or "Relief" in t or "Pump" in t]
    else:
        preferred = available

    team = (preferred or available or pool)[0]
    rationale = (
        f"Team '{team}' assigned based on incident type '{inc_type}' and "
        f"severity '{severity}'. {len(busy_teams)} team(s) currently occupied."
    )

    return {
        "incident_id": incident.get("incident_id"),
        "zone": incident.get("zone"),
        "assigned_team": team,
        "team_status": "Dispatched",
        "rationale": rationale,
        "agent": "Civic Response Coordination Agent",
    }


def generate_emergency_protocol(zone_data: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a full emergency response protocol for a high-risk zone.

    Returns dict with: zone, city, protocol_level, immediate_actions,
    short_term_actions, communication_plan, resource_requirements.
    """
    zone      = zone_data.get("zone_name", "Unknown")
    city      = zone_data.get("city", "Unknown")
    risk      = zone_data.get("risk_level", "Low")
    pop_den   = zone_data.get("population_density", "Medium")
    rainfall  = zone_data.get("rainfall_intensity", 0)
    blockage  = zone_data.get("drainage_blockage_level", 0)

    if risk == "Critical":
        protocol_level = "Level 4 – Full Emergency Mobilisation"
        immediate_actions = [
            "Activate City Emergency Operations Centre (EOC)",
            "Mandatory evacuation for flood-prone sub-zones",
            "Open all designated relief shelters",
            "Deploy NDRF / State Disaster Response Force",
            f"Issue Level-4 public alert via SMS, sirens, and social media for {zone}",
        ]
        short_term_actions = [
            "Continuous water-level monitoring every 15 minutes",
            "Post-event structural damage survey",
            "Coordinate with power utility to isolate hazardous circuits",
            "Deploy mobile medical units",
        ]
        resources = [
            "4× High-capacity pumps (100,000 L/hr each)",
            "2× Rescue boats with trained operators",
            "500 flood barriers",
            "Emergency shelter capacity: 2000 persons",
            "Medical team: 2 doctors, 4 paramedics",
        ]
    elif risk == "High":
        protocol_level = "Level 3 – High Alert"
        immediate_actions = [
            "Put response teams on 30-minute standby",
            f"Issue Level-3 advisory for {zone}",
            "Pre-position pumps at known flood spots",
            "Open one relief shelter as precaution",
        ]
        short_term_actions = [
            "Drain inspection and urgent unblocking",
            "Coordinate with traffic police for pre-emptive road management",
            "Monitor citizen reports feed every 30 minutes",
        ]
        resources = [
            "2× Medium-capacity pumps",
            "1× Rescue boat on standby",
            "200 sandbags",
            "Relief shelter capacity: 500 persons",
        ]
    else:
        protocol_level = "Level 2 – Watch"
        immediate_actions = [
            f"Enhanced monitoring for {zone}",
            "Inspect drains and clear visible blockages",
        ]
        short_term_actions = [
            "Issue public awareness advisory",
            "Confirm readiness of response teams",
        ]
        resources = [
            "1× Small pump unit on standby",
            "50 sandbags",
        ]

    communication_plan = [
        f"SMS blast to all registered residents of {zone} (city emergency system)",
        f"WhatsApp community broadcast – {city} Ward Officers group",
        "Press release via Ahmedabad/Surat Municipal Corporation PRO",
        "Social media post on official civic accounts (Twitter, Facebook)",
        "PA announcements via mounted loudspeakers in affected sectors",
    ]

    return {
        "zone": zone,
        "city": city,
        "risk_level": risk,
        "protocol_level": protocol_level,
        "immediate_actions": immediate_actions,
        "short_term_actions": short_term_actions,
        "communication_plan": communication_plan,
        "resource_requirements": resources,
        "context": {
            "rainfall_intensity": f"{rainfall} mm/hr",
            "drainage_blockage": f"{blockage}%",
            "population_density": pop_den,
        },
        "agent": "Civic Response Coordination Agent",
    }
