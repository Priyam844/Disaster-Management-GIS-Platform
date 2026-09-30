from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.core.config import get_settings
from app.services.auth import decode_token, check_state_permission, check_admin, check_analyst
from app.models.auth import User

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_payload = decode_token(credentials.credentials)
    if not token_payload or token_payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = uuid.UUID(token_payload.sub)
    result = await db.execute(select(User).where(User.id == user_id, User.is_active))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if not check_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_analyst(current_user: User = Depends(get_current_active_user)) -> User:
    if not check_analyst(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst privileges required",
        )
    return current_user


async def require_state_permission(
    state_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
) -> User:
    if not check_state_permission(current_user, state_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this state",
        )
    return current_user


def get_optional_user(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> Optional[User]:
    if not credentials:
        return None
    
    token_payload = decode_token(credentials.credentials)
    if not token_payload or token_payload.type != "access":
        return None
    
    # Note: This would need async execution, so in practice use a separate dependency
    return None


class PaginationParams:
    def __init__(self, page: int = 1, size: int = 50):
        self.page = max(1, page)
        self.size = min(100, max(1, size))
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        return self.size


def get_pagination_params(page: int = 1, size: int = 50) -> PaginationParams:
    return PaginationParams(page=page, size=size)