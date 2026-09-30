from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from geoalchemy2.shape import to_shape
import uuid
from typing import Optional

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_analyst, require_admin, get_pagination_params, require_state_permission
from app.schemas.spatial import (
    StateCreate, StateUpdate, StateResponse,
    DistrictCreate, DistrictUpdate, DistrictResponse,
    HabitationCreate, HabitationUpdate, HabitationResponse, HabitationListResponse,
    PaginationParams, PaginatedResponse,
)
from app.models.spatial import State, District, Habitation
from app.models.auth import User, UserRole

router = APIRouter()


# State Routes
@router.post("/states", response_model=StateResponse, status_code=status.HTTP_201_CREATED)
async def create_state(
    state_data: StateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    from geoalchemy2 import WKTElement
    geom = WKTElement(
        f"SRID=4326;{state_data.geom}", 
        srid=4326
    ) if isinstance(state_data.geom, str) else WKTElement(
        f"SRID=4326;{state_data.geom}", 
        srid=4326
    )
    
    state = State(
        name=state_data.name,
        code=state_data.code.upper(),
        geom=geom,
        metadata_=state_data.metadata,
    )
    db.add(state)
    await db.commit()
    await db.refresh(state)
    return state


@router.get("/states", response_model=PaginatedResponse[StateResponse])
async def list_states(
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(State).order_by(State.name)
    
    # Filter by permitted states
    if not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        permitted_ids = [s.id for s in current_user.permitted_states]
        if permitted_ids:
            query = query.where(State.id.in_(permitted_ids))
    
    total = await db.scalar(
        select(func.count()).select_from(query.subquery())
    )
    
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    states = list(result.scalars().all())
    
    return PaginatedResponse.create(states, total, params)


@router.get("/states/{state_id}", response_model=StateResponse)
async def get_state(
    state_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await require_state_permission(state_id, current_user)
    
    result = await db.execute(select(State).where(State.id == state_id))
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    return state


@router.patch("/states/{state_id}", response_model=StateResponse)
async def update_state(
    state_id: uuid.UUID,
    state_data: StateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await require_state_permission(state_id, current_user)
    
    result = await db.execute(select(State).where(State.id == state_id))
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    update_data = state_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            state.metadata_ = value
        else:
            setattr(state, key, value)
    
    await db.commit()
    await db.refresh(state)
    return state


@router.delete("/states/{state_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_state(
    state_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await require_state_permission(state_id, current_user)
    
    result = await db.execute(select(State).where(State.id == state_id))
    state = result.scalar_one_or_none()
    if not state:
        raise HTTPException(status_code=404, detail="State not found")
    
    await db.delete(state)
    await db.commit()


# District Routes
@router.post("/districts", response_model=DistrictResponse, status_code=status.HTTP_201_CREATED)
async def create_district(
    district_data: DistrictCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    # Verify state access
    await require_state_permission(district_data.state_id, current_user)
    
    from geoalchemy2 import WKTElement
    geom = WKTElement(district_data.geom, srid=4326)
    
    district = District(
        state_id=district_data.state_id,
        name=district_data.name,
        code=district_data.code.upper(),
        geom=geom,
        metadata_=district_data.metadata,
    )
    db.add(district)
    await db.commit()
    await db.refresh(district)
    return district


@router.get("/districts", response_model=PaginatedResponse[DistrictResponse])
async def list_districts(
    state_id: Optional[uuid.UUID] = None,
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(District).options(selectinload(District.state)).order_by(District.name)
    
    if state_id:
        await require_state_permission(state_id, current_user)
        query = query.where(District.state_id == state_id)
    elif not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        permitted_state_ids = [s.id for s in current_user.permitted_states]
        if permitted_state_ids:
            query = query.where(District.state_id.in_(permitted_state_ids))
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    districts = list(result.scalars().all())
    
    return PaginatedResponse.create(districts, total, params)


@router.get("/districts/{district_id}", response_model=DistrictResponse)
async def get_district(
    district_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(District).options(selectinload(District.state)).where(District.id == district_id)
    )
    district = result.scalar_one_or_none()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    await require_state_permission(district.state_id, current_user)
    return district


@router.patch("/districts/{district_id}", response_model=DistrictResponse)
async def update_district(
    district_id: uuid.UUID,
    district_data: DistrictUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    result = await db.execute(
        select(District).options(selectinload(District.state)).where(District.id == district_id)
    )
    district = result.scalar_one_or_none()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    await require_state_permission(district.state_id, current_user)
    
    update_data = district_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            district.metadata_ = value
        else:
            setattr(district, key, value)
    
    await db.commit()
    await db.refresh(district)
    return district


@router.delete("/districts/{district_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_district(
    district_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(District).options(selectinload(District.state)).where(District.id == district_id)
    )
    district = result.scalar_one_or_none()
    if not district:
        raise HTTPException(status_code=404, detail="District not found")
    
    await require_state_permission(district.state_id, current_user)
    await db.delete(district)
    await db.commit()


# Habitation Routes
@router.post("/habitations", response_model=HabitationResponse, status_code=status.HTTP_201_CREATED)
async def create_habitation(
    habitation_data: HabitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    await require_state_permission(habitation_data.state_id, current_user)
    
    # Verify district belongs to state
    result = await db.execute(
        select(District).where(
            District.id == habitation_data.district_id,
            District.state_id == habitation_data.state_id
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="District does not belong to the specified state"
        )
    
    from geoalchemy2 import WKTElement
    geom = WKTElement(habitation_data.geom, srid=4326)
    boundary_geom = WKTElement(habitation_data.boundary_geom, srid=4326) if habitation_data.boundary_geom else None
    
    habitation = Habitation(
        district_id=habitation_data.district_id,
        state_id=habitation_data.state_id,
        name=habitation_data.name,
        geom=geom,
        boundary_geom=boundary_geom,
        population=habitation_data.population,
        households=habitation_data.households,
        literacy_rate=habitation_data.literacy_rate,
        pucca_houses_pct=habitation_data.pucca_houses_pct,
        sc_st_pct=habitation_data.sc_st_pct,
        female_headed_pct=habitation_data.female_headed_pct,
        disability_pct=habitation_data.disability_pct,
        road_access_km=habitation_data.road_access_km,
        healthcare_access_km=habitation_data.healthcare_access_km,
        metadata_=habitation_data.metadata,
    )
    db.add(habitation)
    await db.commit()
    await db.refresh(habitation)
    return habitation


@router.get("/habitations", response_model=PaginatedResponse[HabitationListResponse])
async def list_habitations(
    district_id: Optional[uuid.UUID] = None,
    state_id: Optional[uuid.UUID] = None,
    vulnerability_min: Optional[float] = Query(None, ge=0, le=100),
    vulnerability_max: Optional[float] = Query(None, ge=0, le=100),
    params: PaginationParams = Depends(get_pagination_params),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Habitation).options(
        selectinload(Habitation.district).selectinload(District.state)
    ).order_by(Habitation.name)
    
    if district_id:
        result = await db.execute(
            select(District).options(selectinload(District.state)).where(District.id == district_id)
        )
        district = result.scalar_one_or_none()
        if not district:
            raise HTTPException(status_code=404, detail="District not found")
        await require_state_permission(district.state_id, current_user)
        query = query.where(Habitation.district_id == district_id)
    elif state_id:
        await require_state_permission(state_id, current_user)
        query = query.where(Habitation.state_id == state_id)
    elif not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        permitted_state_ids = [s.id for s in current_user.permitted_states]
        if permitted_state_ids:
            query = query.where(Habitation.state_id.in_(permitted_state_ids))
    
    if vulnerability_min is not None:
        query = query.where(Habitation.composite_vulnerability >= vulnerability_min)
    if vulnerability_max is not None:
        query = query.where(Habitation.composite_vulnerability <= vulnerability_max)
    
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    habitations = list(result.scalars().all())
    
    return PaginatedResponse.create(habitations, total, params)


@router.get("/habitations/{habitation_id}", response_model=HabitationResponse)
async def get_habitation(
    habitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(Habitation)
        .options(selectinload(Habitation.district).selectinload(District.state))
        .where(Habitation.id == habitation_id)
    )
    habitation = result.scalar_one_or_none()
    if not habitation:
        raise HTTPException(status_code=404, detail="Habitation not found")
    
    await require_state_permission(habitation.state_id, current_user)
    return habitation


@router.patch("/habitations/{habitation_id}", response_model=HabitationResponse)
async def update_habitation(
    habitation_id: uuid.UUID,
    habitation_data: HabitationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_analyst),
):
    result = await db.execute(
        select(Habitation)
        .options(selectinload(Habitation.district).selectinload(District.state))
        .where(Habitation.id == habitation_id)
    )
    habitation = result.scalar_one_or_none()
    if not habitation:
        raise HTTPException(status_code=404, detail="Habitation not found")
    
    await require_state_permission(habitation.state_id, current_user)
    
    update_data = habitation_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            habitation.metadata_ = value
        else:
            setattr(habitation, key, value)
    
    await db.commit()
    await db.refresh(habitation)
    return habitation


@router.delete("/habitations/{habitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_habitation(
    habitation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    result = await db.execute(
        select(Habitation)
        .options(selectinload(Habitation.district).selectinload(District.state))
        .where(Habitation.id == habitation_id)
    )
    habitation = result.scalar_one_or_none()
    if not habitation:
        raise HTTPException(status_code=404, detail="Habitation not found")
    
    await require_state_permission(habitation.state_id, current_user)
    await db.delete(habitation)
    await db.commit()


# GeoJSON Export
@router.get("/habitations/geojson/export", response_model=dict)
async def export_habitations_geojson(
    district_id: Optional[uuid.UUID] = None,
    state_id: Optional[uuid.UUID] = None,
    vulnerability_min: Optional[float] = Query(None, ge=0, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Habitation).options(
        selectinload(Habitation.district).selectinload(District.state)
    )
    
    if district_id:
        result = await db.execute(
            select(District).options(selectinload(District.state)).where(District.id == district_id)
        )
        district = result.scalar_one_or_none()
        if not district:
            raise HTTPException(status_code=404, detail="District not found")
        await require_state_permission(district.state_id, current_user)
        query = query.where(Habitation.district_id == district_id)
    elif state_id:
        await require_state_permission(state_id, current_user)
        query = query.where(Habitation.state_id == state_id)
    elif not current_user.is_superuser and current_user.role != UserRole.ADMIN:
        permitted_state_ids = [s.id for s in current_user.permitted_states]
        if permitted_state_ids:
            query = query.where(Habitation.state_id.in_(permitted_state_ids))
    
    if vulnerability_min is not None:
        query = query.where(Habitation.composite_vulnerability >= vulnerability_min)
    
    result = await db.execute(query)
    habitations = list(result.scalars().all())
    
    features = []
    for h in habitations:
        geom = to_shape(h.geom)
        features.append({
            "type": "Feature",
            "geometry": geom.__geo_interface__,
            "properties": {
                "id": str(h.id),
                "name": h.name,
                "district": h.district.name if h.district else None,
                "state": h.district.state.name if h.district and h.district.state else None,
                "population": h.population,
                "composite_vulnerability": float(h.composite_vulnerability) if h.composite_vulnerability else None,
            }
        })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }