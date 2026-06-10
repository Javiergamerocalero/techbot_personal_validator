"""ValidationLog: auditoría de cada consulta a /validate.

Pedido por Javier 2026-06-09:
- fecha y hora
- identificador consultado
- resultado de la validación
- nombre del quiosco
"""
import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class IdentifierType(str, enum.Enum):
    DNI = "DNI"
    EMPLOYEE_CODE = "EMPLOYEE_CODE"


class ValidationResult(str, enum.Enum):
    AUTHORIZED = "AUTHORIZED"
    NOT_FOUND = "NOT_FOUND"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    ERROR = "ERROR"


class ValidationLog(Base):
    __tablename__ = "validation_logs"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    # tenant_id sin FK — Qapp manda el tenant en cada request, no
    # tenemos tabla `tenants` que valide.
    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    identifier_type: Mapped[IdentifierType] = mapped_column(
        Enum(IdentifierType, name="identifier_type", native_enum=False),
        nullable=False,
    )
    identifier: Mapped[str] = mapped_column(String(64), nullable=False)
    result: Mapped[ValidationResult] = mapped_column(
        Enum(ValidationResult, name="validation_result", native_enum=False),
        nullable=False,
    )

    kiosk_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    employee_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_validation_tenant_created", "tenant_id", "created_at"),
    )
