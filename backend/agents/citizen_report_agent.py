"""
Agent 4 – Citizen Flood Reporting Agent
========================================
Validates and categorises citizen-submitted flood reports, detects duplicates,
and forwards critical reports to the Civic Response Agent.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime


# ─── Severity mapping from user-selected dropdown values ─────────────────────
SEVERITY_LABELS = {
    "minor":    "Low",
    "moderate": "Medium",
    "severe":   "High",
    "critical": "Critical",
}

# Water level cm thresholds for auto-upgrading severity
WATER_UPGRADE_HIGH     = 40.0  # cm → at least "High"
WATER_UPGRADE_CRITICAL = 70.0  # cm → "Critical"


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── Public API ───────────────────────────────────────────────────────────────

def analyze_report(report_data: dict[str, Any]) -> dict[str, Any]:
    """
    Categorise and enrich a raw citizen report.

    Input keys expected: city, zone, flood_severity, water_level_cm,
    blocked_drain (bool), description, timestamp (optional).

    Returns enriched report dict with: report_id, severity_final, category,
    action_required, confidence, timestamp, agent.
    """
    city          = report_data.get("city", "Unknown")
    zone          = report_data.get("zone", "Unknown")
    severity_raw  = str(report_data.get("flood_severity", "minor")).lower()
    water_level   = float(report_data.get("water_level_cm", 0))
    blocked_drain = bool(report_data.get("blocked_drain", False))
    description   = str(report_data.get("description", ""))
    timestamp     = report_data.get("timestamp") or _now_str()

    # Base severity
    severity = SEVERITY_LABELS.get(severity_raw, "Low")

    # Auto-upgrade based on water level
    if water_level >= WATER_UPGRADE_CRITICAL:
        severity = "Critical"
    elif water_level >= WATER_UPGRADE_HIGH and severity in ("Low", "Medium"):
        severity = "High"

    # Determine category
    if blocked_drain and water_level > 20:
        category = "Flooding + Blocked Drain"
    elif blocked_drain:
        category = "Blocked Drain"
    elif water_level > 20:
        category = "Waterlogging / Flooding"
    else:
        category = "General Water Accumulation"

    # Determine if immediate action is required
    action_required = severity in ("High", "Critical")

    # Confidence based on completeness
    filled_fields = sum([
        bool(city and city != "Unknown"),
        bool(zone and zone != "Unknown"),
        bool(description),
        water_level > 0,
    ])
    confidence = 0.50 + (filled_fields * 0.10)

    report_id = f"CR-{city[:3].upper()}-{datetime.now().strftime('%H%M%S')}"

    return {
        "report_id": report_id,
        "city": city,
        "zone": zone,
        "severity_submitted": SEVERITY_LABELS.get(severity_raw, severity_raw),
        "severity_final": severity,
        "category": category,
        "water_level_cm": water_level,
        "blocked_drain": blocked_drain,
        "description": description,
        "timestamp": timestamp,
        "action_required": action_required,
        "confidence": round(confidence, 2),
        "agent": "Citizen Flood Reporting Agent",
    }


def detect_duplicates(report: dict[str, Any], existing_reports: list[dict]) -> dict[str, Any]:
    """
    Check whether an incoming report is a likely duplicate of an existing one.

    Two reports are considered duplicates when they share the same city + zone
    and were filed within 30 minutes of each other.

    Returns dict with: is_duplicate (bool), matched_report_id (str | None),
    reason (str).
    """
    city  = report.get("city", "").lower()
    zone  = report.get("zone", "").lower()

    try:
        ts_new = datetime.fromisoformat(report.get("timestamp", _now_str()))
    except ValueError:
        ts_new = datetime.now()

    for existing in existing_reports:
        if (
            existing.get("city", "").lower() == city
            and existing.get("zone", "").lower() == zone
        ):
            try:
                ts_old = datetime.fromisoformat(existing.get("timestamp", "2000-01-01T00:00:00"))
            except ValueError:
                continue
            diff_minutes = abs((ts_new - ts_old).total_seconds()) / 60.0
            if diff_minutes <= 30:
                return {
                    "is_duplicate": True,
                    "matched_report_id": existing.get("report_id") or existing.get("incident_id"),
                    "reason": (
                        f"A report for {zone.title()}, {city.title()} was already filed "
                        f"{int(diff_minutes)} minute(s) ago. Merging with existing record."
                    ),
                    "agent": "Citizen Flood Reporting Agent",
                }

    return {
        "is_duplicate": False,
        "matched_report_id": None,
        "reason": "No duplicate found – new unique report.",
        "agent": "Citizen Flood Reporting Agent",
    }


def validate_severity(report: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and potentially override the user-selected severity using objective criteria.

    Returns dict with: original_severity, validated_severity, adjusted (bool), reason.
    """
    original   = SEVERITY_LABELS.get(str(report.get("flood_severity", "minor")).lower(), "Low")
    water_lvl  = float(report.get("water_level_cm", 0))
    blocked    = bool(report.get("blocked_drain", False))

    validated  = original
    adjusted   = False
    reasons    = []

    if water_lvl >= WATER_UPGRADE_CRITICAL and original != "Critical":
        validated = "Critical"
        adjusted  = True
        reasons.append(f"Water level {water_lvl} cm exceeds critical threshold (≥{WATER_UPGRADE_CRITICAL} cm)")

    elif water_lvl >= WATER_UPGRADE_HIGH and original in ("Low", "Medium"):
        validated = "High"
        adjusted  = True
        reasons.append(f"Water level {water_lvl} cm exceeds High threshold (≥{WATER_UPGRADE_HIGH} cm)")

    if blocked and water_lvl > 30 and validated == "Low":
        validated = "Medium"
        adjusted  = True
        reasons.append("Blocked drain combined with waterlogging upgraded from Low to Medium")

    return {
        "original_severity": original,
        "validated_severity": validated,
        "adjusted": adjusted,
        "reason": "; ".join(reasons) if reasons else "Severity confirmed as reported.",
        "agent": "Citizen Flood Reporting Agent",
    }


def forward_to_civic_agent(report: dict[str, Any]) -> dict[str, Any]:
    """
    Decide whether a citizen report should be forwarded to the Civic Response Agent.
    Returns a forwarding decision with the transformed incident payload.

    When forwarded, returns a dict ready to be passed to civic_response_agent
    as a new incident.
    """
    enriched = analyze_report(report)

    if not enriched["action_required"]:
        return {
            "forwarded": False,
            "reason": f"Severity '{enriched['severity_final']}' does not meet forwarding threshold (High / Critical).",
            "report_id": enriched["report_id"],
            "agent": "Citizen Flood Reporting Agent",
        }

    # Build a minimal incident dict compatible with civic_response_agent
    incident_payload = {
        "incident_id": enriched["report_id"],
        "city": enriched["city"],
        "zone": enriched["zone"],
        "location": f"{enriched['zone']}, {enriched['city']} (Citizen Report)",
        "severity": enriched["severity_final"],
        "type": "Flooding" if "Flood" in enriched["category"] else "Blocked Drain",
        "status": "Active",
        "assigned_team": "Pending Assignment",
        "reported_time": enriched["timestamp"],
        "description": enriched["description"],
        "recommended_actions": [],
        "source": "citizen_report",
    }

    return {
        "forwarded": True,
        "reason": f"Severity '{enriched['severity_final']}' meets forwarding threshold. Incident created.",
        "report_id": enriched["report_id"],
        "incident_payload": incident_payload,
        "agent": "Citizen Flood Reporting Agent",
    }
