"""Endpoints administrativos: alta + listado + rotación de API key.

Acceso protegido por X-Admin-Token (ver core/security.py).
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import (
    generate_api_key,
    require_admin,
)
from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate, TenantCreated, TenantOut

router = APIRouter(prefix="/tenants", dependencies=[Depends(require_admin)])


@router.post(
    "",
    response_model=TenantCreated,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    summary="Crear tenant + emitir API key",
)
async def create_tenant(
    payload: TenantCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TenantCreated:
    raw_key, hashed = generate_api_key()
    tenant = Tenant(name=payload.name, slug=payload.slug, api_key_hash=hashed)
    session.add(tenant)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tenant slug ya existe",
        )
    await session.refresh(tenant)
    return TenantCreated(
        tenant=TenantOut.model_validate(tenant), api_key=raw_key
    )


@router.get(
    "",
    response_model=list[TenantOut],
    response_model_by_alias=True,
    summary="Listado de tenants",
)
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[TenantOut]:
    result = await session.execute(select(Tenant).order_by(Tenant.name))
    return [TenantOut.model_validate(t) for t in result.scalars()]


@router.post(
    "/{tenant_id}/rotate",
    response_model=TenantCreated,
    response_model_by_alias=True,
    summary="Rotar API key de un tenant",
)
async def rotate_key(
    tenant_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> TenantCreated:
    result = await session.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no existe"
        )
    raw_key, hashed = generate_api_key()
    tenant.api_key_hash = hashed
    await session.commit()
    await session.refresh(tenant)
    return TenantCreated(
        tenant=TenantOut.model_validate(tenant), api_key=raw_key
    )
