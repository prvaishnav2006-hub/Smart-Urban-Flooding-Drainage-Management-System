"""
Data models for the Smart Urban Flooding & Drainage Management System.
Pydantic models used for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enumerations ────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class DrainCondition(str, Enum):
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"


class IncidentSeverity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class IncidentStatus(str, Enum):
    ACTIVE = "Active"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"


class IncidentType(str, Enum):
    FLOODING = "Flooding"
    BLOCKED_DRAIN = "Blocked Drain"
    WATERLOGGING = "Waterlogging"
    ROAD_CLOSURE = "Road Closure"


class TrafficCondition(str, Enum):
    NORMAL = "Normal"
    SLOW = "Slow"
    HEAVY = "Heavy"
    BLOCKED = "Blocked"


class PopulationDensity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    VERY_HIGH = "Very High"


class MaintenanceStatus(str, Enum):
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"
    CRITICAL = "Critical"


# ─── Domain Models ────────────────────────────────────────────────────────────

class Zone(BaseModel):
    zone_id: str
    city: str
    zone_name: str
    lat: float
    lon: float
    rainfall_intensity: float          # mm/hr
    historical_flood_frequency: float  # 0-10 scale
    drainage_capacity: float           # percentage
    drainage_blockage_level: float     # percentage
    water_level: float                 # cm
    traffic_condition: TrafficCondition
    population_density: PopulationDensity
    citizen_reports_count: int
    flood_risk_score: float            # 0-100
    risk_level: RiskLevel
    maintenance_status: MaintenanceStatus
    last_maintenance_date: str


class Drain(BaseModel):
    drain_id: str
    city: str
    location: str
    capacity_rating: str               # e.g. "High", "Medium", "Low"
    blockage_percentage: float
    condition: DrainCondition
    last_maintenance: str
    maintenance_due: str
    priority_level: str
    lat: float
    lon: float


class Incident(BaseModel):
    incident_id: str
    city: str
    zone: str
    location: str
    severity: IncidentSeverity
    type: IncidentType
    status: IncidentStatus
    assigned_team: str
    reported_time: str
    description: str
    recommended_actions: List[str]


# ─── API Request/Response Models ──────────────────────────────────────────────

class CitizenReport(BaseModel):
    city: str
    zone: str
    flood_severity: str
    water_level_cm: float
    blocked_drain: bool
    description: str
    timestamp: Optional[str] = None


class AIAssistantQuery(BaseModel):
    question: str
    city: Optional[str] = None


class AIAssistantResponse(BaseModel):
    answer: str
    reasoning: str
    recommended_actions: List[str]
    confidence: float
    source: str                        # "IBM Granite LLM" or "[DEMO - Simulated Granite Response]"
    agent_used: str


class ScenarioTriggerResponse(BaseModel):
    status: str
    steps: List[dict]
    affected_zones: List[str]
    triggered_agents: List[str]
    message: str


class DamageAssessmentResponse(BaseModel):
    status: str
    affected_areas: List[dict]
    damage_categories: List[dict]
    recovery_priorities: List[dict]
    report_text: str
    total_estimated_damage: str
