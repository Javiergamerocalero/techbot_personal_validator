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


def _lima_range_bounds(
    date_from: date | None, date_to: date | None
) -> tuple[datetime | None, datetime | None]:
    """[start_utc, end_utc) para un rango de fechas INCLUSIVO en zona Lima.

    `date_to` incluye todo su día (hasta el final), igual que lo esperaría
    quien pide "ventas del 1 al 5": las del día 5 también.
    """
    start_utc = None
    end_utc = None
    if date_from is not None:
        start_lima = datetime.combine(date_from, datetime.min.time(), tzinfo=_LIMA_TZ)
        start_utc = start_lima.astimezone(timezone.utc)
    if date_to is not None:
        # fin exclusivo = inicio del día siguiente, así el día `date_to` entra entero
        end_lima = datetime.combine(date_to, datetime.min.time(), tzinfo=_LIMA_TZ) + timedelta(days=1)
        end_utc = end_lima.astimezone(timezone.utc)
    return start_utc, end_utc


async def list_purchases(
    session: AsyncSession,
    *,
    tenant_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    employee_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[int, int, list[dict]]:
    """Listado de compras del tenant (join con empleado) + total del rango.

    Devuelve (count_total, suma_total_cents, filas). El total es sobre
    TODO el filtro, no solo la página que se devuelve.
    """
    start_utc, end_utc = _lima_range_bounds(date_from, date_to)

    filters = [Purchase.tenant_id == tenant_id]
    if employee_id is not None:
        filters.append(Purchase.employee_id == employee_id)
    if start_utc is not None:
        filters.append(Purchase.purchased_at >= start_utc)
    if end_utc is not None:
        filters.append(Purchase.purchased_at < end_utc)

    totals = await session.execute(
        select(
            func.count(Purchase.id),
            func.coalesce(func.sum(Purchase.amount_cents), 0),
        ).where(*filters)
    )
    count, total_cents = totals.one()

    rows = await session.execute(
        select(
            Purchase.id,
            Purchase.employee_id,
            Employee.full_name,
            Employee.employee_code,
            Employee.document_number,
            Purchase.amount_cents,
            Purchase.currency,
            Purchase.purchased_at,
            Purchase.kiosk_name,
        )
        .join(Employee, Employee.id == Purchase.employee_id)
        .where(*filters)
        .order_by(Purchase.purchased_at.desc(), Purchase.id.desc())
        .limit(limit)
        .offset(offset)
    )
    items = [
        {
            "id": r.id,
            "employee_id": r.employee_id,
            "employee_name": r.full_name,
            "employee_code": r.employee_code,
            "document_number": r.document_number,
            "amount_cents": r.amount_cents,
            "currency": r.currency,
            "purchased_at": r.purchased_at,
            "kiosk_name": r.kiosk_name,
        }
        for r in rows.all()
    ]
    return int(count), int(total_cents), items
