# GIS Disaster Management Platform - Implementation Plan

## Project Overview
- **Title**: Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations
- **Scope**: Multi-State / National Platform
- **Timeline**: 2-3 Months (Hackathon/Prototype MVP)
- **Primary Users**: State Disaster Management Authorities (SDMA)
- **Target Hazards (MVP)**: Landslide + Flood (recommended for data availability)

---

## Technology Stack

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| **Backend Framework** | FastAPI | 0.110+ | High performance, async, automatic OpenAPI docs, excellent GIS library support |
| **Language** | Python | 3.11+ | Modern async support, rich GIS/ML ecosystem |
| **Database** | PostgreSQL + PostGIS | 15+ / 3.4+ | Industry standard for spatial data, ACID, scalable |
| **Spatial Processing** | GeoPandas, Shapely, Rasterio, PyProj | Latest | Complete vector/raster analysis toolkit |
| **AI/ML** | Scikit-learn, XGBoost, TensorFlow/Keras | Latest | Hazard prediction, vulnerability scoring, prioritization |
| **Task Queue** | Celery + Redis | Latest | Async processing for heavy GIS operations |
| **Cache/Session** | Redis | 7+ | Fast caching, pub/sub for real-time updates |
| **Frontend Framework** | Next.js | 14+ (App Router) | SSR, TypeScript support, excellent performance |
| **UI Library** | React | 18+ | Component-based, large ecosystem |
| **Language** | TypeScript | 5+ | Type safety for complex spatial data |
| **Mapping** | Deck.gl + MapLibre GL | Latest | High-performance WebGL, open-source |
| **State Management** | Zustand + TanStack Query | Latest | Lightweight, performant server state |
| **Charts/Analytics** | Recharts / Apache ECharts | Latest | Interactive visualizations |
| **Authentication** | JWT + bcrypt | Latest | Stateless, role-based access control |
| **Containerization** | Docker + Docker Compose | Latest | Consistent dev/prod environments |
| **CI/CD** | GitHub Actions | - | Automated testing, linting, deployment |
| **Code Quality** | Ruff, Black, MyPy, ESLint, Prettier | Latest | Fast linting, formatting, type checking |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  SDMA Dashboard  │  │   Mobile App     │  │  API Consumers   │          │
│  │  (Next.js/React) │  │   (Future)       │  │  (External)      │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
└───────────┼─────────────────────┼─────────────────────┼─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API GATEWAY (FastAPI)                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │   Auth/     │  │   Hazard    │  │   Site      │  │  Relocation/    │   │
│  │   RBAC      │  │   Zones     │  │   Capacity  │  │  Prioritization │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │
│  │  Analytics  │  │   Export    │  │   Admin     │  │   WebSocket     │   │
│  │  /Reports   │  │   (GeoJSON, │  │  (Data      │  │   (Real-time)   │   │
│  │             │  │   PDF, CSV) │  │   Sources)  │  │                 │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────┘   │
└───────────┬─────────────────────┬─────────────────────┬─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SERVICE LAYER                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Hazard Engine   │  │ Carrying Capacity│  │  Vulnerability           │  │
│  │  - Susceptibility│  │  Engine          │  │  Assessment              │  │
│  │    Modeling      │  │  - Suitability   │  │  - Socioeconomic Index   │  │
│  │  - Red Zone Gen  │  │    Scoring       │  │  - Physical Vulnerability│  │
│  │  - Time Series   │  │  - Optimization  │  │  - Composite Scoring     │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │ Prioritization   │  │  Data Ingestion  │  │  Notification/           │  │
│  │ Engine           │  │  Pipeline        │  │  Alerting                │  │
│  │ - MCDA (TOPSIS)  │  │  - ETL Workers   │  │  - Threshold Alerts      │  │
│  │ - Cost-Benefit   │  │  - Validation    │  │  - Scheduled Reports     │  │
│  │ - Tier Assignment│  │  - Transformation│  │  - WebSocket Push        │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└───────────┬─────────────────────┬─────────────────────┬─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  PostgreSQL +    │  │  Redis           │  │  Object Storage          │  │
│  │  PostGIS         │  │  - Cache         │  │  (MinIO/S3)              │  │
│  │  - Spatial Tables│  │  - Task Queue    │  │  - Raster Files (COG)    │  │
│  │  - Materialized  │  │  - Pub/Sub       │  │  - Model Artifacts       │  │
│  │    Views         │  │  - Sessions      │  │  - Export Files          │  │
│  │  - Spatial Index │  │  - Rate Limit    │  │                          │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────┘  │
└───────────┬─────────────────────┬─────────────────────┬─────────────────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL DATA SOURCES                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Bhuvan    │ │     IMD     │ │    CWC      │ │    GSI      │           │
│  │  (NRSC/ISRO)│ │             │ │             │ │             │           │
│  │  - DEM      │ │ - Rainfall  │ │ - River     │ │ - Landslide │           │
│  │  - LULC     │ │ - Forecasts │ │   Levels    │ │   Inventory │           │
│  │  - Watershed│ │ - Extremes  │ │ - Flood Fcst│ │ - Geology   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │   Census    │ │  Sentinel   │ │  Landsat    │ │   OSM       │           │
│  │  / NFHS     │ │  1/2        │ │  8/9        │ │             │           │
│  │  - Pop/House│ │  - SAR Flood│ │  - Optical  │ │ - Roads     │           │
│  │  - Socioeco │ │  - Change   │ │    Change   │ │ - Buildings │           │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐                                               │
│  │   NDMA/     │ │  INCOIS     │                                               │
│  │   SDMA      │ │             │                                               │
│  │  - History  │ │ - Coastal   │                                               │
│  │  - Camps    │ │   Erosion   │                                               │
│  └─────────────┘ └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (PostGIS)

### Core Administrative Tables
```sql
-- States
CREATE TABLE states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL UNIQUE,  -- e.g., 'UK', 'HP', 'AS'
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_states_geom ON states USING GIST (geom);

-- Districts
CREATE TABLE districts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    state_id UUID NOT NULL REFERENCES states(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) NOT NULL,
    geom GEOMETRY(MULTIPOLYGON, 4326) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(state_id, code)
);
CREATE INDEX idx_districts_geom ON districts USING GIST (geom);
CREATE INDEX idx_districts_state ON districts(state_id);

-- Habitations (Villages/Settlements)
CREATE TABLE habitations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    geom GEOMETRY(POINT, 4326) NOT NULL,  -- Centroid
    boundary_geom GEOMETRY(POLYGON, 4326),  -- Optional: village boundary
    population INTEGER,
    households INTEGER,
    -- Vulnerability components (0-100 each)
    socioeconomic_vulnerability DECIMAL(5,2),
    physical_vulnerability DECIMAL(5,2),
    composite_vulnerability DECIMAL(5,2),  -- Weighted composite
    -- Socioeconomic indicators
    literacy_rate DECIMAL(5,2),
    pucca_houses_pct DECIMAL(5,2),
    sc_st_pct DECIMAL(5,2),
    female_headed_pct DECIMAL(5,2),
    disability_pct DECIMAL(5,2),
    road_access_km DECIMAL(8,2),
    healthcare_access_km DECIMAL(8,2),
    metadata JSONB DEFAULT '{}',
    assessed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_habitations_geom ON habitations USING GIST (geom);
CREATE INDEX idx_habitations_district ON habitations(district_id);
CREATE INDEX idx_habitations_vulnerability ON habitations(composite_vulnerability);
```

### Hazard Zones (Time-Series, Multi-Hazard)
```sql
-- Hazard types enum
CREATE TYPE hazard_type AS ENUM ('LANDSLIDE', 'FLOOD', 'COASTAL_EROSION', 'CLOUDBURST', 'EARTHQUAKE');
CREATE TYPE severity_level AS ENUM ('VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH');

-- Hazard Zones - stores polygon zones with severity for specific time periods
CREATE TABLE hazard_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hazard_type hazard_type NOT NULL,
    severity severity_level NOT NULL,
    severity_score DECIMAL(4,2),  -- 0-100 continuous score
    geom GEOMETRY(POLYGON, 4326) NOT NULL,
    -- Temporal validity
    valid_from TIMESTAMPTZ NOT NULL,
    valid_to TIMESTAMPTZ,  -- NULL = current/ongoing
    -- Source & quality
    source VARCHAR(100) NOT NULL,  -- e.g., 'BHUVAN_LULC_2023', 'IMD_RAINFALL_2024', 'MODEL_V1'
    model_version VARCHAR(50),
    confidence_score DECIMAL(4,2),  -- 0-100
    -- Metadata
    metadata JSONB DEFAULT '{}',  -- e.g., {"rainfall_mm": 250, "return_period": 50}
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_hazard_zones_geom ON hazard_zones USING GIST (geom);
CREATE INDEX idx_hazard_zones_type_severity ON hazard_zones(hazard_type, severity);
CREATE INDEX idx_hazard_zones_temporal ON hazard_zones(valid_from, valid_to);
CREATE INDEX idx_hazard_zones_source ON hazard_zones(source);

-- Disaster Events (Historical Records)
CREATE TABLE disaster_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hazard_type hazard_type NOT NULL,
    event_name VARCHAR(200),  -- e.g., "2023 Himachal Flash Floods"
    event_date DATE NOT NULL,
    end_date DATE,
    affected_geom GEOMETRY(GEOMETRY, 4326),  -- Affected area
    affected_habitations UUID[],  -- Array of habitation IDs
    casualties INTEGER,
    injured INTEGER,
    displaced INTEGER,
    houses_damaged INTEGER,
    economic_loss_inr BIGINT,  -- In Rupees
    source VARCHAR(100),  -- 'NDMA', 'SDMA', 'NEWS', 'SATELLITE'
    verified BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_disaster_events_geom ON disaster_events USING GIST (affected_geom);
CREATE INDEX idx_disaster_events_type_date ON disaster_events(hazard_type, event_date);
```

### Relocation Sites & Carrying Capacity
```sql
-- Relocation Site Assessment
CREATE TABLE relocation_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    district_id UUID NOT NULL REFERENCES districts(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    geom GEOMETRY(POLYGON, 4326) NOT NULL,
    centroid GEOMETRY(POINT, 4326) GENERATED ALWAYS AS (ST_Centroid(geom)) STORED,
    -- Area metrics (hectares)
    total_area_ha DECIMAL(10,2) NOT NULL,
    buildable_area_ha DECIMAL(10,2),
    agricultural_area_ha DECIMAL(10,2),
    forest_area_ha DECIMAL(10,2),
    water_body_area_ha DECIMAL(10,2),
    -- Infrastructure & Services
    water_availability_score DECIMAL(4,2),  -- 0-100
    road_access_score DECIMAL(4,2),  -- 0-100 (distance to nearest major road)
    electricity_access BOOLEAN DEFAULT FALSE,
    healthcare_facility_km DECIMAL(8,2),
    school_facility_km DECIMAL(8,2),
    market_facility_km DECIMAL(8,2),
    -- Capacity
    current_population INTEGER DEFAULT 0,
    max_carrying_capacity INTEGER,  -- Calculated max sustainable population
    recommended_capacity INTEGER,   -- With safety buffer (e.g., 80% of max)
    -- Suitability (0-100)
    land_suitability_score DECIMAL(4,2),
    water_suitability_score DECIMAL(4,2),
    infrastructure_suitability_score DECIMAL(4,2),
    environmental_suitability_score DECIMAL(4,2),
    composite_suitability_score DECIMAL(4,2),
    -- Constraints & Risks
    flood_risk BOOLEAN DEFAULT FALSE,
    landslide_risk BOOLEAN DEFAULT FALSE,
    seismic_zone INTEGER,  -- 2, 3, 4, 5
    ecological_sensitivity VARCHAR(20),  -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    land_ownership VARCHAR(50),  -- 'GOVERNMENT', 'FOREST', 'PRIVATE', 'COMMUNITY'
    -- Assessment
    assessment_date DATE NOT NULL,
    assessed_by VARCHAR(100),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_relocation_sites_geom ON relocation_sites USING GIST (geom);
CREATE INDEX idx_relocation_sites_district ON relocation_sites(district_id);
CREATE INDEX idx_relocation_sites_suitability ON relocation_sites(composite_suitability_score);
```

### Relocation Prioritization
```sql
-- Priority tiers
CREATE TYPE priority_tier AS ENUM ('IMMEDIATE', 'SHORT_TERM', 'MEDIUM_TERM', 'NOT_REQUIRED');
CREATE TYPE relocation_status AS ENUM ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'CANCELLED');

-- Relocation Priority Mapping
CREATE TABLE relocation_priorities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    habitation_id UUID NOT NULL REFERENCES habitations(id) ON DELETE CASCADE,
    recommended_site_id UUID REFERENCES relocation_sites(id) ON DELETE SET NULL,
    alternative_site_ids UUID[],  -- Other suitable sites
    -- Priority
    priority_tier priority_tier NOT NULL,
    priority_rank INTEGER,  -- 1 = highest priority within tier
    -- Scoring components (0-100 each)
    hazard_exposure_score DECIMAL(5,2),
    vulnerability_score DECIMAL(5,2),
    capacity_gap_score DECIMAL(5,2),  -- Population vs site capacity
    distance_score DECIMAL(5,2),      -- Distance to recommended site
    cost_effectiveness_score DECIMAL(5,2),
    composite_priority_score DECIMAL(5,2),  -- Final weighted score
    -- Logistics
    distance_to_site_km DECIMAL(8,2),
    estimated_relocation_cost_inr BIGINT,
    estimated_timeline_months INTEGER,
    -- Status tracking
    status relocation_status DEFAULT 'PENDING',
    approved_by VARCHAR(100),
    approved_at TIMESTAMPTZ,
    notes TEXT,
    -- Model info
    model_version VARCHAR(50),
    computed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(habitation_id, model_version)
);
CREATE INDEX idx_relocation_priorities_habitation ON relocation_priorities(habitation_id);
CREATE INDEX idx_relocation_priorities_tier ON relocation_priorities(priority_tier);
CREATE INDEX idx_relocation_priorities_site ON relocation_priorities(recommended_site_id);
CREATE INDEX idx_relocation_priorities_score ON relocation_priorities(composite_priority_score);
```

### Model Registry & Metadata
```sql
-- ML Model Registry
CREATE TABLE ml_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,  -- e.g., 'landslide_susceptibility_v1'
    version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50),  -- 'susceptibility', 'vulnerability', 'capacity', 'prioritization', 'forecast'
    hazard_type hazard_type,
    framework VARCHAR(50),  -- 'sklearn', 'xgboost', 'tensorflow', 'pytorch'
    artifact_path VARCHAR(500),  -- S3/MinIO path
    metrics JSONB,  -- {"auc": 0.87, "f1": 0.82, "precision": 0.79}
    training_data_hash VARCHAR(64),  -- SHA256 of training data
    features JSONB,  -- Feature names and types
    hyperparameters JSONB,
    status VARCHAR(20) DEFAULT 'STAGING',  -- 'STAGING', 'PRODUCTION', 'ARCHIVED'
    deployed_at TIMESTAMPTZ,
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(name, version)
);

-- Data Ingestion Logs
CREATE TABLE ingestion_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source VARCHAR(100) NOT NULL,
    dataset VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- 'STARTED', 'SUCCESS', 'FAILED', 'PARTIAL'
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX idx_ingestion_logs_source_date ON ingestion_logs(source, started_at);
```

### Materialized Views for Performance
```sql
-- Current Red Zones (latest hazard zones per type)
CREATE MATERIALIZED VIEW current_red_zones AS
SELECT DISTINCT ON (hz.hazard_type, hz.geom)
    hz.id, hz.hazard_type, hz.severity, hz.severity_score,
    hz.geom, hz.valid_from, hz.source, hz.confidence_score,
    hz.metadata
FROM hazard_zones hz
WHERE hz.valid_to IS NULL OR hz.valid_to > NOW()
  AND hz.severity IN ('HIGH', 'VERY_HIGH')
ORDER BY hz.hazard_type, hz.geom, hz.valid_from DESC;

CREATE UNIQUE INDEX idx_current_red_zones_unique ON current_red_zones(hazard_type, geom);
CREATE INDEX idx_current_red_zones_geom ON current_red_zones USING GIST (geom);

-- Habitation Hazard Exposure (current)
CREATE MATERIALIZED VIEW habitation_hazard_exposure AS
SELECT 
    h.id AS habitation_id,
    h.name AS habitation_name,
    h.district_id,
    h.geom,
    h.composite_vulnerability,
    hz.hazard_type,
    hz.severity,
    hz.severity_score,
    ST_Distance(h.geom::geography, hz.geom::geography) AS distance_m
FROM habitations h
JOIN current_red_zones hz ON ST_Intersects(h.geom, hz.geom)
WHERE h.composite_vulnerability IS NOT NULL;

CREATE INDEX idx_habitation_exposure_habitation ON habitation_hazard_exposure(habitation_id);
CREATE INDEX idx_habitation_exposure_type ON habitation_hazard_exposure(hazard_type);

-- Site Capacity Summary
CREATE MATERIALIZED VIEW site_capacity_summary AS
SELECT 
    s.id AS site_id,
    s.name AS site_name,
    s.district_id,
    s.geom,
    s.max_carrying_capacity,
    s.recommended_capacity,
    s.current_population,
    (s.recommended_capacity - s.current_population) AS available_capacity,
    s.composite_suitability_score,
    COUNT(DISTINCT rp.habitation_id) AS assigned_habitations,
    COALESCE(SUM(hab.population), 0) AS assigned_population
FROM relocation_sites s
LEFT JOIN relocation_priorities rp ON rp.recommended_site_id = s.id AND rp.status IN ('PENDING', 'IN_PROGRESS')
LEFT JOIN habitations hab ON hab.id = rp.habitation_id
GROUP BY s.id;

CREATE INDEX idx_site_capacity_summary_district ON site_capacity_summary(district_id);
```

---

## API Specification (OpenAPI 3.0)

### Authentication
```
POST   /api/v1/auth/login              # Login, returns access + refresh token
POST   /api/v1/auth/refresh            # Refresh access token
GET    /api/v1/auth/me                 # Current user info + permissions
POST   /api/v1/auth/logout             # Logout (blacklist refresh token)
```

### Hazard Zones
```
GET    /api/v1/hazards/zones                    # List with filters
       ?hazard_type=LANDSLIDE&severity=HIGH&state=UK&district=&bbox=&page=1&size=50
GET    /api/v1/hazards/zones/{zone_id}          # Single zone detail
GET    /api/v1/hazards/zones/geojson            # Export as GeoJSON FeatureCollection
GET    /api/v1/hazards/timeseries               # Time-series for location
       ?lat=&lon=&hazard_type=LANDSLIDE&days=365
POST   /api/v1/hazards/refresh                  # Trigger model inference (admin)
GET    /api/v1/hazards/statistics               # Summary stats by state/district
```

### Red Zones (Current High/Very High Severity)
```
GET    /api/v1/red-zones                        # Current red zones
       ?hazard_type=&state=&district=&bbox=
GET    /api/v1/red-zones/habitation/{hab_id}    # Red zones affecting a habitation
GET    /api/v1/red-zones/geojson                # Export for mapping
POST   /api/v1/red-zones/generate               # Regenerate from latest models (admin)
```

### Relocation Sites
```
GET    /api/v1/sites                            # List sites with filters
       ?district=&suitability_min=60&capacity_min=100&risk_free=true&page=1&size=50
GET    /api/v1/sites/{site_id}                  # Site detail with capacity breakdown
GET    /api/v1/sites/{site_id}/capacity         # Detailed capacity analysis
GET    /api/v1/sites/geojson                    # Export sites as GeoJSON
POST   /api/v1/sites                            # Create site (admin)
PUT    /api/v1/sites/{site_id}                  # Update site (admin)
POST   /api/v1/sites/{site_id}/assess           # Run carrying capacity assessment (admin)
```

### Vulnerability Assessment
```
GET    /api/v1/vulnerability/habitations        # List with vulnerability scores
       ?district=&vulnerability_min=70&page=1&size=50
GET    /api/v1/vulnerability/habitations/{hab_id}  # Detailed vulnerability profile
POST   /api/v1/vulnerability/assess             # Run vulnerability assessment (admin)
GET    /api/v1/vulnerability/indicators         # Available indicators metadata
```

### Prioritization
```
GET    /api/v1/prioritization                   # Prioritized relocation list
       ?state=&district=&tier=IMMEDIATE&page=1&size=100
GET    /api/v1/prioritization/habitation/{hab_id}  # Priority detail for one habitation
GET    /api/v1/prioritization/site/{site_id}      # Habitations assigned to a site
GET    /api/v1/prioritization/statistics          # Tier counts, population affected
GET    /api/v1/prioritization/geojson             # Export as GeoJSON
POST   /api/v1/prioritization/run                 # Run prioritization engine (admin)
PUT    /api/v1/prioritization/{priority_id}       # Update status/notes (admin)
```

### Analytics & Dashboard
```
GET    /api/v1/analytics/dashboard              # Summary cards for dashboard
GET    /api/v1/analytics/hazard-trends          # Time-series trends
       ?hazard_type=&state=&granularity=month&months=24
GET    /api/v1/analytics/vulnerability-distribution  # Histogram of vulnerability scores
GET    /api/v1/analytics/relocation-progress    # Status tracking
GET    /api/v1/analytics/capacity-gap           # Demand vs supply by district
GET    /api/v1/analytics/comparative            # State/district comparison
```

### Export & Reports
```
GET    /api/v1/export/red-zones.geojson
GET    /api/v1/export/relocation-plan.geojson
GET    /api/v1/export/priority-report.pdf       # PDF report
GET    /api/v1/export/capacity-report.csv
GET    /api/v1/export/habitation-profile/{hab_id}.pdf
```

### Admin / Data Management
```
GET    /api/v1/admin/data-sources               # List configured sources
POST   /api/v1/admin/data-sources               # Add data source
POST   /api/v1/admin/ingest/{source_id}         # Trigger ingestion
GET    /api/v1/admin/ingestion-logs             # Ingestion history
GET    /api/v1/admin/models                     # Model registry
POST   /api/v1/admin/models                     # Register model
PUT    /api/v1/admin/models/{model_id}/deploy   # Deploy to production
GET    /api/v1/admin/users                      # User management (admin only)
```

### WebSocket (Real-time)
```
WS     /api/v1/ws/hazards                       # Real-time hazard updates
       Subscribe: { "action": "subscribe", "filters": {"state": "UK", "hazard_type": "LANDSLIDE"} }
       Message: { "type": "hazard_update", "data": {...} }
WS     /api/v1/ws/notifications                 # Alert notifications
```

---

## AI/ML Model Specifications

### 1. Multi-Hazard Susceptibility Model
| Aspect | Specification |
|--------|---------------|
| **Target** | Per-grid-cell (100m/30m) probability for each hazard type |
| **Approach** | Ensemble: XGBoost (primary) + Random Forest + Logistic Regression |
| **Features** | DEM derivatives (slope, aspect, curvature, TWI, SPI), Lithology, Land cover, Distance to faults/rivers/coast, Rainfall (historical + forecast), Soil type, NDVI, Night lights, Historical events |
| **Training Data** | Historical disaster events (GSI, NDMA) + Bhuvan LULC + IMD rainfall + Sentinel SAR |
| **Output** | Probability (0-1) per hazard type per grid cell |
| **Validation** | Spatial cross-validation (block CV), AUC-ROC, Precision-Recall |
| **Update Frequency** | Monthly (rainfall), Seasonal (LULC), Annual (model retrain) |

### 2. Vulnerability Scoring Model
| Aspect | Specification |
|--------|---------------|
| **Target** | Composite vulnerability score (0-100) per habitation |
| **Approach** | Gradient Boosting (XGBoost) + PCA for dimensionality reduction |
| **Features** | Population density, % kutcha houses, literacy rate, SC/ST %, female-headed HH %, disability %, distance to road/healthcare/market, dependency ratio, income proxy (night lights), historical damage |
| **Components** | Socioeconomic (50%), Physical (30%), Exposure (20%) |
| **Output** | Score 0-100 + component scores + feature importance |
| **Validation** | Hold-out districts, correlation with historical casualties |

### 3. Carrying Capacity Model
| Aspect | Specification |
|--------|---------------|
| **Target** | Max sustainable population per relocation site |
| **Approach** | Constraint-based optimization + ML correction |
| **Constraints** | Water availability (lpcd), Buildable land (sqm/person), Infrastructure capacity, Ecological limits, Climate projections |
| **Formula** | `Capacity = min(Water_Limit, Land_Limit, Infra_Limit, Eco_Limit) * Safety_Factor(0.8)` |
| **ML Correction** | Random Forest to adjust for unmodeled factors using historical settlement data |
| **Output** | Max capacity, Recommended capacity (80%), Component breakdown |

### 4. Prioritization Engine (MCDA)
| Aspect | Specification |
|--------|---------------|
| **Method** | TOPSIS (Technique for Order Preference by Similarity to Ideal Solution) |
| **Criteria & Weights** | Hazard Exposure (30%), Vulnerability (25%), Capacity Gap (20%), Distance (15%), Cost-Effectiveness (10%) |
| **Normalization** | Vector normalization for benefit/cost criteria |
| **Tiers** | IMMEDIATE (top 10%), SHORT_TERM (10-30%), MEDIUM_TERM (30-60%), NOT_REQUIRED (bottom 40%) |
| **Output** | Ranked list with scores, recommended site, alternatives, cost estimates |

### 5. Hazard Forecasting (Phase 2+)
| Aspect | Specification |
|--------|---------------|
| **Target** | 7-30 day hazard probability forecasts |
| **Approach** | LSTM/Transformer on spatio-temporal sequences |
| **Inputs** | Historical rainfall, soil moisture (SMAP), satellite indices (NDWI, NDSI), IMD forecasts |
| **Output** | Probability maps for next 7/15/30 days |

---

## Data Ingestion Pipeline

### Sources & Frequencies
| Source | Dataset | Frequency | Method | Format |
|--------|---------|-----------|--------|--------|
| Bhuvan | DEM (10m/30m) | Annual | Direct Download | GeoTIFF |
| Bhuvan | LULC | Annual | WCS/WMS | GeoTIFF |
| Bhuvan | Watersheds | Static | Direct Download | Shapefile |
| IMD | Daily Rainfall (0.25°) | Daily | API / NetCDF | NetCDF |
| IMD | Weather Forecast | 3-hourly | API | JSON/GRIB |
| CWC | River Levels | Hourly | API | JSON/CSV |
| CWC | Flood Forecast | Daily | API | JSON |
| GSI | Landslide Inventory | Event-based | Portal | Shapefile/CSV |
| Census | Population/Housing | Decadal | Download | CSV/Shapefile |
| Sentinel-1 | SAR (Flood) | 12-day | Sentinel Hub / AWS | GeoTIFF (COG) |
| Sentinel-2 | Optical (Change) | 5-day | Sentinel Hub / AWS | GeoTIFF (COG) |
| Landsat 8/9 | Long-term Change | 16-day | AWS / USGS | GeoTIFF (COG) |
| OSM | Roads/Buildings | Weekly | Overpass / Planet | PBF/GeoJSON |
| NDMA/SDMA | Disaster Records | Event-based | Manual/API | CSV/Excel |

### ETL Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Scheduler  │────▶│  Extractor  │────▶│ Transformer │────▶│   Loader    │
│  (Celery    │     │  (per src)  │     │  (Validate, │     │  (PostGIS)  │
│   Beat)     │     │             │     │  Reproject, │     │             │
└─────────────┘     └─────────────┘     │  Clip,      │     └─────────────┘
                                        │  Enrich)    │              │
                                        └─────────────┘              ▼
                                                              ┌─────────────┐
                                                              │  Materialized│
                                                              │  View Refresh│
                                                              └─────────────┘
```

### Data Quality Checks
- Geometry validity (ST_IsValid, ST_MakeValid)
- CRS enforcement (EPSG:4326)
- Schema validation (Pydantic models)
- Duplicate detection (spatial + attribute)
- Completeness thresholds (>90% required fields)
- Anomaly detection (statistical outliers)

---

## Frontend Architecture (SDMA Dashboard)

### Tech Stack
- **Framework**: Next.js 14 (App Router) + React 18 + TypeScript
- **Mapping**: Deck.gl + MapLibre GL (with MapTiler/OSM tiles)
- **State**: Zustand (UI state) + TanStack Query (server state)
- **UI Components**: Radix UI + Tailwind CSS
- **Charts**: Recharts + Apache ECharts
- **Forms**: React Hook Form + Zod validation
- **Auth**: NextAuth.js (JWT)

### Page Structure
```
/ (Dashboard Overview)
├── /hazards                    # Hazard Explorer
│   ├── /hazards/map            # Full-screen map
│   ├── /hazards/timeseries     # Temporal analysis
│   └── /hazards/red-zones      # Red zone list + map
├── /sites                      # Relocation Sites
│   ├── /sites/map              # Site map with capacity viz
│   ├── /sites/{id}             # Site detail
│   └── /sites/compare          # Multi-site comparison
├── /prioritization             # Relocation Priorities
│   ├── /prioritization/table   # Tiered table (IMMEDIATE/SHORT/MEDIUM)
│   ├── /prioritization/map     # Priority map
│   └── /prioritization/{id}    # Habitation priority detail
├── /habitations                # Habitation Registry
│   ├── /habitations/map        # Habitation map
│   └── /habitations/{id}       # 360° profile
├── /analytics                  # Analytics & Reports
│   ├── /analytics/trends       # Hazard trends
│   ├── /analytics/vulnerability # Vulnerability distribution
│   ├── /analytics/capacity     # Capacity gap analysis
│   └── /analytics/comparative  # State/district comparison
├── /admin                      # Administration (RBAC)
│   ├── /admin/data-sources     # Source management
│   ├── /admin/ingestion        # Ingestion monitoring
│   ├── /admin/models           # Model registry
│   └── /admin/users            # User management
└── /settings                   # User preferences
```

### Map Components
| Component | Purpose | Deck.gl Layer |
|-----------|---------|---------------|
| HazardHexagonLayer | Hazard density heatmap | HexagonLayer |
| HazardPolygonLayer | Red zone polygons | PolygonLayer |
| HabitationLayer | Habitation points (sized by pop/vuln) | ScatterplotLayer |
| SiteLayer | Relocation sites (sized by capacity) | ScatterplotLayer + IconLayer |
| PriorityFlowLayer | Habitation→Site flows | ArcLayer / LineLayer |
| TimeSlider | Temporal animation | Custom + useAnimationFrame |

### Responsive Breakpoints
- Desktop: ≥1280px (full dashboard)
- Tablet: 768-1279px (collapsible sidebar)
- Mobile: <768px (bottom navigation, map-first)

---

## Implementation Phases (14 Weeks)

### Phase 1: Foundation (Weeks 1-3)
| Week | Tasks | Deliverables |
|------|-------|--------------|
| 1 | Project setup: Docker Compose (PostgreSQL, PostGIS, Redis, MinIO), FastAPI skeleton, Next.js app, CI/CD pipeline, Ruff/Black/MyPy/ESLint config | Running dev environment, linting passing |
| 2 | Auth system: JWT, RBAC (Admin, Analyst, Viewer), user models, login page, protected routes | Working authentication |
| 3 | Core spatial models + Alembic migrations, PostGIS setup, spatial indexes, base CRUD APIs for states/districts/habitations | Database schema deployed, basic API |
| 3 | Data ingestion framework: Celery workers, base extractor/transformer/loader classes, ingestion log table | ETL framework ready |

### Phase 2: Hazard Engine & Red Zones (Weeks 4-6)
| Week | Tasks | Deliverables |
|------|-------|--------------|
| 4 | Landslide susceptibility model (XGBoost) using Bhuvan DEM, GSI inventory, IMD rainfall; Flood susceptibility using Sentinel-1 SAR, CWC river data, DEM | Trained models (v1), model registry entries |
| 5 | Red zone generation: thresholding susceptibility → severity classes (5 levels), polygonization, temporal versioning, materialized views | Dynamic red zone API + GeoJSON export |
| 6 | Hazard map visualization: Deck.gl layers for hazard polygons, hexagon density, time slider, layer controls, legend | Interactive hazard map in dashboard |

### Phase 3: Carrying Capacity & Sites (Weeks 7-9)
| Week | Tasks | Deliverables |
|------|-------|--------------|
| 7 | Site CRUD API, site assessment algorithm (water, land, infra, environment constraints), carrying capacity calculation, suitability scoring | Site management + capacity API |
| 8 | Suitability ML model (Random Forest) trained on historical settlement patterns + site characteristics | Suitability scores per site |
| 9 | Site dashboard: capacity breakdown charts, suitability radar chart, comparison view, map with capacity visualization | Site assessment UI |

### Phase 4: Vulnerability & Prioritization (Weeks 10-12)
| Week | Tasks | Deliverables |
|------|-------|--------------|
| 10 | Vulnerability model: socioeconomic indicators from Census/NFHS, physical vulnerability from housing/road data, composite scoring | Vulnerability scores for all habitations |
| 11 | Prioritization engine: TOPSIS implementation, criteria weights, tier assignment, alternative site recommendation, cost estimation | Prioritization API + ranked lists |
| 12 | Prioritization dashboard: tiered tables with filters, priority map with flow lines, habitation detail with site options, PDF/GeoJSON export | Complete prioritization UI |

### Phase 5: Integration, Polish & Demo (Weeks 13-14)
| Week | Tasks | Deliverables |
|------|-------|--------------|
| 13 | End-to-end integration testing, performance optimization (vector tiles, query optimization, caching), bug fixes, security audit | Stable, performant prototype |
| 14 | Documentation (README, API docs, user guide), demo script recording, presentation slides, deployment to staging | Hackathon-ready submission |

---

## Risk Register & Mitigations

| ID | Risk | Probability | Impact | Mitigation Strategy |
|----|------|-------------|--------|---------------------|
| R1 | Government API access delays / rate limits | High | High | Develop against mock data & open sources (OSM, Sentinel, Census); build adapter pattern for easy source swapping |
| R2 | Insufficient training data for ML models | Medium | High | Use physics-based heuristic rules as baseline; transfer learning from similar regions; synthetic data augmentation |
| R3 | Spatial query performance at national scale | High | Medium | Vector tiles (Tippecanoe/PMTiles), materialized views, spatial partitioning, read replicas, CDN for static tiles |
| R4 | Coordinate system mismatches across sources | Medium | Medium | Enforce EPSG:4326 at ingestion boundary; validate with PROJ; automated CRS detection |
| R5 | Scope creep beyond 2-hazard MVP | High | High | Strict scope document; weekly scope review; "parking lot" for future features |
| R6 | Model explainability for government users | Medium | High | SHAP values for all predictions; rule-based fallback; clear confidence scores |
| R7 | Data privacy / sensitive habitation data | Low | High | Role-based access; anonymization for exports; audit logs; encryption at rest |
| R8 | Real-time WebSocket scaling | Low | Medium | Redis Pub/Sub horizontal scaling; connection pooling; fallback to polling |

---

## Development Standards

### Code Quality
```bash
# Backend
ruff check .          # Linting (fast)
ruff format .         # Formatting
mypy .                # Type checking
pytest --cov=app      # Tests with coverage

# Frontend
npm run lint          # ESLint
npm run format        # Prettier
npm run typecheck     # tsc --noEmit
npm run test          # Vitest/Jest
```

### Git Workflow
- `main` - Production ready
- `develop` - Integration branch
- `feature/*` - Feature branches
- `hotfix/*` - Urgent fixes
- PR required for all merges to `develop`/`main`
- Conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`

### Environment Variables
```env
# Backend (.env)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/gis_platform
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=gis-data
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/api/v1/ws
NEXT_PUBLIC_MAPTILER_KEY=your-key
NEXT_PUBLIC_APP_NAME=GIS Disaster Platform
```

---

## Deployment Architecture (Production)

```
                    ┌─────────────────┐
                    │   Load Balancer │  (NGINX/Cloud LB)
                    │   (SSL Term.)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌─────────┐   ┌─────────┐   ┌─────────┐
         │ App Pod │   │ App Pod │   │ App Pod │  (FastAPI + Gunicorn/Uvicorn workers)
         └────┬────┘   └────┬────┘   └────┬────┘
              │             │             │
              └─────────────┼─────────────┘
                            ▼
              ┌─────────────────────────┐
              │     PgBouncer Pool      │
              └───────────┬─────────────┘
                          ▼
              ┌─────────────────────────┐
              │  PostgreSQL Primary     │
              │  (PostGIS, Streaming    │
              │   Replication)          │
              └───────────┬─────────────┘
                          ▼
              ┌─────────────────────────┐
              │  PostgreSQL Replicas    │  (Read queries, analytics)
              └─────────────────────────┘

              ┌─────────────────────────┐
              │     Redis Cluster       │  (Cache, Queue, Pub/Sub)
              └─────────────────────────┘

              ┌─────────────────────────┐
              │     MinIO / S3          │  (Raster tiles, models, exports)
              └─────────────────────────┘

              ┌─────────────────────────┐
              │   Frontend (Vercel/     │  (Static export or SSR)
              │   Cloudflare Pages)     │
              └─────────────────────────┘
```

---

## Success Metrics (MVP)

| Metric | Target |
|--------|--------|
| API Response Time (p95) | < 500ms |
| Map Load Time (initial) | < 3 seconds |
| Spatial Query (10k features) | < 1 second |
| Model Inference (state-wide) | < 5 minutes |
| Data Ingestion (daily) | < 30 minutes |
| Uptime | 99.5% |
| Test Coverage | > 80% |
| Lighthouse Score | > 90 |

---

## Appendix: Key References

1. **NDMA Guidelines** - National Disaster Management Plan (2019)
2. **Bhuvan Portal** - https://bhuvan.nrsc.gov.in
3. **IMD Data Portal** - https://mausam.imd.gov.in
4. **CWC Flood Forecasting** - https://ffs.indiawaterportal.org
5. **GSI Landslide Atlas** - https://www.gsi.gov.in
6. **Sentinel Hub** - https://www.sentinel-hub.com
7. **PostGIS Documentation** - https://postgis.net/documentation/
8. **Deck.gl Documentation** - https://deck.gl
9. **TOPSIS Method** - Hwang & Yoon (1981)
10. **Sendai Framework** - UN Disaster Risk Reduction (2015-2030)

---

## Next Immediate Actions

1. [ ] Initialize Git repository with conventional commits
2. [ ] Create Docker Compose with all services
3. [ ] Set up FastAPI project structure with Alembic
4. [ ] Configure PostgreSQL + PostGIS with spatial extensions
5. [ ] Implement JWT authentication + RBAC
6. [ ] Create base spatial models (State, District, Habitation)
7. [ ] Build first ETL worker for Census + OSM data
8. [ ] Set up Next.js frontend with MapLibre + Deck.gl
9. [ ] Implement basic hazard zone API + map visualization
10. [ ] Train landslide susceptibility model (v1)

---

*Document Version: 1.0*
*Last Updated: 2026-09-01*
*Status: Ready for Implementation*