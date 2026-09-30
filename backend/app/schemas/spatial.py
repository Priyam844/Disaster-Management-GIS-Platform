from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import uuid
from app.schemas.base import IDMixin
from app.models.spatial import HazardType, SeverityLevel, PriorityTier, RelocationStatus


# State Schemas
class StateBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=10)
    metadata: Dict[str, Any] = {}


class StateCreate(StateBase):
    geom: Dict[str, Any]  # GeoJSON geometry


class StateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class StateResponse(StateBase, IDMixin):
    pass


# District Schemas
class DistrictBase(BaseModel):
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    metadata: Dict[str, Any] = {}


class DistrictCreate(DistrictBase):
    state_id: uuid.UUID
    geom: Dict[str, Any]


class DistrictUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = None


class DistrictResponse(DistrictBase, IDMixin):
    state_id: uuid.UUID


# Habitation Schemas
class HabitationBase(BaseModel):
    name: str = Field(..., max_length=200)
    population: Optional[int] = None
    households: Optional[int] = None
    literacy_rate: Optional[float] = None
    pucca_houses_pct: Optional[float] = None
    sc_st_pct: Optional[float] = None
    female_headed_pct: Optional[float] = None
    disability_pct: Optional[float] = None
    road_access_km: Optional[float] = None
    healthcare_access_km: Optional[float] = None
    metadata: Dict[str, Any] = {}


class HabitationCreate(HabitationBase):
    district_id: uuid.UUID
    state_id: uuid.UUID
    geom: Dict[str, Any]  # Point geometry
    boundary_geom: Optional[Dict[str, Any]] = None


class HabitationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    population: Optional[int] = None
    households: Optional[int] = None
    literacy_rate: Optional[float] = None
    pucca_houses_pct: Optional[float] = None
    sc_st_pct: Optional[float] = None
    female_headed_pct: Optional[float] = None
    disability_pct: Optional[float] = None
    road_access_km: Optional[float] = None
    healthcare_access_km: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class HabitationResponse(HabitationBase, IDMixin):
    district_id: uuid.UUID
    state_id: uuid.UUID
    socioeconomic_vulnerability: Optional[float] = None
    physical_vulnerability: Optional[float] = None
    composite_vulnerability: Optional[float] = None
    assessed_at: Optional[datetime] = None


class HabitationListResponse(HabitationResponse):
    geom: Dict[str, Any]


# Hazard Zone Schemas
class HazardZoneBase(BaseModel):
    hazard_type: HazardType
    severity: SeverityLevel
    severity_score: Optional[float] = Field(None, ge=0, le=100)
    source: str = Field(..., max_length=100)
    model_version: Optional[str] = None
    confidence_score: Optional[float] = Field(None, ge=0, le=100)
    metadata: Dict[str, Any] = {}


class HazardZoneCreate(HazardZoneBase):
    geom: Dict[str, Any]
    valid_from: datetime
    valid_to: Optional[datetime] = None


class HazardZoneUpdate(BaseModel):
    severity: Optional[SeverityLevel] = None
    severity_score: Optional[float] = Field(None, ge=0, le=100)
    valid_to: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class HazardZoneResponse(HazardZoneBase, IDMixin):
    geom: Dict[str, Any]
    valid_from: datetime
    valid_to: Optional[datetime] = None


# Disaster Event Schemas
class DisasterEventBase(BaseModel):
    hazard_type: HazardType
    event_name: Optional[str] = None
    event_date: date
    end_date: Optional[date] = None
    affected_habitations: List[uuid.UUID] = []
    casualties: Optional[int] = None
    injured: Optional[int] = None
    displaced: Optional[int] = None
    houses_damaged: Optional[int] = None
    economic_loss_inr: Optional[int] = None
    source: Optional[str] = None
    verified: bool = False
    metadata: Dict[str, Any] = {}


class DisasterEventCreate(DisasterEventBase):
    affected_geom: Optional[Dict[str, Any]] = None


class DisasterEventUpdate(BaseModel):
    event_name: Optional[str] = None
    end_date: Optional[date] = None
    affected_habitations: Optional[List[uuid.UUID]] = None
    casualties: Optional[int] = None
    injured: Optional[int] = None
    displaced: Optional[int] = None
    houses_damaged: Optional[int] = None
    economic_loss_inr: Optional[int] = None
    source: Optional[str] = None
    verified: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class DisasterEventResponse(DisasterEventBase, IDMixin):
    affected_geom: Optional[Dict[str, Any]] = None


# Relocation Site Schemas
class RelocationSiteBase(BaseModel):
    name: str = Field(..., max_length=200)
    total_area_ha: float = Field(..., gt=0)
    buildable_area_ha: Optional[float] = None
    agricultural_area_ha: Optional[float] = None
    forest_area_ha: Optional[float] = None
    water_body_area_ha: Optional[float] = None
    water_availability_score: Optional[float] = Field(None, ge=0, le=100)
    road_access_score: Optional[float] = Field(None, ge=0, le=100)
    electricity_access: bool = False
    healthcare_facility_km: Optional[float] = None
    school_facility_km: Optional[float] = None
    market_facility_km: Optional[float] = None
    current_population: int = 0
    max_carrying_capacity: Optional[int] = None
    recommended_capacity: Optional[int] = None
    land_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    water_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    infrastructure_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    environmental_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    composite_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    flood_risk: bool = False
    landslide_risk: bool = False
    seismic_zone: Optional[int] = None
    ecological_sensitivity: Optional[str] = None
    land_ownership: Optional[str] = None
    assessment_date: date
    assessed_by: Optional[str] = None
    metadata: Dict[str, Any] = {}


class RelocationSiteCreate(RelocationSiteBase):
    district_id: uuid.UUID
    geom: Dict[str, Any]


class RelocationSiteUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=200)
    total_area_ha: Optional[float] = Field(None, gt=0)
    buildable_area_ha: Optional[float] = None
    agricultural_area_ha: Optional[float] = None
    forest_area_ha: Optional[float] = None
    water_body_area_ha: Optional[float] = None
    water_availability_score: Optional[float] = Field(None, ge=0, le=100)
    road_access_score: Optional[float] = Field(None, ge=0, le=100)
    electricity_access: Optional[bool] = None
    healthcare_facility_km: Optional[float] = None
    school_facility_km: Optional[float] = None
    market_facility_km: Optional[float] = None
    current_population: Optional[int] = None
    max_carrying_capacity: Optional[int] = None
    recommended_capacity: Optional[int] = None
    land_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    water_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    infrastructure_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    environmental_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    composite_suitability_score: Optional[float] = Field(None, ge=0, le=100)
    flood_risk: Optional[bool] = None
    landslide_risk: Optional[bool] = None
    seismic_zone: Optional[int] = None
    ecological_sensitivity: Optional[str] = None
    land_ownership: Optional[str] = None
    assessment_date: Optional[date] = None
    assessed_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class RelocationSiteResponse(RelocationSiteBase, IDMixin):
    district_id: uuid.UUID
    centroid: Dict[str, Any]


class RelocationSiteCapacityResponse(BaseModel):
    site_id: uuid.UUID
    site_name: str
    max_carrying_capacity: Optional[int]
    recommended_capacity: Optional[int]
    current_population: int
    available_capacity: int
    composite_suitability_score: Optional[float]
    assigned_habitations: int
    assigned_population: int
    capacity_breakdown: Dict[str, Any]


# Relocation Priority Schemas
class RelocationPriorityBase(BaseModel):
    habitation_id: uuid.UUID
    recommended_site_id: Optional[uuid.UUID] = None
    alternative_site_ids: List[uuid.UUID] = []
    priority_tier: PriorityTier
    priority_rank: Optional[int] = None
    hazard_exposure_score: Optional[float] = Field(None, ge=0, le=100)
    vulnerability_score: Optional[float] = Field(None, ge=0, le=100)
    capacity_gap_score: Optional[float] = Field(None, ge=0, le=100)
    distance_score: Optional[float] = Field(None, ge=0, le=100)
    cost_effectiveness_score: Optional[float] = Field(None, ge=0, le=100)
    composite_priority_score: Optional[float] = Field(None, ge=0, le=100)
    distance_to_site_km: Optional[float] = None
    estimated_relocation_cost_inr: Optional[int] = None
    estimated_timeline_months: Optional[int] = None
    status: RelocationStatus = RelocationStatus.PENDING
    approved_by: Optional[str] = None
    notes: Optional[str] = None
    model_version: Optional[str] = None


class RelocationPriorityCreate(RelocationPriorityBase):
    pass


class RelocationPriorityUpdate(BaseModel):
    recommended_site_id: Optional[uuid.UUID] = None
    alternative_site_ids: Optional[List[uuid.UUID]] = None
    priority_tier: Optional[PriorityTier] = None
    priority_rank: Optional[int] = None
    status: Optional[RelocationStatus] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    notes: Optional[str] = None


class RelocationPriorityResponse(RelocationPriorityBase, IDMixin):
    computed_at: datetime


class RelocationPriorityListResponse(RelocationPriorityResponse):
    habitation_name: str
    habitation_population: Optional[int]
    habitation_vulnerability: Optional[float]
    site_name: Optional[str] = None


# Filter/Query Schemas
class HazardZoneFilters(BaseModel):
    hazard_type: Optional[HazardType] = None
    severity: Optional[SeverityLevel] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    bbox: Optional[str] = None  # minx,miny,maxx,maxy
    valid_at: Optional[datetime] = None
    source: Optional[str] = None


class SiteFilters(BaseModel):
    district_id: Optional[uuid.UUID] = None
    state_code: Optional[str] = None
    suitability_min: Optional[float] = Field(None, ge=0, le=100)
    capacity_min: Optional[int] = Field(None, ge=0)
    risk_free: Optional[bool] = None
    available_capacity_min: Optional[int] = Field(None, ge=0)


class PrioritizationFilters(BaseModel):
    state_code: Optional[str] = None
    district_id: Optional[uuid.UUID] = None
    tier: Optional[PriorityTier] = None
    site_id: Optional[uuid.UUID] = None
    status: Optional[RelocationStatus] = None
    min_score: Optional[float] = Field(None, ge=0, le=100)


# Statistics/Analytics Schemas
class DashboardSummary(BaseModel):
    total_habitations: int
    total_population: int
    high_vulnerability_habitations: int
    active_red_zones: int
    total_relocation_sites: int
    total_capacity: int
    immediate_priority_count: int
    short_term_priority_count: int
    medium_term_priority_count: int
    population_at_risk: int


class HazardTrendPoint(BaseModel):
    date: date
    hazard_type: HazardType
    count: int
    affected_population: int


class VulnerabilityDistribution(BaseModel):
    range: str
    count: int
    percentage: float


class CapacityGapAnalysis(BaseModel):
    district_id: uuid.UUID
    district_name: str
    demand_population: int
    available_capacity: int
    gap: int
    gap_percentage: float


# Export Schemas
class ExportRequest(BaseModel):
    format: str = Field(..., pattern="^(geojson|csv|pdf)$")
    filters: Optional[Dict[str, Any]] = None