"""Endpoints de compras de empleado en el kiosco.

Per Javier 2026-08-06: el kiosco San Fernando debe registrar cada
compra al servicio para que a futuro se apliquen límites por
empleado (diario / mensual). Estos endpoints son PÚBLICOS igual
que /validate — la seguridad la da Qapp desde su lado.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.schemas.purchase import (
    PurchaseCreateRequest,
    PurchaseCreateResponse,
    PurchaseOut,
    TodayTotalResponse,
)
from app.services.purchase_service import (
    PurchaseError,
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
