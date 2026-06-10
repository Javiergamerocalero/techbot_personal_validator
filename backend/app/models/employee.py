"""Employee + enums asociados.

Schema definitivo confirmado por Javier 2026-06-09 21:03:
- id (autogenerado)
- tenant_id
- tenant_name (varchar 100, nullable)
- employee_code
- document_number
- document_type (enum DNI/CE/PASSPORT)
- full_name (varchar 100)
- status: STRING "Active" / "Inactive"
  (la flag de autorización se evalúa por igualdad con "Active")
- status_reason: varchar(100) nullable, texto libre
  (describe POR QUÉ está Inactive, ej. "Vacaciones desde X")
- created_at, updated_at

Búsqueda principal por (tenant_id, document_number) y
(tenant_id, employee_code). Sin FK a `tenants` — Qapp manda el
tenant_id en cada request.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
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


# Constantes para `status` — string libre con dos valores válidos.
STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"
VALID_STATUSES = (STATUS_ACTIVE, STATUS_INACTIVE)


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

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

    status: Mapped[str] = mapped_column(
        String(16), nullable=False, default=STATUS_ACTIVE
    )
    status_reason: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def is_authorized(self) -> bool:
        """True si el empleado puede comprar (status normalizado a Active)."""
        return (self.status or "").strip().lower() == STATUS_ACTIVE.lower()

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
