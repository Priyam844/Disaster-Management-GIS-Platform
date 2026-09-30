# GIS Disaster Management Platform

Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Immediate Relocation Needs for Vulnerable Habitations.

## Overview

This platform provides a comprehensive GIS-enabled decision support system for State Disaster Management Authorities (SDMA) to:

- **Map and update hazard-based Red Zones** in real-time (landslides, floods, coastal erosion, cloudbursts)
- **Assess carrying capacity** of safer relocation sites
- **Prioritize vulnerable habitations** for immediate, short-term, and medium-term relocation
- **Provide actionable insights** for proactive disaster management planning

## Tech Stack

### Backend
- **FastAPI** - High-performance async Python API framework
- **PostgreSQL + PostGIS** - Spatial database for geospatial data
- **Redis** - Caching, task queue (Celery), pub/sub
- **MinIO** - S3-compatible object storage for raster files
- **GeoPandas, Shapely, Rasterio** - Geospatial processing
- **Scikit-learn, XGBoost** - ML models for hazard prediction
- **Celery** - Distributed task queue for data ingestion

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Deck.gl + MapLibre GL** - High-performance WebGL mapping
- **TanStack Query** - Server state management
- **Zustand** - Client state management
- **Tailwind CSS** - Utility-first styling
- **Radix UI** - Accessible component primitives

### Infrastructure
- **Docker + Docker Compose** - Containerized deployment
- **GitHub Actions** - CI/CD pipeline
- **PostGIS** - Spatial extensions for PostgreSQL

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/           # API routes
│   │   ├── core/          # Configuration
│   │   ├── db/            # Database session
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── workers/       # Celery workers
│   │   └── main.py        # FastAPI app
│   ├── alembic/           # Database migrations
│   ├── tests/             # Unit tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/           # Next.js App Router pages
│   │   ├── components/    # React components
│   │   ├── lib/           # Utilities, API client, stores
│   │   ├── hooks/         # Custom React hooks
│   │   └── types/         # TypeScript types
│   ├── Dockerfile
│   ├── package.json
│   └── tailwind.config.js
├── docker-compose.yml
├── plan.md
└── README.md
```

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd gis-disaster-platform
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Development Setup

#### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Documentation

The API follows RESTful conventions with OpenAPI 3.0 specification available at `/docs`.

### Main Endpoints

#### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh access token
- `GET /api/v1/auth/me` - Current user info

#### Spatial Data
- `GET /api/v1/states` - List states
- `GET /api/v1/districts` - List districts
- `GET /api/v1/habitations` - List habitations with vulnerability scores

#### Hazards & Red Zones
- `GET /api/v1/hazards/zones` - Hazard zones with filters
- `GET /api/v1/red-zones` - Current high-severity zones
- `GET /api/v1/red-zones/geojson/export` - Export as GeoJSON
- `GET /api/v1/hazards/timeseries` - Time series for location

#### Relocation Sites
- `GET /api/v1/sites` - List relocation sites
- `GET /api/v1/sites/{id}/capacity` - Site capacity analysis

#### Prioritization
- `GET /api/v1/prioritization` - Prioritized relocation list
- `GET /api/v1/prioritization/statistics` - Priority statistics

#### Analytics
- `GET /api/v1/analytics/dashboard` - Dashboard summary
- `GET /api/v1/analytics/hazard-trends` - Hazard trends
- `GET /api/v1/analytics/capacity-gap` - Capacity gap analysis

## Data Sources

The platform integrates data from:

- **Bhuvan (NRSC/ISRO)** - DEM, LULC, Watershed boundaries
- **IMD** - Rainfall, Weather forecasts, Extreme events
- **CWC** - River levels, Flood forecasts
- **GSI** - Landslide inventory, Geological maps
- **Census/NFHS** - Population, Housing, Socioeconomic data
- **Sentinel-1/2** - SAR flood mapping, Optical change detection
- **Landsat 8/9** - Long-term change detection
- **OpenStreetMap** - Roads, Buildings, POIs
- **NDMA/SDMA** - Historical disaster records

## ML Models

1. **Multi-Hazard Susceptibility** - XGBoost ensemble for per-grid probability
2. **Vulnerability Scoring** - Gradient boosting for composite vulnerability
3. **Carrying Capacity** - Constraint-based optimization + ML correction
4. **Prioritization Engine** - TOPSIS MCDA for relocation ranking

## Deployment

### Production Deployment

1. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

2. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Environment Variables

Key environment variables (see `.env.example`):

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Redis
REDIS_URL=redis://host:6379/0

# MinIO
MINIO_ENDPOINT=host:9000
MINIO_ACCESS_KEY=key
MINIO_SECRET_KEY=secret

# JWT
JWT_SECRET_KEY=your-secret-key-min-32-chars

# External APIs
BHUVAN_API_KEY=your-key
IMD_API_KEY=your-key
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NRSC/ISRO for Bhuvan geospatial data
- IMD for meteorological data
- CWC for hydrological data
- GSI for geological data
- OpenStreetMap contributors
- Copernicus/Sentinel for satellite imagery