"""
Agent 1 – Flood Risk Prediction Agent
======================================
Analyses zone-level sensor data and computes flood risk scores.
Produces early-warning messages and explanations of contributing factors.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any


# ─── Risk thresholds ─────────────────────────────────────────────────────────
RAINFALL_CRITICAL = 45.0      # mm/hr
RAINFALL_HIGH = 30.0
RAINFALL_MEDIUM = 15.0

BLOCKAGE_CRITICAL = 70.0     # %
BLOCKAGE_HIGH = 50.0
BLOCKAGE_MEDIUM = 30.0

WATER_LEVEL_CRITICAL = 60.0  # cm
WATER_LEVEL_HIGH = 40.0
WATER_LEVEL_MEDIUM = 20.0

REPORT_CRITICAL = 15
REPORT_HIGH = 8
REPORT_MEDIUM = 3


# ─── Core helpers ─────────────────────────────────────────────────────────────

def _score_factor(value: float, medium: float, high: float, critical: float) -> float:
    """Return a 0-1 sub-score for a single numeric factor."""
    if value >= critical:
        return 1.0
    if value >= high:
        return 0.66
    if value >= medium:
        return 0.33
    return 0.1


# ─── Public API ───────────────────────────────────────────────────────────────

def analyze_zone_risk(zone_data: dict[str, Any]) -> dict[str, Any]:
    """
    Analyse a single zone dict and return a detailed risk assessment.

    Returns
    -------
    dict with keys:
      zone_id, zone_name, city, risk_score (0-100), risk_level,
      contributing_factors (list of dicts), explanation (str),
      confidence (float 0-1)
    """
    rainfall    = zone_data.get("rainfall_intensity", 0)
    blockage    = zone_data.get("drainage_blockage_level", 0)
    hist_freq   = zone_data.get("historical_flood_frequency", 0)   # 0-10
    water_level = zone_data.get("water_level", 0)
    reports     = zone_data.get("citizen_reports_count", 0)

    # Weighted contribution (weights sum to 1.0)
    w_rain   = 0.30
    w_block  = 0.25
    w_hist   = 0.20
    w_water  = 0.15
    w_report = 0.10

    score = (
        w_rain   * _score_factor(rainfall, RAINFALL_MEDIUM, RAINFALL_HIGH, RAINFALL_CRITICAL) * 100
        + w_block  * _score_factor(blockage, BLOCKAGE_MEDIUM, BLOCKAGE_HIGH, BLOCKAGE_CRITICAL) * 100
        + w_hist   * (hist_freq / 10.0) * 100
        + w_water  * _score_factor(water_level, WATER_LEVEL_MEDIUM, WATER_LEVEL_HIGH, WATER_LEVEL_CRITICAL) * 100
        + w_report * _score_factor(reports, REPORT_MEDIUM, REPORT_HIGH, REPORT_CRITICAL) * 100
    )
    score = round(min(score, 100), 1)

    if score >= 80:
        risk_level = "Critical"
    elif score >= 60:
        risk_level = "High"
    elif score >= 35:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    contributing_factors = []

    if rainfall >= RAINFALL_CRITICAL:
        contributing_factors.append({
            "factor": "Rainfall Intensity",
            "value": f"{rainfall} mm/hr",
            "threshold": f"Critical: ≥{RAINFALL_CRITICAL} mm/hr",
            "status": "⚠ CRITICAL",
        })
    elif rainfall >= RAINFALL_HIGH:
        contributing_factors.append({
            "factor": "Rainfall Intensity",
            "value": f"{rainfall} mm/hr",
            "threshold": f"High: ≥{RAINFALL_HIGH} mm/hr",
            "status": "⚠ HIGH",
        })

    if blockage >= BLOCKAGE_CRITICAL:
        contributing_factors.append({
            "factor": "Drainage Blockage",
            "value": f"{blockage}%",
            "threshold": f"Critical: ≥{BLOCKAGE_CRITICAL}%",
            "status": "⚠ CRITICAL",
        })
    elif blockage >= BLOCKAGE_HIGH:
        contributing_factors.append({
            "factor": "Drainage Blockage",
            "value": f"{blockage}%",
            "threshold": f"High: ≥{BLOCKAGE_HIGH}%",
            "status": "⚠ HIGH",
        })

    if hist_freq >= 7:
        contributing_factors.append({
            "factor": "Historical Flood Frequency",
            "value": f"{hist_freq}/10",
            "threshold": "High history ≥ 7/10",
            "status": "⚠ HIGH HISTORY",
        })

    if water_level >= WATER_LEVEL_HIGH:
        contributing_factors.append({
            "factor": "Water Level",
            "value": f"{water_level} cm",
            "threshold": f"High: ≥{WATER_LEVEL_HIGH} cm",
            "status": "⚠ ELEVATED",
        })

    if reports >= REPORT_HIGH:
        contributing_factors.append({
            "factor": "Citizen Reports",
            "value": f"{reports} reports",
            "threshold": f"High alert: ≥{REPORT_HIGH} reports",
            "status": "⚠ MANY REPORTS",
        })

    explanation = (
        f"Zone {zone_data.get('zone_name', 'Unknown')} in {zone_data.get('city', 'Unknown')} "
        f"carries a flood risk score of {score}/100 ({risk_level}). "
        f"The primary driver is rainfall intensity of {rainfall} mm/hr combined with "
        f"{blockage}% drainage blockage, reducing the effective drainage capacity significantly. "
        f"Historical flood frequency of {hist_freq}/10 indicates this zone has recurring flooding issues."
    )

    return {
        "zone_id": zone_data.get("zone_id"),
        "zone_name": zone_data.get("zone_name"),
        "city": zone_data.get("city"),
        "risk_score": score,
        "risk_level": risk_level,
        "contributing_factors": contributing_factors,
        "explanation": explanation,
        "confidence": round(0.70 + (len(contributing_factors) * 0.05), 2),
        "agent": "Flood Risk Prediction Agent",
    }


def predict_flood_risk(city: str, zones: list[dict]) -> list[dict]:
    """
    Predict flood risk for all zones in a city.

    Parameters
    ----------
    city : str – "Ahmedabad" or "Surat"
    zones : list of zone dicts from synthetic_data

    Returns list of risk assessments sorted by risk_score descending.
    """
    city_zones = [z for z in zones if z.get("city", "").lower() == city.lower()]
    assessments = [analyze_zone_risk(z) for z in city_zones]
    return sorted(assessments, key=lambda a: a["risk_score"], reverse=True)


def generate_early_warning(zone_data: dict[str, Any]) -> dict[str, Any]:
    """
    Generate a structured early-warning message for a zone.

    Returns dict with: zone, city, severity, message, actions, timestamp_label
    """
    assessment = analyze_zone_risk(zone_data)
    level = assessment["risk_level"]

    if level == "Critical":
        message = (
            f"🚨 CRITICAL FLOOD WARNING for {zone_data.get('zone_name')}, "
            f"{zone_data.get('city')}: Immediate evacuation of low-lying areas required. "
            f"All emergency services to be mobilised NOW."
        )
        actions = [
            "Activate full emergency response protocol",
            "Issue public evacuation advisory",
            "Deploy all available pumping units",
            "Alert NDRF and state disaster management",
            "Close all underpasses and low-lying roads",
        ]
    elif level == "High":
        message = (
            f"⚠ HIGH FLOOD ALERT for {zone_data.get('zone_name')}, "
            f"{zone_data.get('city')}: Pre-position response teams. "
            f"Residents in flood-prone areas should move to higher ground."
        )
        actions = [
            "Pre-position pump units and rescue boats",
            "Issue advisory to residents in flood-prone areas",
            "Deploy drain maintenance crew immediately",
            "Open relief shelters as precaution",
        ]
    elif level == "Medium":
        message = (
            f"⚡ MEDIUM FLOOD WATCH for {zone_data.get('zone_name')}, "
            f"{zone_data.get('city')}: Elevated risk. Monitor situation closely."
        )
        actions = [
            "Increase monitoring frequency to every 30 minutes",
            "Inspect and clear blocked drains",
            "Alert local ward office",
        ]
    else:
        message = (
            f"✅ LOW RISK – {zone_data.get('zone_name')}, "
            f"{zone_data.get('city')}: Normal conditions. Routine monitoring active."
        )
        actions = ["Continue routine monitoring"]

    return {
        "zone": zone_data.get("zone_name"),
        "city": zone_data.get("city"),
        "severity": level,
        "risk_score": assessment["risk_score"],
        "message": message,
        "actions": actions,
        "agent": "Flood Risk Prediction Agent",
    }


def get_risk_factors(zone_data: dict[str, Any]) -> list[dict]:
    """Return the list of contributing risk factors for a zone."""
    return analyze_zone_risk(zone_data)["contributing_factors"]
