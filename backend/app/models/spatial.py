import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Integer, BigInteger, DateTime, Date, 
    ForeignKey, UniqueConstraint, Index, JSON, Enum as SQLEnum,
    ARRAY, DECIMAL, Boolean, func
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry
from app.models.base import BaseModel
import enum


class HazardType(str, enum.Enum):
    LANDSLIDE = "LANDSLIDE"
    FLOOD = "FLOOD"
    COASTAL_EROSION = "COASTAL_EROSION"
    CLOUDBURST = "CLOUDBURST"
    EARTHQUAKE = "EARTHQUAKE"


class SeverityLevel(str, enum.Enum):
    VERY_LOW = "VERY_LOW"
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class PriorityTier(str, enum.Enum):
    IMMEDIATE = "IMMEDIATE"
    SHORT_TERM = "SHORT_TERM"
    MEDIUM_TERM = "MEDIUM_TERM"
    NOT_REQUIRED = "NOT_REQUIRED"


class RelocationStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"


class ModelStatus(str, enum.Enum):
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"
    ARCHIVED = "ARCHIVED"


class IngestionStatus(str, enum.Enum):
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"


class State(BaseModel):
    __tablename__ = "states"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    districts: Mapped[List["District"]] = relationship(
        "District", back_populates="state", cascade="all, delete-orphan"
    )
    habitations: Mapped[List["Habitation"]] = relationship(
        "Habitation", back_populates="state", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_states_geom", "geom", postgresql_using="gist"),
    )


class District(BaseModel):
    __tablename__ = "districts"
    
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="MULTIPOLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    state: Mapped["State"] = relationship("State", back_populates="districts")
    habitations: Mapped[List["Habitation"]] = relationship(
        "Habitation", back_populates="district", cascade="all, delete-orphan"
    )
    relocation_sites: Mapped[List["RelocationSite"]] = relationship(
        "RelocationSite", back_populates="district", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        UniqueConstraint("state_id", "code", name="uq_district_state_code"),
        Index("idx_districts_geom", "geom", postgresql_using="gist"),
    )


class Habitation(BaseModel):
    __tablename__ = "habitations"
    
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    state_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("states.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False
    )
    boundary_geom: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=True
    )
    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    households: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Vulnerability scores (0-100)
    socioeconomic_vulnerability: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    physical_vulnerability: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    composite_vulnerability: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True, index=True)
    
    # Socioeconomic indicators
    literacy_rate: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    pucca_houses_pct: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    sc_st_pct: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    female_headed_pct: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    disability_pct: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    road_access_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    healthcare_access_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    assessed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    district: Mapped["District"] = relationship("District", back_populates="habitations")
    state: Mapped["State"] = relationship("State", back_populates="habitations")
    relocation_priorities: Mapped[List["RelocationPriority"]] = relationship(
        "RelocationPriority", back_populates="habitation", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        Index("idx_habitations_geom", "geom", postgresql_using="gist"),
        Index("idx_habitations_district", "district_id"),
        Index("idx_habitations_vulnerability", "composite_vulnerability"),
    )


class HazardZone(BaseModel):
    __tablename__ = "hazard_zones"
    
    hazard_type: Mapped[HazardType] = mapped_column(
        SQLEnum(HazardType, name="hazard_type_enum", create_constraint=True),
        nullable=False,
        index=True
    )
    severity: Mapped[SeverityLevel] = mapped_column(
        SQLEnum(SeverityLevel, name="severity_level_enum", create_constraint=True),
        nullable=False,
        index=True
    )
    severity_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False,
        index=True
    )
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    __table_args__ = (
        Index("idx_hazard_zones_geom", "geom", postgresql_using="gist"),
        Index("idx_hazard_zones_type_severity", "hazard_type", "severity"),
        Index("idx_hazard_zones_temporal", "valid_from", "valid_to"),
    )


class DisasterEvent(BaseModel):
    __tablename__ = "disaster_events"
    
    hazard_type: Mapped[HazardType] = mapped_column(
        SQLEnum(HazardType, name="hazard_type_enum_disaster", create_constraint=True),
        nullable=False,
        index=True
    )
    event_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    event_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    affected_geom: Mapped[Optional[str]] = mapped_column(
        Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True),
        nullable=True
    )
    affected_habitations: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(postgresql.UUID(as_uuid=True)), 
        default=list,
        nullable=False
    )
    casualties: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    injured: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    displaced: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    houses_damaged: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    economic_loss_inr: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    __table_args__ = (
        Index("idx_disaster_events_geom", "affected_geom", postgresql_using="gist"),
        Index("idx_disaster_events_type_date", "hazard_type", "event_date"),
    )


class RelocationSite(BaseModel):
    __tablename__ = "relocation_sites"
    
    district_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("districts.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geom: Mapped[str] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False
    )
    
    # Area metrics (hectares)
    total_area_ha: Mapped[float] = mapped_column(DECIMAL(10,2), nullable=False)
    buildable_area_ha: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2), nullable=True)
    agricultural_area_ha: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2), nullable=True)
    forest_area_ha: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2), nullable=True)
    water_body_area_ha: Mapped[Optional[float]] = mapped_column(DECIMAL(10,2), nullable=True)
    
    # Infrastructure & Services
    water_availability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    road_access_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    electricity_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    healthcare_facility_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    school_facility_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    market_facility_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    
    # Capacity
    current_population: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_carrying_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    recommended_capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Suitability (0-100)
    land_suitability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    water_suitability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    infrastructure_suitability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    environmental_suitability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True)
    composite_suitability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4,2), nullable=True, index=True)
    
    # Constraints & Risks
    flood_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    landslide_risk: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    seismic_zone: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ecological_sensitivity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    land_ownership: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Assessment
    assessment_date: Mapped[date] = mapped_column(Date, nullable=False)
    assessed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    district: Mapped["District"] = relationship("District", back_populates="relocation_sites")
    relocation_priorities: Mapped[List["RelocationPriority"]] = relationship(
        "RelocationPriority", back_populates="recommended_site"
    )
    
    __table_args__ = (
        Index("idx_relocation_sites_geom", "geom", postgresql_using="gist"),
        Index("idx_relocation_sites_district", "district_id"),
        Index("idx_relocation_sites_suitability", "composite_suitability_score"),
    )


class RelocationPriority(BaseModel):
    __tablename__ = "relocation_priorities"
    
    habitation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("habitations.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    recommended_site_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("relocation_sites.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    alternative_site_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(postgresql.UUID(as_uuid=True)), 
        default=list,
        nullable=False
    )
    
    # Priority
    priority_tier: Mapped[PriorityTier] = mapped_column(
        SQLEnum(PriorityTier, name="priority_tier_enum", create_constraint=True),
        nullable=False,
        index=True
    )
    priority_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Scoring components (0-100 each)
    hazard_exposure_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    vulnerability_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    capacity_gap_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    distance_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    cost_effectiveness_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True)
    composite_priority_score: Mapped[Optional[float]] = mapped_column(DECIMAL(5,2), nullable=True, index=True)
    
    # Logistics
    distance_to_site_km: Mapped[Optional[float]] = mapped_column(DECIMAL(8,2), nullable=True)
    estimated_relocation_cost_inr: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    estimated_timeline_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status tracking
    status: Mapped[RelocationStatus] = mapped_column(
        SQLEnum(RelocationStatus, name="relocation_status_enum", create_constraint=True),
        default=RelocationStatus.PENDING,
        nullable=False
    )
    approved_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Model info
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    
    habitation: Mapped["Habitation"] = relationship("Habitation", back_populates="relocation_priorities")
    recommended_site: Mapped[Optional["RelocationSite"]] = relationship(
        "RelocationSite", back_populates="relocation_priorities"
    )
    
    __table_args__ = (
        UniqueConstraint("habitation_id", "model_version", name="uq_priority_habitation_version"),
        Index("idx_relocation_priorities_tier", "priority_tier"),
        Index("idx_relocation_priorities_site", "recommended_site_id"),
        Index("idx_relocation_priorities_score", "composite_priority_score"),
    )


class MLModel(BaseModel):
    __tablename__ = "ml_models"
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hazard_type: Mapped[Optional[HazardType]] = mapped_column(
        SQLEnum(HazardType, name="hazard_type_enum_model", create_constraint=True),
        nullable=True
    )
    framework: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    artifact_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    training_data_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    features: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    hyperparameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    status: Mapped[ModelStatus] = mapped_column(
        SQLEnum(ModelStatus, name="model_status_enum", create_constraint=True),
        default=ModelStatus.STAGING,
        nullable=False
    )
    deployed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_name_version"),
    )


class IngestionLog(BaseModel):
    __tablename__ = "ingestion_logs"
    
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    dataset: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[IngestionStatus] = mapped_column(
        SQLEnum(IngestionStatus, name="ingestion_status_enum", create_constraint=True),
        nullable=False
    )
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    records_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    __table_args__ = (
        Index("idx_ingestion_logs_source_date", "source", "started_at"),
    )