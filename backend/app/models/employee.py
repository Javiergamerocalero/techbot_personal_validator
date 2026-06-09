"""Employee + enums asociados.

Schema definido con Javier 2026-06-09. Multi-tenant: cada empleado
pertenece a un tenant. Búsqueda principal por (tenant_id, document_number)
y (tenant_id, employee_code).
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Tipos de documento aceptados en `document_number`.

    Si el cliente trae solo DNI ahora, la lista se queda en eso y se
    extiende cuando aparezca otro caso.
    """

    DNI = "DNI"
    CE = "CE"  # Carné de Extranjería
    PASSPORT = "PASSPORT"


class StatusReason(str, enum.Enum):
    """Catálogo cerrado de razones de estado (Javier 2026-06-09).

    Mantener acotado — la lista exacta la confirma Javier antes del
    despliegue. Los valores acá son un placeholder razonable; si
    cambian se agrega una migration que cambia el enum.
    """

    ACTIVE = "ACTIVE"
    DESVINCULADO = "DESVINCULADO"
    SUSPENDIDO = "SUSPENDIDO"
    VACACIONES = "VACACIONES"
    OTRO = "OTRO"


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    tenant_id: Mapped[int] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    employee_code: Mapped[str] = mapped_column(String(64), nullable=False)
    document_number: Mapped[str] = mapped_column(String(32), nullable=False)
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", native_enum=False),
        nullable=False,
        default=DocumentType.DNI,
    )

    full_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Bool de autorización inmediata: si False el empleado NO puede
    # comprar (independiente de status_reason).
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

    tenant = relationship("Tenant", lazy="joined")

    __table_args__ = (
        # Unicidad fuerte: dentro de un tenant, no puede haber dos
        # empleados con el mismo código ni con el mismo documento.
        UniqueConstraint(
            "tenant_id", "employee_code", name="uq_employee_tenant_code"
        ),
        UniqueConstraint(
            "tenant_id", "document_number", name="uq_employee_tenant_doc"
        ),
        # Índices compuestos para los lookups del /validate. Postgres
        # ya usa el unique para el filter, pero los dejamos explícitos
        # para que el plan sea predecible y por consistencia.
        Index("ix_employee_tenant_code", "tenant_id", "employee_code"),
        Index("ix_employee_tenant_doc", "tenant_id", "document_number"),
    )
