from datetime import datetime, timedelta
from typing import Optional
import uuid
import hashlib
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.auth import User, RefreshToken, UserRole
from app.schemas.auth import TokenPayload, Token
from app.schemas.base import PaginationParams, PaginatedResponse

settings = get_settings()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def decode_token(token: str) -> Optional[TokenPayload]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return TokenPayload(**payload)
    except JWTError:
        return None


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    result = await db.execute(
        select(User).where(
            (User.username == username) | (User.email == username),
            User.is_active
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    password: str,
    full_name: Optional[str] = None,
    role: UserRole = UserRole.VIEWER,
    permitted_state_ids: Optional[list[uuid.UUID]] = None,
    is_superuser: bool = False,
) -> User:
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.flush()
    
    if permitted_state_ids:
        from app.models.spatial import State
        states = await db.execute(
            select(State).where(State.id.in_(permitted_state_ids))
        )
        user.permitted_states = list(states.scalars().all())
    
    await db.commit()
    await db.refresh(user)
    return user


async def create_refresh_token_record(
    db: AsyncSession,
    user_id: uuid.UUID,
    token: str,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> RefreshToken:
    token_hash = hash_token(token)
    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    db.add(refresh_token)
    await db.commit()
    await db.refresh(refresh_token)
    return refresh_token


async def verify_refresh_token(db: AsyncSession, token: str) -> Optional[RefreshToken]:
    token_hash = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > datetime.utcnow()
        )
    )
    return result.scalar_one_or_none()


async def revoke_refresh_token(db: AsyncSession, token: str) -> bool:
    token_hash = hash_token(token)
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    refresh_token = result.scalar_one_or_none()
    if refresh_token:
        refresh_token.revoked = True
        await db.commit()
        return True
    return False


async def revoke_all_user_refresh_tokens(db: AsyncSession, user_id: uuid.UUID) -> int:
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False)
        )
    )
    tokens = list(result.scalars().all())
    for token in tokens:
        token.revoked = True
    await db.commit()
    return len(tokens)


async def create_tokens_for_user(user: User) -> Token:
    permitted_state_ids = [str(s.id) for s in user.permitted_states]
    access_token_data = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
        "permitted_state_ids": permitted_state_ids,
        "is_superuser": user.is_superuser,
    }
    refresh_token_data = {
        "sub": str(user.id),
        "type": "refresh",
    }
    
    access_token = create_access_token(access_token_data)
    refresh_token = create_refresh_token(refresh_token_data)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    params: PaginationParams,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
) -> PaginatedResponse[User]:
    query = select(User)
    
    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    
    query = query.order_by(User.created_at.desc())
    
    # Count total
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)
    
    # Paginate
    query = query.offset(params.offset).limit(params.limit)
    result = await db.execute(query)
    users = list(result.scalars().all())
    
    return PaginatedResponse.create(users, total, params)


async def update_user(
    db: AsyncSession,
    user_id: uuid.UUID,
    **kwargs,
) -> Optional[User]:
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            if key == "permitted_state_ids":
                from app.models.spatial import State
                states = await db.execute(
                    select(State).where(State.id.in_(value))
                )
                user.permitted_states = list(states.scalars().all())
            else:
                setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    return True


# Permission checking
def check_state_permission(user: User, state_id: uuid.UUID) -> bool:
    if user.is_superuser:
        return True
    return any(s.id == state_id for s in user.permitted_states)


def check_admin(user: User) -> bool:
    return user.is_superuser or user.role == UserRole.ADMIN


def check_analyst(user: User) -> bool:
    return user.is_superuser or user.role in [UserRole.ADMIN, UserRole.ANALYST]