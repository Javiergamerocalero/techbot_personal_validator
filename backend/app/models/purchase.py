"""Purchase: registro de compras del kiosco por empleado.

Per Javier 2026-08-06: cada compra completada en el kiosco San
Fernando debe persistir para poder aplicar límites por empleado
(diario / mensual / etc). Se guarda:

- tenant_id + employee_id (FK -> employees)
- amount en centavos (Integer, sin puntos flotantes)
- currency (default 'PEN')
- purchased_at (UTC, indexado para queries por rango)
- kiosk_name (opcional, para auditoría)
- external_reference (id del pago o ticket en el POS, opcional)

Índice compuesto (tenant_id, employee_id, purchased_at) para
optimizar el cálculo del total del día.
"""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Purchase(Base):
    __tablename__ = "purchases"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    tenant_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    employee_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Monto en centavos para evitar problemas de precisión.
    # S/ 25.50 => 2550.
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)

    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PEN")

    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    kiosk_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    external_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index(
            "ix_purchases_tenant_employee_date",
            "tenant_id",
            "employee_id",
            "purchased_at",
        ),
    )
