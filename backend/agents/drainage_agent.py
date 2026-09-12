"""
Agent 2 – Drainage Maintenance Scheduling Agent
================================================
Assesses drain conditions, generates prioritised maintenance schedules,
identifies critical drains, and recommends preventive actions.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime, date


# ─── Thresholds ───────────────────────────────────────────────────────────────
BLOCKAGE_URGENT   = 75.0   # %
BLOCKAGE_HIGH     = 55.0
BLOCKAGE_MEDIUM   = 35.0


def _days_since(date_str: str) -> int:
    """Return the number of days since a date string (YYYY-MM-DD)."""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (date.today() - d).days
    except Exception:
        return 0


def _priority_score(drain: dict[str, Any]) -> float:
    """
    Compute a composite urgency score (higher = more urgent).
    Factors: blockage %, days since maintenance, condition rating.
    """
    blockage = drain.get("blockage_percentage", 0)
    days_old  = _days_since(drain.get("last_maintenance", "2025-01-01"))

    condition_map = {"Critical": 1.0, "Poor": 0.75, "Fair": 0.5, "Good": 0.25}
    cond_score = condition_map.get(drain.get("condition", "Good"), 0.25)

    # blockage weight 0.5, age weight 0.3, condition weight 0.2
    age_norm = min(days_old / 365.0, 1.0)
    return round(0.5 * (blockage / 100.0) + 0.3 * age_norm + 0.2 * cond_score, 4)


# ─── Public API ───────────────────────────────────────────────────────────────

def assess_drain_condition(drain: dict[str, Any]) -> dict[str, Any]:
    """
    Assess a single drain and return a condition report.

    Returns dict with: drain_id, location, condition, blockage_percentage,
    days_since_maintenance, urgency_score, recommended_action, notes.
    """
    blockage       = drain.get("blockage_percentage", 0)
    condition      = drain.get("condition", "Good")
    days_since_mnt = _days_since(drain.get("last_maintenance", "2025-01-01"))
    urgency        = _priority_score(drain)

    if condition == "Critical" or blockage >= BLOCKAGE_URGENT:
        recommended_action = "EMERGENCY cleaning – deploy jet-cleaning vehicle within 24 hours"
        status = "Urgent"
    elif condition == "Poor" or blockage >= BLOCKAGE_HIGH:
        recommended_action = "Schedule cleaning within 72 hours"
        status = "High Priority"
    elif condition == "Fair" or blockage >= BLOCKAGE_MEDIUM:
        recommended_action = "Schedule routine cleaning within 2 weeks"
        status = "Medium Priority"
    else:
        recommended_action = "Routine inspection at next scheduled maintenance"
        status = "Normal"

    notes = []
    if days_since_mnt > 180:
        notes.append(f"Last maintained {days_since_mnt} days ago – overdue by {days_since_mnt - 90} days.")
    if blockage >= BLOCKAGE_URGENT:
        notes.append("Blockage exceeds 75%: high risk of overflow during monsoon rainfall.")
    if condition == "Critical":
        notes.append("Structural assessment recommended before cleaning.")

    return {
        "drain_id": drain.get("drain_id"),
        "location": drain.get("location"),
        "city": drain.get("city"),
        "condition": condition,
        "blockage_percentage": blockage,
        "days_since_maintenance": days_since_mnt,
        "urgency_score": urgency,
        "status": status,
        "recommended_action": recommended_action,
        "notes": notes,
        "agent": "Drainage Maintenance Scheduling Agent",
    }


def generate_maintenance_schedule(city: str, drains: list[dict]) -> list[dict]:
    """
    Generate a prioritised maintenance schedule for all drains in a city.

    Returns list of drain condition reports sorted by urgency_score descending.
    """
    city_drains = [d for d in drains if d.get("city", "").lower() == city.lower()]
    reports = [assess_drain_condition(d) for d in city_drains]
    return sorted(reports, key=lambda r: r["urgency_score"], reverse=True)


def identify_critical_drains(drains: list[dict]) -> list[dict]:
    """
    Return all drains that require urgent or high-priority attention across both cities.
    """
    urgent = []
    for d in drains:
        report = assess_drain_condition(d)
        if report["status"] in ("Urgent", "High Priority"):
            urgent.append(report)
    return sorted(urgent, key=lambda r: r["urgency_score"], reverse=True)


def recommend_preventive_action(zone_data: dict[str, Any], drains: list[dict]) -> dict[str, Any]:
    """
    Given a zone, identify drains in that zone and recommend preventive actions.

    Returns dict with: zone, city, drain_count, critical_count, actions, schedule_summary.
    """
    zone_name = zone_data.get("zone_name", "")
    city      = zone_data.get("city", "")
    blockage  = zone_data.get("drainage_blockage_level", 0)
    rainfall  = zone_data.get("rainfall_intensity", 0)

    # Find drains in the same zone (by matching city and partial location string)
    zone_drains = [
        d for d in drains
        if d.get("city", "").lower() == city.lower()
        and zone_name.lower() in d.get("location", "").lower()
    ]

    critical_count = len([d for d in zone_drains if d.get("condition") in ("Critical", "Poor")])

    actions = []

    if rainfall > 35 and blockage > 60:
        actions.append(f"IMMEDIATE: Deploy emergency pump units to {zone_name}")
        actions.append("Dispatch jet-cleaning vehicle to clear primary storm drains")
        actions.append("Install temporary flood barriers at low-lying entry points")
    elif rainfall > 20 or blockage > 40:
        actions.append(f"Schedule drain cleaning in {zone_name} within next 48 hours")
        actions.append("Inspect all roadside culverts for debris accumulation")
        actions.append("Issue advisory to residents about drain blockage risks")
    else:
        actions.append(f"Routine monthly inspection scheduled for {zone_name} drains")
        actions.append("Clear any visible debris from drain inlets")

    # Add vegetation/seasonal recommendation
    actions.append("Remove monsoon debris (plastic, vegetation) from drain inlets")
    if blockage > 50:
        actions.append("Consider installing drain mesh guards to reduce blockage recurrence")

    schedule_summary = (
        f"Zone {zone_name} has {len(zone_drains)} monitored drain(s); "
        f"{critical_count} require urgent attention. "
        f"Current zone blockage level: {blockage}%. "
        f"Preventive cleaning would reduce overflow risk by an estimated 40-60%."
    )

    return {
        "zone": zone_name,
        "city": city,
        "drain_count": len(zone_drains),
        "critical_count": critical_count,
        "recommended_actions": actions,
        "schedule_summary": schedule_summary,
        "agent": "Drainage Maintenance Scheduling Agent",
    }
