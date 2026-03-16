"""
SQLAlchemy ORM models for SRP Autonomous OS.

Tables
------
core_users       — platform users
organizations    — multi-tenant org boundary
apps             — apps owned by an organisation
app_schemas      — versioned JSON schema for each app
app_records      — real user-submitted data rows
country_rules    — database-driven compliance rules per country
execution_logs   — immutable audit log of every backend action
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, ForeignKey, Integer, String, Text, DateTime, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from .database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# =============================================================================
# core_users
# =============================================================================
class CoreUser(Base):
    __tablename__ = "core_users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email      = Column(Text, unique=True, nullable=False)
    role       = Column(Text, nullable=False, default="owner")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    # Relationships
    organizations = relationship("Organization", back_populates="owner", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":         str(self.id),
            "email":      self.email,
            "role":       self.role,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# organizations
# =============================================================================
class Organization(Base):
    __tablename__ = "organizations"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id    = Column(UUID(as_uuid=True), ForeignKey("core_users.id", ondelete="CASCADE"), nullable=False)
    name        = Column(Text, nullable=False)
    slug        = Column(Text, nullable=False, unique=True)
    custom_domain = Column(Text, nullable=True, unique=True)
    country     = Column(Text)
    industry    = Column(Text)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_now)

    # Relationships
    owner = relationship("CoreUser", back_populates="organizations")
    apps  = relationship("App", back_populates="organization", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":          str(self.id),
            "owner_id":    str(self.owner_id),
            "name":        self.name,
            "slug":        self.slug,
            "custom_domain": self.custom_domain,
            "country":     self.country,
            "industry":    self.industry,
            "created_at":  self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# apps
# =============================================================================
class App(Base):
    __tablename__ = "apps"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id      = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name                 = Column(Text, nullable=False)
    description          = Column(Text)
    status               = Column(Text, nullable=False, default="active")
    modules              = Column(JSONB, nullable=True)  # populated when a business template is applied
    app_type             = Column(Text, nullable=True)   # e.g. 'payroll', 'invoice', 'crm', 'custom'
    blueprint            = Column(JSONB, nullable=True)  # UI blueprint for TemplateRenderer
    architecture_summary = Column(Text, nullable=True)   # AI-generated or human-written architecture description
    created_at           = Column(DateTime(timezone=True), nullable=False, default=_now)

    # Relationships
    organization    = relationship("Organization", back_populates="apps")
    schemas         = relationship("AppSchema",   back_populates="app", cascade="all, delete-orphan")
    records         = relationship("AppRecord",   back_populates="app", cascade="all, delete-orphan")
    execution_logs  = relationship("ExecutionLog", back_populates="app", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id":                   str(self.id),
            "organization_id":      str(self.organization_id),
            "name":                 self.name,
            "description":          self.description,
            "status":               self.status,
            "modules":              self.modules,
            "app_type":             self.app_type,
            "blueprint":            self.blueprint,
            "architecture_summary": self.architecture_summary,
            "created_at":           self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# app_schemas
# =============================================================================
class AppSchema(Base):
    __tablename__ = "app_schemas"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id      = Column(UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    schema_json = Column(JSONB)
    version     = Column(Integer, nullable=False, default=1)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_now)

    app = relationship("App", back_populates="schemas")

    def to_dict(self) -> dict:
        return {
            "id":          str(self.id),
            "app_id":      str(self.app_id),
            "schema_json": self.schema_json,
            "version":     self.version,
            "created_at":  self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# app_records
# =============================================================================
class AppRecord(Base):
    __tablename__ = "app_records"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id      = Column(UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=False)
    record_json = Column(JSONB)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_now)

    app = relationship("App", back_populates="records")

    def to_dict(self) -> dict:
        return {
            "id":          str(self.id),
            "app_id":      str(self.app_id),
            "record_json": self.record_json,
            "created_at":  self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# country_rules
# =============================================================================
class CountryRule(Base):
    __tablename__ = "country_rules"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country     = Column(Text, nullable=False)
    industry    = Column(Text)
    rule_type   = Column(Text, nullable=False)
    rule_json   = Column(JSONB)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=_now)

    def to_dict(self) -> dict:
        return {
            "id":         str(self.id),
            "country":    self.country,
            "industry":   self.industry,
            "rule_type":  self.rule_type,
            "rule_json":  self.rule_json,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
        }


# =============================================================================
# execution_logs
# =============================================================================
class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    app_id        = Column(UUID(as_uuid=True), ForeignKey("apps.id", ondelete="CASCADE"), nullable=True)
    action        = Column(Text, nullable=False)
    status        = Column(Text, nullable=False, default="success")
    response_json = Column(JSONB)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=_now)

    app = relationship("App", back_populates="execution_logs")

    def to_dict(self) -> dict:
        return {
            "id":            str(self.id),
            "app_id":        str(self.app_id) if self.app_id is not None else None,
            "action":        self.action,
            "status":        self.status,
            "response_json": self.response_json,
            "created_at":    self.created_at.isoformat() if self.created_at is not None else None,
        }
