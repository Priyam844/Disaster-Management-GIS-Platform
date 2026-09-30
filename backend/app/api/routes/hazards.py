from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from geoalchemy2 import functions as geofunc
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
import uuid
from typing import List, Optional
from datetime import datetime, date, timedelta

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_analyst, require_admin, get_pagination_params, require_state_permission
from app.schemas.spatial import (
    HazardZoneCreate, HazardZoneUpdate, HazardZoneResponse,
    DisasterEventCreate, DisasterEventUpdate, DisasterEventResponse,
    PaginationParams, PaginatedResponse,
)
from app.models.spatial import HazardZone, DisasterEvent, HazardType, SeverityLevel, State, District
from app.models.auth import User

router = APIRouter()


# Hazard Zone Routes
@router.post("/hazards/zones", response_model=HazardZoneResponse, status_code=status.HTTP_201_CREATED)
async def create_hazard_zone(
    zone_data: HazardZoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    # For now, allow creation without state check (zones can span states)
    from geoalchemy2 import WKTElement
    geom = WKTElement(zone_data.geom, srid=4326)
    
    zone = HazardZone(
        hazard_type=zone_data.hazard_type,
        severity=zone_data.severity,
        severity_score=zone_data.severity_score,
        geom=geom,
        valid_from=zone_data.valid_from,
        valid_to=zone_data.valid_to,
        source=zone_data.source,
        model_version=zone_data.model_version,
        confidence_score=zone_data.confidence_score,
        metadata_=zone_data.metadata,
    )
    db.add(zone)
    await db.commit()
    await db.refresh(zone)
    return zone


@router.get("/hazards/zones", response_model=PaginatedResponse[HazardZoneResponse])
async def list_hazard_zones(
    hazard_type: Optional[HazardType] = None,
    severity: Optional[SeverityLevel] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    bbox: Optional[str] = None,  # minx,miny,maxx,maxy
    valid_at: Optional[datetime] = None,
    source: Optional[str] = None,
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(HazardZone).order_by(HazardZone.valid_from.desc())
    
    if hazard_type:
        query = query.where(HazardZone.hazard_type == hazard_type)
    if severity:
        query = query.where(HazardZone.severity == severity)
    if source:
        query = query.where(HazardZone.source.ilike(f"%{source}%"))
    if valid_at:
        query = query.where(
            and_(
                HazardZone.valid_from <= valid_at,
                or_(HazardZone.valid_to.is_(None), HazardZone.valid_to > valid_at)
            )
        )
    
    # Spatial filter by state/district
    if state_code or district_code:
        # Join with states/districts for filtering
        if district_code:
            district_subq = select(District.id).where(
                District.code == district_code.upper()
            )
            if state_code:
                district_subq = district_subq.where(
                    District.state_id == select(State.id).where(State.code == state_code.upper()).scalar_subquery()
                )
            district_ids = [row[0] for row in (await db.execute(district_subq)).all()]
            if district_ids:
                # Filter zones that intersect with district boundaries
                district_geoms = select(District.geom).where(District.id.in_(district_ids))
                query = query.where(
                    geofunc.ST_Intersects(HazardZone.geom, district_geoms)
                )
        elif state_code:
            state_geom = select(State.geom).where(State.code == state_code.upper())
            query = query.where(
                geofunc.ST_Intersects(HazardZone.geom, state_geom)
            )
    
    # Bounding box filter
    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
            from geoalchemy2 import WKTElement
            bbox_poly = WKTElement(
                f"SRID=4326;POLYGON(({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))",
                srid=4326
            )
            query = query.where(geofunc.ST_Intersects(HazardZone.geom, bbox_poly))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Use minx,miny,maxx,maxy"
            )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    zones = list(result.scalars().all())
    
    return PaginatedResponse.create(zones, total, params)


@router.get("/hazards/zones/{zone_id}", response_model=HazardZoneResponse)
async def get_hazard_zone(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(HazardZone).where(HazardZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Hazard zone not found")
    return zone


@router.patch("/hazards/zones/{zone_id}", response_model=HazardZoneResponse)
async def update_hazard_zone(
    zone_id: uuid.UUID,
    zone_data: HazardZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    result = await db.execute(select(HazardZone).where(HazardZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Hazard zone not found")
    
    update_data = zone_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            zone.metadata_ = value
        else:
            setattr(zone, key, value)
    
    await db.commit()
    await db.refresh(zone)
    return zone


@router.delete("/hazards/zones/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hazard_zone(
    zone_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(select(HazardZone).where(HazardZone.id == zone_id))
    zone = result.scalar_one_or_none()
    if not zone:
        raise HTTPException(status_code=404, detail="Hazard zone not found")
    
    await db.delete(zone)
    await db.commit()


# Red Zones (Current High/Very High Severity)
@router.get("/red-zones", response_model=PaginatedResponse[HazardZoneResponse])
async def list_red_zones(
    hazard_type: Optional[HazardType] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    bbox: Optional[str] = None,
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current red zones (HIGH and VERY_HIGH severity, valid now)"""
    now = datetime.utcnow()
    
    query = select(HazardZone).where(
        HazardZone.severity.in_([SeverityLevel.HIGH, SeverityLevel.VERY_HIGH]),
        HazardZone.valid_from <= now,
        or_(HazardZone.valid_to.is_(None), HazardZone.valid_to > now)
    ).order_by(HazardZone.severity.desc(), HazardZone.valid_from.desc())
    
    if hazard_type:
        query = query.where(HazardZone.hazard_type == hazard_type)
    
    # Spatial filters
    if state_code or district_code:
        if district_code:
            district_subq = select(District.id).where(District.code == district_code.upper())
            if state_code:
                district_subq = district_subq.where(
                    District.state_id == select(State.id).where(State.code == state_code.upper()).scalar_subquery()
                )
            district_ids = [row[0] for row in (await db.execute(district_subq)).all()]
            if district_ids:
                district_geoms = select(District.geom).where(District.id.in_(district_ids))
                query = query.where(geofunc.ST_Intersects(HazardZone.geom, district_geoms))
        elif state_code:
            state_geom = select(State.geom).where(State.code == state_code.upper())
            query = query.where(geofunc.ST_Intersects(HazardZone.geom, state_geom))
    
    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
            from geoalchemy2 import WKTElement
            bbox_poly = WKTElement(
                f"SRID=4326;POLYGON(({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))",
                srid=4326
            )
            query = query.where(geofunc.ST_Intersects(HazardZone.geom, bbox_poly))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Use minx,miny,maxx,maxy"
            )
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    zones = list(result.scalars().all())
    
    return PaginatedResponse.create(zones, total, params)


@router.get("/red-zones/habitation/{habitation_id}", response_model=List[HazardZoneResponse])
async def get_red_zones_for_habitation(
    habitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get red zones that intersect with a specific habitation"""
    from app.models.spatial import Habitation
    
    result = await db.execute(
        select(Habitation)
        .options(selectinload(Habitation.district).selectinload(District.state))
        .where(Habitation.id == habitation_id)
    )
    habitation = result.scalar_one_or_none()
    if not habitation:
        raise HTTPException(status_code=404, detail="Habitation not found")
    
    await require_state_permission(habitation.state_id, current_user)
    
    now = datetime.utcnow()
    query = select(HazardZone).where(
        HazardZone.severity.in_([SeverityLevel.HIGH, SeverityLevel.VERY_HIGH]),
        HazardZone.valid_from <= now,
        or_(HazardZone.valid_to.is_(None), HazardZone.valid_to > now),
        geofunc.ST_Intersects(HazardZone.geom, habitation.geom)
    ).order_by(HazardZone.severity.desc())
    
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/red-zones/geojson/export", response_model=dict)
async def export_red_zones_geojson(
    hazard_type: Optional[HazardType] = None,
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    bbox: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    now = datetime.utcnow()
    query = select(HazardZone).where(
        HazardZone.severity.in_([SeverityLevel.HIGH, SeverityLevel.VERY_HIGH]),
        HazardZone.valid_from <= now,
        or_(HazardZone.valid_to.is_(None), HazardZone.valid_to > now)
    )
    
    if hazard_type:
        query = query.where(HazardZone.hazard_type == hazard_type)
    
    if state_code or district_code:
        if district_code:
            district_subq = select(District.id).where(District.code == district_code.upper())
            if state_code:
                district_subq = district_subq.where(
                    District.state_id == select(State.id).where(State.code == state_code.upper()).scalar_subquery()
                )
            district_ids = [row[0] for row in (await db.execute(district_subq)).all()]
            if district_ids:
                district_geoms = select(District.geom).where(District.id.in_(district_ids))
                query = query.where(geofunc.ST_Intersects(HazardZone.geom, district_geoms))
        elif state_code:
            state_geom = select(State.geom).where(State.code == state_code.upper())
            query = query.where(geofunc.ST_Intersects(HazardZone.geom, state_geom))
    
    if bbox:
        try:
            minx, miny, maxx, maxy = map(float, bbox.split(","))
            from geoalchemy2 import WKTElement
            bbox_poly = WKTElement(
                f"SRID=4326;POLYGON(({minx} {miny}, {maxx} {miny}, {maxx} {maxy}, {minx} {maxy}, {minx} {miny}))",
                srid=4326
            )
            query = query.where(geofunc.ST_Intersects(HazardZone.geom, bbox_poly))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Use minx,miny,maxx,maxy"
            )
    
    result = await db.execute(query)
    zones = list(result.scalars().all())
    
    features = []
    for z in zones:
        geom = to_shape(z.geom)
        features.append({
            "type": "Feature",
            "geometry": mapping(geom),
            "properties": {
                "id": str(z.id),
                "hazard_type": z.hazard_type.value,
                "severity": z.severity.value,
                "severity_score": float(z.severity_score) if z.severity_score else None,
                "source": z.source,
                "model_version": z.model_version,
                "confidence_score": float(z.confidence_score) if z.confidence_score else None,
                "valid_from": z.valid_from.isoformat(),
                "valid_to": z.valid_to.isoformat() if z.valid_to else None,
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


# Time Series for Location
@router.get("/hazards/timeseries")
async def get_hazard_timeseries(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    hazard_type: Optional[HazardType] = None,
    days: int = Query(365, ge=1, le=3650),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get hazard history for a specific point location"""
    from geoalchemy2 import WKTElement
    point = WKTElement(f"SRID=4326;POINT({lon} {lat})", srid=4326)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = select(HazardZone).where(
        HazardZone.valid_from >= since,
        geofunc.ST_Contains(HazardZone.geom, point)
    ).order_by(HazardZone.valid_from)
    
    if hazard_type:
        query = query.where(HazardZone.hazard_type == hazard_type)
    
    result = await db.execute(query)
    zones = list(result.scalars().all())
    
    return {
        "location": {"lat": lat, "lon": lon},
        "period_days": days,
        "hazard_type": hazard_type.value if hazard_type else "all",
        "data": [
            {
                "date": z.valid_from.date().isoformat(),
                "hazard_type": z.hazard_type.value,
                "severity": z.severity.value,
                "severity_score": float(z.severity_score) if z.severity_score else None,
                "source": z.source,
                "confidence_score": float(z.confidence_score) if z.confidence_score else None,
            }
            for z in zones
        ]
    }


# Disaster Event Routes
@router.post("/hazards/events", response_model=DisasterEventResponse, status_code=status.HTTP_201_CREATED)
async def create_disaster_event(
    event_data: DisasterEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    from geoalchemy2 import WKTElement
    affected_geom = WKTElement(event_data.affected_geom, srid=4326) if event_data.affected_geom else None
    
    event = DisasterEvent(
        hazard_type=event_data.hazard_type,
        event_name=event_data.event_name,
        event_date=event_data.event_date,
        end_date=event_data.end_date,
        affected_geom=affected_geom,
        affected_habitations=event_data.affected_habitations,
        casualties=event_data.casualties,
        injured=event_data.injured,
        displaced=event_data.displaced,
        houses_damaged=event_data.houses_damaged,
        economic_loss_inr=event_data.economic_loss_inr,
        source=event_data.source,
        verified=event_data.verified,
        metadata_=event_data.metadata,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


@router.get("/hazards/events", response_model=PaginatedResponse[DisasterEventResponse])
async def list_disaster_events(
    hazard_type: Optional[HazardType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    verified: Optional[bool] = None,
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(DisasterEvent).order_by(DisasterEvent.event_date.desc())
    
    if hazard_type:
        query = query.where(DisasterEvent.hazard_type == hazard_type)
    if start_date:
        query = query.where(DisasterEvent.event_date >= start_date)
    if end_date:
        query = query.where(DisasterEvent.event_date <= end_date)
    if verified is not None:
        query = query.where(DisasterEvent.verified == verified)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    events = list(result.scalars().all())
    
    return PaginatedResponse.create(events, total, params)


@router.get("/hazards/events/{event_id}", response_model=DisasterEventResponse)
async def get_disaster_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(DisasterEvent).where(DisasterEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disaster event not found")
    return event


@router.patch("/hazards/events/{event_id}", response_model=DisasterEventResponse)
async def update_disaster_event(
    event_id: uuid.UUID,
    event_data: DisasterEventUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    result = await db.execute(select(DisasterEvent).where(DisasterEvent.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Disaster event not found")
    
    update_data = event_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            event.metadata_ = value
        else:
            setattr(event, key, value)
    
    await db.commit()
    await db.refresh(event)
    return event


# Statistics
@router.get("/hazards/statistics")
async def get_hazard_statistics(
    state_code: Optional[str] = None,
    district_code: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get hazard zone statistics by type and severity"""
    now = datetime.utcnow()
    
    base_query = select(HazardZone).where(
        HazardZone.valid_from <= now,
        or_(HazardZone.valid_to.is_(None), HazardZone.valid_to > now)
    )
    
    if state_code or district_code:
        if district_code:
            district_subq = select(District.id).where(District.code == district_code.upper())
            if state_code:
                district_subq = district_subq.where(
                    District.state_id == select(State.id).where(State.code == state_code.upper()).scalar_subquery()
                )
            district_ids = [row[0] for row in (await db.execute(district_subq)).all()]
            if district_ids:
                district_geoms = select(District.geom).where(District.id.in_(district_ids))
                base_query = base_query.where(geofunc.ST_Intersects(HazardZone.geom, district_geoms))
        elif state_code:
            state_geom = select(State.geom).where(State.code == state_code.upper())
            base_query = base_query.where(geofunc.ST_Intersects(HazardZone.geom, state_geom))
    
    # Count by hazard type and severity
    stats = {}
    for h_type in HazardType:
        for sev in SeverityLevel:
            count_q = select(func.count()).select_from(
                base_query.where(
                    HazardZone.hazard_type == h_type,
                    HazardZone.severity == sev
                ).subquery()
            )
            count = await db.scalar(count_q)
            if count > 0:
                key = f"{h_type.value}_{sev.value}"
                stats[key] = count
    
    # Total red zones
    red_zone_count = await db.scalar(
        select(func.count()).select_from(
            base_query.where(
                HazardZone.severity.in_([SeverityLevel.HIGH, SeverityLevel.VERY_HIGH])
            ).subquery()
        )
    )
    
    return {
        "by_type_severity": stats,
        "total_red_zones": red_zone_count,
        "generated_at": datetime.utcnow().isoformat()
    }