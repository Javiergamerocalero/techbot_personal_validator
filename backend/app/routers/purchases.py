"""Endpoints de compras de empleado en el kiosco.

Per Javier 2026-08-06: el kiosco San Fernando debe registrar cada
compra al servicio para que a futuro se apliquen límites por
empleado (diario / mensual). Estos endpoints son PÚBLICOS igual
que /validate — la seguridad la da Qapp desde su lado.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_admin
from app.schemas.purchase import (
    PurchaseCreateRequest,
    PurchaseCreateResponse,
    PurchaseListResponse,
    PurchaseOut,
    PurchaseRow,
    TodayTotalResponse,
)
from app.services.purchase_export import build_purchases_xlsx
from app.services.purchase_service import (
    PurchaseError,
    list_purchases,
    register_purchase,
    today_total,
)

router = APIRouter(prefix="/employees/{employee_id}/purchases")


@router.post(
    "",
    response_model=PurchaseCreateResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una compra hecha por el empleado en el kiosco",
)
async def create_purchase(
    employee_id: int,
    payload: PurchaseCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PurchaseCreateResponse:
    try:
        purchase = await register_purchase(
            session,
            employee_id=employee_id,
            tenant_id=payload.tenant_id,
            amount_cents=payload.amount_cents,
            currency=payload.currency.upper(),
            kiosk_name=payload.kiosk_name,
            external_reference=payload.external_reference,
        )
    except PurchaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    await session.commit()
    return PurchaseCreateResponse(
        success=True, purchase=PurchaseOut.model_validate(purchase)
    )


@router.get(
    "/today-total",
    response_model=TodayTotalResponse,
    response_model_by_alias=True,
    summary="Total de compras del empleado en el día (zona Lima)",
)
async def get_today_total(
    employee_id: int,
    tenant_id: Annotated[int, Query(alias="tenantId", gt=0)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TodayTotalResponse:
    count, total_cents, day = await today_total(
        session, tenant_id=tenant_id, employee_id=employee_id
    )
    return TodayTotalResponse(
        tenant_id=tenant_id,
        employee_id=employee_id,
        date=day.isoformat(),
        count=count,
        total_cents=total_cents,
    )


# ── Vista de admin: compras del tenant (listado + exportación) ──────────
# Pedido por Javier el 2026-10-01: pantalla para ver y descargar las
# compras por fechas, con subfiltro por empleado o general. Requiere
# X-Admin-Token (igual que el listado de empleados), distinto de los
# endpoints públicos del kiosco de arriba.
admin_router = APIRouter(prefix="/purchases")


@admin_router.get(
    "",
    response_model=PurchaseListResponse,
    response_model_by_alias=True,
    summary="Listado de compras del tenant (admin)",
    dependencies=[Depends(require_admin)],
)
async def list_(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    employee_id: int | None = Query(default=None, gt=0, alias="employeeId"),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
) -> PurchaseListResponse:
    total, total_cents, items = await list_purchases(
        session,
        tenant_id=tenant_id,
        date_from=date_from,
        date_to=date_to,
        employee_id=employee_id,
        limit=limit,
        offset=offset,
    )
    return PurchaseListResponse(
        total=total,
        total_cents=total_cents,
        items=[PurchaseRow.model_validate(it) for it in items],
    )


@admin_router.get(
    "/export.xlsx",
    summary="Descarga las compras filtradas en Excel (admin)",
    dependencies=[Depends(require_admin)],
)
async def export_xlsx(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
    date_from: date | None = Query(default=None, alias="dateFrom"),
    date_to: date | None = Query(default=None, alias="dateTo"),
    employee_id: int | None = Query(default=None, gt=0, alias="employeeId"),
) -> Response:
    # Sin paginar: el Excel trae todo lo que cae en el filtro (tope alto
    # de seguridad para no agotar memoria con un rango enorme).
    total, total_cents, items = await list_purchases(
        session,
        tenant_id=tenant_id,
        date_from=date_from,
        date_to=date_to,
        employee_id=employee_id,
        limit=50000,
        offset=0,
    )
    employee_name = items[0]["employee_name"] if (employee_id and items) else None
    payload = build_purchases_xlsx(
        items,
        total_cents,
        date_from=date_from,
        date_to=date_to,
        employee_name=employee_name,
    )
    filename = "compras"
    if date_from:
        filename += f"_{date_from.isoformat()}"
    if date_to:
        filename += f"_{date_to.isoformat()}"
    return Response(
        content=payload,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}.xlsx"',
        },
    )
