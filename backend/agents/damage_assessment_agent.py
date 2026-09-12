"""
Agent 6 – Post-Disaster Damage Assessment Agent
================================================
Assesses post-flood damage, categorises it, generates recovery priorities,
and produces a full post-disaster assessment report.

NOTE: All outputs are clearly labelled DEMO DATA – Not official predictions.
"""

from __future__ import annotations
from typing import Any
from datetime import datetime


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# ─── Damage estimation tables ────────────────────────────────────────────────
# (₹ per affected zone – rough indicative values for demo purposes)
DAMAGE_ESTIMATES = {
    "Critical": {"infrastructure": 5_00_00_000, "property": 3_00_00_000, "economic_loss": 2_00_00_000},
    "High":     {"infrastructure": 2_00_00_000, "property": 1_00_00_000, "economic_loss": 75_00_000},
    "Medium":   {"infrastructure": 50_00_000,   "property": 25_00_000,   "economic_loss": 15_00_000},
    "Low":      {"infrastructure": 10_00_000,   "property": 5_00_000,    "economic_loss": 2_00_000},
}


def _inr(amount: int) -> str:
    """Format an integer as Indian Rupees shorthand."""
    if amount >= 1_00_00_000:
        return f"₹{amount / 1_00_00_000:.1f} Cr"
    if amount >= 1_00_000:
        return f"₹{amount / 1_00_000:.1f} L"
    return f"₹{amount:,}"


# ─── Public API ───────────────────────────────────────────────────────────────

def assess_damage(zone_data: dict[str, Any]) -> dict[str, Any]:
    """
    Estimate damage for a single zone based on its flood risk level and water level.

    Returns dict with: zone, city, risk_level, damage_estimates, affected_population_pct,
    infrastructure_score, recovery_time_days, agent.
    """
    risk_level  = zone_data.get("risk_level", "Low")
    water_level = zone_data.get("water_level", 0)
    pop_density = zone_data.get("population_density", "Medium")

    estimates = DAMAGE_ESTIMATES.get(risk_level, DAMAGE_ESTIMATES["Low"]).copy()

    # Scale by water level severity
    if water_level > 60:
        scale = 1.5
    elif water_level > 40:
        scale = 1.2
    else:
        scale = 1.0

    estimates = {k: int(v * scale) for k, v in estimates.items()}

    # Affected population % based on density
    pop_pct_map = {"Very High": 65, "High": 45, "Medium": 25, "Low": 10}
    affected_pop_pct = pop_pct_map.get(pop_density, 25)

    # Recovery time estimate
    recovery_days_map = {"Critical": 30, "High": 14, "Medium": 7, "Low": 3}
    recovery_days = recovery_days_map.get(risk_level, 7)
    if water_level > 50:
        recovery_days = int(recovery_days * 1.5)

    # Infrastructure damage score 0-100
    infra_score_map = {"Critical": 85, "High": 60, "Medium": 30, "Low": 10}
    infra_score = infra_score_map.get(risk_level, 10)

    return {
        "zone": zone_data.get("zone_name"),
        "city": zone_data.get("city"),
        "risk_level": risk_level,
        "water_level_cm": water_level,
        "damage_estimates": {
            "infrastructure": _inr(estimates["infrastructure"]),
            "property": _inr(estimates["property"]),
            "economic_loss": _inr(estimates["economic_loss"]),
            "total": _inr(sum(estimates.values())),
        },
        "damage_estimates_raw": estimates,
        "affected_population_pct": affected_pop_pct,
        "infrastructure_damage_score": infra_score,
        "estimated_recovery_days": recovery_days,
        "agent": "Post-Disaster Damage Assessment Agent",
    }


def categorize_damage(incidents: list[dict]) -> list[dict]:
    """
    Categorise damage by incident type across all incidents.

    Returns list of category dicts: type, count, severity_distribution, pct_active.
    """
    type_map: dict[str, dict] = {}

    for inc in incidents:
        inc_type = inc.get("type", "Unknown")
        severity = inc.get("severity", "Low")
        status   = inc.get("status", "Active")

        if inc_type not in type_map:
            type_map[inc_type] = {
                "type": inc_type,
                "count": 0,
                "severity_dist": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "active": 0,
            }
        type_map[inc_type]["count"] += 1
        type_map[inc_type]["severity_dist"][severity] = (
            type_map[inc_type]["severity_dist"].get(severity, 0) + 1
        )
        if status != "Resolved":
            type_map[inc_type]["active"] += 1

    result = []
    for entry in type_map.values():
        total = entry["count"]
        entry["pct_active"] = round(entry["active"] / total * 100, 1) if total else 0
        result.append(entry)

    return sorted(result, key=lambda x: x["count"], reverse=True)


def generate_recovery_plan(affected_zones: list[dict]) -> list[dict]:
    """
    Generate a prioritised recovery plan for affected zones.

    Returns list of recovery actions sorted by priority (Critical zones first).
    """
    priority_map = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
    actions = []

    for z in affected_zones:
        risk = z.get("risk_level", "Low")
        zone = z.get("zone_name", "Unknown")
        city = z.get("city", "Unknown")

        base_actions = []
        if risk == "Critical":
            base_actions = [
                f"Emergency structural inspection of all flood-damaged buildings in {zone}",
                f"Restore road connectivity in {zone} – priority repairs to NH/SH access points",
                f"Dewater residential and commercial premises in {zone}",
                f"Distribute clean water and emergency rations to {zone} residents",
                f"Activate temporary housing for displaced families in {zone}",
            ]
        elif risk == "High":
            base_actions = [
                f"Assess and repair drainage infrastructure in {zone}",
                f"Clean and disinfect flood-affected premises in {zone}",
                f"Restore power supply to flooded areas in {zone}",
            ]
        else:
            base_actions = [
                f"Routine post-flood cleaning in {zone}",
                f"Inspect and document minor damage in {zone} for insurance purposes",
            ]

        actions.append({
            "zone": zone,
            "city": city,
            "risk_level": risk,
            "priority": priority_map.get(risk, 4),
            "recovery_actions": base_actions,
            "estimated_recovery_days": assess_damage(z)["estimated_recovery_days"],
        })

    return sorted(actions, key=lambda a: a["priority"])


def create_post_disaster_report(
    zones: list[dict],
    incidents: list[dict],
    drains: list[dict],
) -> str:
    """
    Create a comprehensive post-disaster assessment report as plain text.
    """
    affected_zones = [z for z in zones if z.get("risk_level") in ("Critical", "High")]
    damage_reports = [assess_damage(z) for z in affected_zones]
    categories     = categorize_damage(incidents)
    recovery_plan  = generate_recovery_plan(affected_zones)

    total_infra = sum(r["damage_estimates_raw"]["infrastructure"] for r in damage_reports)
    total_prop  = sum(r["damage_estimates_raw"]["property"]        for r in damage_reports)
    total_econ  = sum(r["damage_estimates_raw"]["economic_loss"]   for r in damage_reports)
    grand_total = total_infra + total_prop + total_econ

    report_lines = [
        "=" * 60,
        " POST-FLOOD DAMAGE ASSESSMENT REPORT",
        " [DEMO DATA – Not official predictions]",
        f" Generated: {_now_str()}",
        " Powered by: IBM Granite LLM (DEMO)",
        "=" * 60,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 40,
        f"Total Affected Zones    : {len(affected_zones)} (Critical + High Risk)",
        f"Total Active Incidents  : {len([i for i in incidents if i.get('status') != 'Resolved'])}",
        f"Critical Drains         : {len([d for d in drains if d.get('condition') == 'Critical'])}",
        "",
        "ESTIMATED DAMAGE (INDICATIVE – DEMO ONLY)",
        "-" * 40,
        f"  Infrastructure Damage : {_inr(total_infra)}",
        f"  Property Damage       : {_inr(total_prop)}",
        f"  Economic Losses       : {_inr(total_econ)}",
        f"  GRAND TOTAL           : {_inr(grand_total)}",
        "",
        "ZONE-WISE DAMAGE BREAKDOWN",
        "-" * 40,
    ]

    for dr in damage_reports:
        report_lines.append(
            f"  {dr['zone']} ({dr['city']}) – {dr['risk_level']}: "
            f"Total {dr['damage_estimates']['total']}, "
            f"Recovery: ~{dr['estimated_recovery_days']} days"
        )

    report_lines += [
        "",
        "INCIDENT CATEGORIES",
        "-" * 40,
    ]
    for cat in categories:
        report_lines.append(
            f"  {cat['type']}: {cat['count']} incidents "
            f"({cat['pct_active']}% still active)"
        )

    report_lines += [
        "",
        "RECOVERY PRIORITY PLAN",
        "-" * 40,
    ]
    for p in recovery_plan[:5]:
        report_lines.append(f"  [{p['risk_level']}] {p['zone']}, {p['city']}:")
        for action in p["recovery_actions"][:2]:
            report_lines.append(f"    - {action}")

    report_lines += [
        "",
        "=" * 60,
        " Report generated by Post-Disaster Damage Assessment Agent",
        " Integrated via IBM Granite LLM (Simulated for DEMO)",
        "=" * 60,
    ]

    return "\n".join(report_lines)
