"""Endpoints de empleados.

Tras feedback de Javier 2026-06-09:
- `/validate` queda público (sin auth). El tenant_id viene en el
  body, Qapp se encarga de la comunicación segura.
- El resto de endpoints (`/import`, `/template`, listado) requieren
  `X-Admin-Token` para evitar escrituras desde Internet.
"""
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Header,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.security import require_admin
from app.schemas.employee import (
    EmployeeListItem,
    EmployeeListResponse,
    EmployeeUpdateRequest,
    ImportSummary,
    TenantListResponse,
    TenantSummary,
    ValidateRequest,
    ValidateResponse,
)
from app.services import excel_parser
from app.services.employee_service import (
    delete_employee,
    list_employees,
    list_tenant_names,
    update_employee,
    upsert_employees,
)
from app.services.validation_service import validate_employee

router = APIRouter(prefix="/employees")


@router.post(
    "/validate",
    response_model=ValidateResponse,
    response_model_by_alias=True,
    summary="Validar empleado por DNI o código (público)",
    description=(
        "Endpoint principal consumido por Qapp. Sin auth — el "
        "tenant_id viene en el body. Qapp asegura la comunicación "
        "desde su lado."
    ),
)
async def validate(
    payload: ValidateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    kiosk_name: Annotated[str | None, Header(alias="X-Kiosk-Name")] = None,
) -> ValidateResponse:
    response = await validate_employee(
        session,
        tenant_id=payload.tenant_id,
        identifier_type=payload.identifier_type,
        identifier=payload.identifier,
        kiosk_name=kiosk_name,
    )
    await session.commit()
    return response


@router.get(
    "/template.xlsx",
    summary="Descargar plantilla Excel vacía (admin)",
    dependencies=[Depends(require_admin)],
)
async def download_template() -> Response:
    payload = excel_parser.build_template_xlsx()
    return Response(
        content=payload,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                'attachment; filename="empleados_plantilla.xlsx"'
            )
        },
    )


@router.post(
    "/import",
    response_model=ImportSummary,
    summary="Carga masiva desde Excel (admin)",
    description=(
        "Sube un .xlsx para el tenant indicado (query param). Cada "
        "fila se valida individualmente; las válidas se hacen upsert "
        "por (tenant_id, employee_code), las inválidas se devuelven "
        "en `errors`."
    ),
    dependencies=[Depends(require_admin)],
)
async def import_employees(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
    file: UploadFile = File(..., description="Archivo .xlsx"),
) -> ImportSummary:
    if not file.filename or not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se acepta formato .xlsx",
        )
    raw = await file.read()
    rows, errors = excel_parser.parse_xlsx(raw)
    inserted = updated = 0
    if rows:
        inserted, updated = await upsert_employees(session, tenant_id, rows)
        await session.commit()
    return ImportSummary(
        received=len(rows) + len(errors),
        inserted=inserted,
        updated=updated,
        failed=len(errors),
        errors=errors,
    )


@router.get(
    "",
    response_model=EmployeeListResponse,
    response_model_by_alias=True,
    summary="Listado paginado de empleados (admin)",
    dependencies=[Depends(require_admin)],
)
async def list_(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, description="Búsqueda libre"),
    tenant_name: str | None = Query(
        default=None,
        alias="tenantName",
        description=(
            "Filtra por tenant_name exacto (case-insensitive). "
            "Cadena vacía = solo empleados sin nombre de tenant."
        ),
    ),
) -> EmployeeListResponse:
    total, items = await list_employees(
        session,
        tenant_id,
        limit=limit,
        offset=offset,
        search=q,
        tenant_name=tenant_name,
    )
    return EmployeeListResponse(
        total=total,
        items=[EmployeeListItem.model_validate(it) for it in items],
    )


@router.get(
    "/tenants",
    response_model=TenantListResponse,
    response_model_by_alias=True,
    summary="Nombres de tenant distintos (dropdown del admin)",
    dependencies=[Depends(require_admin)],
)
async def list_tenants(
    session: Annotated[AsyncSession, Depends(get_session)],
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
) -> TenantListResponse:
    rows = await list_tenant_names(session, tenant_id)
    return TenantListResponse(
        items=[
            TenantSummary(tenant_name=name, count=count)
            for name, count in rows
        ],
    )


@router.patch(
    "/{employee_id}",
    response_model=EmployeeListItem,
    response_model_by_alias=True,
    summary="Editar un empleado (admin)",
    dependencies=[Depends(require_admin)],
)
async def update_(
    session: Annotated[AsyncSession, Depends(get_session)],
    employee_id: int,
    payload: EmployeeUpdateRequest,
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
) -> EmployeeListItem:
    # `model_dump` con `exclude_unset` da solo los campos que el
    # cliente mandó — evita sobrescribir con None valores existentes
    # que el usuario no tocó.
    changes = payload.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay campos para actualizar.",
        )
    updated = await update_employee(
        session, tenant_id, employee_id, changes
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado en este tenant.",
        )
    await session.commit()
    return EmployeeListItem.model_validate(updated)


@router.delete(
    "/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un empleado (admin)",
    dependencies=[Depends(require_admin)],
)
async def delete_(
    session: Annotated[AsyncSession, Depends(get_session)],
    employee_id: int,
    tenant_id: int = Query(..., gt=0, alias="tenantId"),
) -> Response:
    deleted = await delete_employee(session, tenant_id, employee_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado en este tenant.",
        )
    await session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
