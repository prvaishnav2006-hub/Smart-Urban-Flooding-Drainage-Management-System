"""
Agent 5 – Urban Resilience Dashboard Agent
===========================================
Aggregates data from all other agents to produce city-level summaries,
dashboard KPIs, situation reports, and active alerts.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── Public API ───────────────────────────────────────────────────────────────

def get_city_summary(city: str, zones: list[dict], incidents: list[dict], drains: list[dict]) -> dict[str, Any]:
    """
    Produce an overall city-level status summary.

    Returns dict with: city, overall_risk, zone_breakdown, incident_breakdown,
    drain_breakdown, top_concern, summary_text, generated_at.
    """
    city_zones    = [z for z in zones    if z.get("city", "").lower() == city.lower()]
    city_incidents = [i for i in incidents if i.get("city", "").lower() == city.lower()]
    city_drains   = [d for d in drains   if d.get("city", "").lower() == city.lower()]

    # Zone risk breakdown
    zone_breakdown = {
        "Critical": len([z for z in city_zones if z.get("risk_level") == "Critical"]),
        "High":     len([z for z in city_zones if z.get("risk_level") == "High"]),
        "Medium":   len([z for z in city_zones if z.get("risk_level") == "Medium"]),
        "Low":      len([z for z in city_zones if z.get("risk_level") == "Low"]),
    }

    # Incident breakdown
    inc_breakdown = {
        "Active":      len([i for i in city_incidents if i.get("status") == "Active"]),
        "In Progress": len([i for i in city_incidents if i.get("status") == "In Progress"]),
        "Resolved":    len([i for i in city_incidents if i.get("status") == "Resolved"]),
        "Critical":    len([i for i in city_incidents if i.get("severity") == "Critical"]),
    }

    # Drain breakdown
    drain_breakdown = {
        "Critical": len([d for d in city_drains if d.get("condition") == "Critical"]),
        "Poor":     len([d for d in city_drains if d.get("condition") == "Poor"]),
        "Fair":     len([d for d in city_drains if d.get("condition") == "Fair"]),
        "Good":     len([d for d in city_drains if d.get("condition") == "Good"]),
    }

    # Overall city risk
    if zone_breakdown["Critical"] >= 3 or inc_breakdown["Critical"] >= 3:
        overall_risk = "Critical"
    elif zone_breakdown["Critical"] >= 1 or zone_breakdown["High"] >= 3:
        overall_risk = "High"
    elif zone_breakdown["High"] >= 1 or zone_breakdown["Medium"] >= 3:
        overall_risk = "Medium"
    else:
        overall_risk = "Low"

    # Identify top concern zone
    if city_zones:
        top_zone = max(city_zones, key=lambda z: z.get("flood_risk_score", 0))
        top_concern = f"{top_zone['zone_name']} (Risk Score: {top_zone['flood_risk_score']}/100)"
    else:
        top_concern = "N/A"

    total_reports = sum(z.get("citizen_reports_count", 0) for z in city_zones)

    summary_text = (
        f"[DEMO DATA] {city} Flood Situation Summary – {_now_str()}\n"
        f"Overall Risk: {overall_risk}\n"
        f"Critical Zones: {zone_breakdown['Critical']} | High Zones: {zone_breakdown['High']}\n"
        f"Active Incidents: {inc_breakdown['Active']} | Critical Incidents: {inc_breakdown['Critical']}\n"
        f"Critical Drains: {drain_breakdown['Critical']} | Poor Drains: {drain_breakdown['Poor']}\n"
        f"Citizen Reports: {total_reports}\n"
        f"Top Concern: {top_concern}"
    )

    return {
        "city": city,
        "overall_risk": overall_risk,
        "zone_breakdown": zone_breakdown,
        "incident_breakdown": inc_breakdown,
        "drain_breakdown": drain_breakdown,
        "total_citizen_reports": total_reports,
        "top_concern": top_concern,
        "summary_text": summary_text,
        "generated_at": _now_str(),
        "agent": "Urban Resilience Dashboard Agent",
    }


def get_dashboard_metrics(zones: list[dict], incidents: list[dict], drains: list[dict]) -> dict[str, Any]:
    """
    Compute all KPIs for the dashboard home screen.

    Returns a flat dict of counts and averages used by frontend cards.
    """
    active_incidents   = len([i for i in incidents if i.get("status") != "Resolved"])
    critical_zones     = len([z for z in zones     if z.get("risk_level") == "Critical"])
    high_zones         = len([z for z in zones     if z.get("risk_level") == "High"])
    critical_drains    = len([d for d in drains    if d.get("condition") == "Critical"])
    total_reports      = sum(z.get("citizen_reports_count", 0) for z in zones)

    avg_rainfall = round(
        sum(z.get("rainfall_intensity", 0) for z in zones) / max(len(zones), 1), 1
    )
    avg_blockage = round(
        sum(z.get("drainage_blockage_level", 0) for z in zones) / max(len(zones), 1), 1
    )

    ahm_risk = "High"
    srt_risk = "Critical"

    # Risk distribution for donut chart
    risk_dist = {
        "Low":      len([z for z in zones if z.get("risk_level") == "Low"]),
        "Medium":   len([z for z in zones if z.get("risk_level") == "Medium"]),
        "High":     len([z for z in zones if z.get("risk_level") == "High"]),
        "Critical": len([z for z in zones if z.get("risk_level") == "Critical"]),
    }

    # Incident status distribution for bar chart
    inc_status = {
        "Active":      len([i for i in incidents if i.get("status") == "Active"]),
        "In Progress": len([i for i in incidents if i.get("status") == "In Progress"]),
        "Resolved":    len([i for i in incidents if i.get("status") == "Resolved"]),
    }

    return {
        "active_incidents":    active_incidents,
        "critical_zones":      critical_zones,
        "high_risk_zones":     critical_zones + high_zones,
        "current_rainfall":    avg_rainfall,
        "critical_drains":     critical_drains,
        "active_response_teams": 8,
        "citizen_reports":     total_reports,
        "avg_drainage_blockage": avg_blockage,
        "ahmedabad_risk":      ahm_risk,
        "surat_risk":          srt_risk,
        "risk_distribution":   risk_dist,
        "incident_status":     inc_status,
        "generated_at":        _now_str(),
        "agent": "Urban Resilience Dashboard Agent",
    }


def generate_situation_report(
    zones: list[dict],
    incidents: list[dict],
    drains: list[dict],
) -> str:
    """
    Generate a human-readable plain-text situation report for both cities.
    """
    ahm = get_city_summary("Ahmedabad", zones, incidents, drains)
    srt = get_city_summary("Surat",     zones, incidents, drains)

    total_active = len([i for i in incidents if i.get("status") != "Resolved"])
    critical_zones_all = [z for z in zones if z.get("risk_level") == "Critical"]

    report = (
        f"=== SMART URBAN FLOOD MANAGEMENT – SITUATION REPORT ===\n"
        f"[DEMO DATA – Not official predictions]\n"
        f"Generated: {_now_str()}\n\n"
        f"── AHMEDABAD ──────────────────────────────────────\n"
        f"{ahm['summary_text']}\n\n"
        f"── SURAT ──────────────────────────────────────────\n"
        f"{srt['summary_text']}\n\n"
        f"── COMBINED STATISTICS ────────────────────────────\n"
        f"Total Active Incidents : {total_active}\n"
        f"Critical Zones (both)  : {len(critical_zones_all)}\n"
        f"Critical Drains (both) : {len([d for d in drains if d.get('condition') == 'Critical'])}\n"
        f"Active Response Teams  : 8\n\n"
        f"── CRITICAL ZONES ─────────────────────────────────\n"
    )
    for z in critical_zones_all:
        report += (
            f"  • {z['zone_name']} ({z['city']}) – "
            f"Risk Score: {z['flood_risk_score']}, "
            f"Rainfall: {z['rainfall_intensity']} mm/hr, "
            f"Blockage: {z['drainage_blockage_level']}%\n"
        )
    report += "\nPowered by IBM Granite LLM (DEMO) – Urban Resilience Dashboard Agent\n"
    return report


def get_alerts(zones: list[dict], incidents: list[dict]) -> list[dict]:
    """
    Compile a list of active alerts from zone risk assessments and incident data.

    Returns list of alert dicts sorted by severity.
    """
    alerts: list[dict] = []
    severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

    # Zone-based alerts
    for z in zones:
        if z.get("risk_level") in ("Critical", "High"):
            alerts.append({
                "alert_id": f"ALT-{z['zone_id']}",
                "type": "Zone Risk Alert",
                "city": z["city"],
                "zone": z["zone_name"],
                "severity": z["risk_level"],
                "message": (
                    f"{z['zone_name']} ({z['city']}) is at {z['risk_level']} flood risk. "
                    f"Rainfall: {z['rainfall_intensity']} mm/hr | Blockage: {z['drainage_blockage_level']}%"
                ),
                "timestamp": _now_str(),
                "source": "Flood Risk Prediction Agent",
            })

    # Incident-based alerts
    for inc in incidents:
        if inc.get("status") != "Resolved" and inc.get("severity") in ("Critical", "High"):
            alerts.append({
                "alert_id": f"ALT-{inc['incident_id']}",
                "type": "Active Incident",
                "city": inc["city"],
                "zone": inc["zone"],
                "severity": inc["severity"],
                "message": (
                    f"{inc['type']} at {inc['location']} – {inc['severity']} severity. "
                    f"Status: {inc['status']}. Team: {inc['assigned_team']}."
                ),
                "timestamp": inc.get("reported_time", _now_str()),
                "source": "Civic Response Coordination Agent",
            })

    return sorted(alerts, key=lambda a: severity_order.get(a["severity"], 3))
