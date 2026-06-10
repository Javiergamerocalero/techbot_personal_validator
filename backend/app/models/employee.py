"""Employee + enums asociados.

Schema simplificado tras feedback de Javier 2026-06-09:
- `tenant_id` queda como int simple (sin FK) — Qapp manda el
  tenant_id en cada request, no hay tabla `tenants` que validar.
- `status_reason` reducido a ACTIVE / INACTIVE (era catálogo de 5
  valores; el cliente prefiere no complicar).
- Búsqueda principal por (tenant_id, document_number) y
  (tenant_id, employee_code).
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DocumentType(str, enum.Enum):
    DNI = "DNI"
    CE = "CE"  # Carné de Extranjería
    PASSPORT = "PASSPORT"


class StatusReason(str, enum.Enum):
    """Catálogo cerrado, confirmado por Javier 2026-06-09."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # Sin FK: Qapp identifica al tenant y lo manda en el body del
    # request. Si necesitamos rastrear orígenes de cada tenant
    # agregamos una tabla separada después.
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    tenant_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    document_number: Mapped[str] = mapped_column(String(32), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", native_enum=False),
        nullable=False,
        default=DocumentType.DNI,
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)

    status: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    status_reason: Mapped[StatusReason] = mapped_column(
        Enum(StatusReason, name="status_reason", native_enum=False),
        nullable=False,
        default=StatusReason.ACTIVE,
    )

    cost_center: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "employee_code", name="uq_employee_tenant_code"
        ),
        UniqueConstraint(
            "tenant_id", "document_number", name="uq_employee_tenant_doc"
        ),
        Index("ix_employee_tenant_code", "tenant_id", "employee_code"),
        Index("ix_employee_tenant_doc", "tenant_id", "document_number"),
    )
