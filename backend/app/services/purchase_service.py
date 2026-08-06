"""Lógica de compras del kiosco por empleado.

- register_purchase: valida que el empleado exista + esté Active +
  pertenezca al tenant, persiste el row de purchases.
- today_total: suma `amount_cents` de compras del empleado en el
  día actual (zona America/Lima) — sirve para checks de límite.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import STATUS_ACTIVE, Employee
from app.models.purchase import Purchase

log = logging.getLogger(__name__)

# Zona horaria de Lima (Perú) — UTC-5 sin horario de verano.
# Suficiente para agrupar compras "del día" sin traer pytz/zoneinfo.
_LIMA_OFFSET = timedelta(hours=-5)
_LIMA_TZ = timezone(_LIMA_OFFSET, name="America/Lima")


class PurchaseError(Exception):
    """Error de validación al registrar compra (empleado inválido,
    inactivo o de otro tenant)."""


async def register_purchase(
    session: AsyncSession,
    *,
    employee_id: int,
    tenant_id: int,
    amount_cents: int,
    currency: str,
    kiosk_name: str | None,
    external_reference: str | None,
) -> Purchase:
    """Persiste una compra tras validar tenant + empleado activo."""
    stmt = select(Employee).where(Employee.id == employee_id)
    result = await session.execute(stmt)
    employee = result.scalar_one_or_none()
    if employee is None:
        raise PurchaseError("Empleado no encontrado")
    if employee.tenant_id != tenant_id:
        raise PurchaseError("Empleado no pertenece al tenant indicado")
    if employee.status != STATUS_ACTIVE:
        raise PurchaseError("Empleado no autorizado (status != Active)")

    purchase = Purchase(
        tenant_id=tenant_id,
        employee_id=employee.id,
        amount_cents=amount_cents,
        currency=currency,
        kiosk_name=kiosk_name,
        external_reference=external_reference,
    )
    session.add(purchase)
    await session.flush()  # asigna id + purchased_at server_default
    await session.refresh(purchase)
    log.info(
        "purchase.registered",
        extra={
            "tenant_id": tenant_id,
            "employee_id": employee.id,
            "amount_cents": amount_cents,
            "kiosk_name": kiosk_name,
        },
    )
    return purchase


def _lima_day_bounds(target: date) -> tuple[datetime, datetime]:
    """Devuelve [start_utc, end_utc) del día `target` en zona Lima."""
    start_lima = datetime.combine(target, datetime.min.time(), tzinfo=_LIMA_TZ)
    end_lima = start_lima + timedelta(days=1)
    return start_lima.astimezone(timezone.utc), end_lima.astimezone(timezone.utc)


async def today_total(
    session: AsyncSession,
    *,
    tenant_id: int,
    employee_id: int,
) -> tuple[int, int, date]:
    """Devuelve (count, total_cents, day_in_lima) del empleado hoy."""
    today = datetime.now(_LIMA_TZ).date()
    start_utc, end_utc = _lima_day_bounds(today)

    stmt = select(
        func.count(Purchase.id),
        func.coalesce(func.sum(Purchase.amount_cents), 0),
    ).where(
        Purchase.tenant_id == tenant_id,
        Purchase.employee_id == employee_id,
        Purchase.purchased_at >= start_utc,
        Purchase.purchased_at < end_utc,
    )
    result = await session.execute(stmt)
    count, total = result.one()
    return int(count), int(total), today
