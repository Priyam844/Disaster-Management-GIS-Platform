import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, JSON, Table, Column, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from app.models.base import BaseModel
from app.models.spatial import State
import enum


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


# Association table for user-state permissions
user_state_permissions = Table(
    "user_state_permissions",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("state_id", ForeignKey("states.id", ondelete="CASCADE"), primary_key=True),
    Column("role", SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False),
)


class User(BaseModel):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role_enum", create_constraint=True),
        default=UserRole.VIEWER,
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default={}, nullable=False)
    
    # State-level permissions (many-to-many with extra role column)
    permitted_states: Mapped[List["State"]] = relationship(
        "State", 
        secondary=user_state_permissions,
        back_populates="permitted_users"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False, nullable=False)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")
    
    __table_args__ = (
        Index("idx_refresh_token_user_expires", "user_id", "expires_at"),
    )


# Add back-reference to State model
State.permitted_users = relationship(
    "User", 
    secondary=user_state_permissions,
    back_populates="permitted_states"
)