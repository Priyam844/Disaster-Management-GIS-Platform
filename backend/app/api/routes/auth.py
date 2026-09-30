from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db.session import get_db
from app.api.deps import get_current_active_user, require_admin, get_pagination_params
from app.schemas.auth import (
    UserCreate, UserUpdate, UserResponse, UserWithPermissions,
    Token, PasswordChangeRequest
)
from app.schemas.base import PaginationParams, PaginatedResponse
from app.services.auth import (
    authenticate_user, create_user, create_tokens_for_user,
    create_refresh_token_record, verify_refresh_token, revoke_refresh_token,
    revoke_all_user_refresh_tokens, get_user_by_id, get_users, update_user, delete_user
)
from app.models.auth import User, UserRole

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = await create_tokens_for_user(user)
    await create_refresh_token_record(
        db, user.id, tokens.refresh_token,
        user_agent=request.headers.get("user-agent"),
    )
    
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )
    
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_token(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )
    
    token_record = await verify_refresh_token(db, refresh_token)
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    user = await get_user_by_id(db, token_record.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Revoke old refresh token
    await revoke_refresh_token(db, refresh_token)
    
    # Create new tokens
    tokens = await create_tokens_for_user(user)
    await create_refresh_token_record(
        db, user.id, tokens.refresh_token,
        user_agent=request.headers.get("user-agent"),
    )
    
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )
    
    return tokens


@router.post("/logout")
async def logout(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)
    
    response.delete_cookie(key="refresh_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserWithPermissions)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    return UserWithPermissions(
        **current_user.__dict__,
        permitted_states=[
            {"id": str(s.id), "name": s.name, "code": s.code}
            for s in current_user.permitted_states
        ],
        permissions=get_user_permissions(current_user),
    )


def get_user_permissions(user: User) -> List[str]:
    permissions = []
    if user.is_superuser:
        permissions.append("superuser")
    if user.role == UserRole.ADMIN:
        permissions.extend(["admin", "manage_users", "manage_data", "manage_models"])
    if user.role in [UserRole.ADMIN, UserRole.ANALYST]:
        permissions.extend(["read_analytics", "run_models", "export_data"])
    permissions.append("read_data")
    return permissions


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_new_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    # Check if username or email exists
    from sqlalchemy import select
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )
    
    user = await create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        full_name=user_data.full_name,
        role=user_data.role,
        permitted_state_ids=user_data.permitted_state_ids,
    )
    return user


@router.get("", response_model=PaginatedResponse[UserResponse])
async def list_users(
    params: PaginationParams = Depends(get_pagination_params),
    role: UserRole = None,
    is_active: bool = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await get_users(db, params, role, is_active)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: uuid.UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    user = await update_user(db, user_id, **user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself",
        )
    
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    from app.services.auth import verify_password, get_password_hash
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    # Revoke all other sessions
    await revoke_all_user_refresh_tokens(db, current_user.id)
    
    return {"message": "Password changed successfully. Please log in again."}