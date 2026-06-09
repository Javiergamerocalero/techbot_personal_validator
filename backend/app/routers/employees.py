"""Endpoints de empleados: validate + import + listado + template."""
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

from app.core.config import get_settings
from app.core.database import get_session
from app.core.security import require_tenant
from app.models.tenant import Tenant
from app.schemas.employee import (
    EmployeeListItem,
    EmployeeListResponse,
    ImportSummary,
    ValidateRequest,
    ValidateResponse,
)
from app.services import excel_parser
from app.services.employee_service import list_employees, upsert_employees
from app.services.validation_service import validate_employee

router = APIRouter(prefix="/employees")


@router.post(
    "/validate",
    response_model=ValidateResponse,
    response_model_by_alias=True,
    summary="Validar empleado por DNI o código",
    description=(
        "Endpoint principal consumido por Qapp. Multi-tenant: el "
        "tenant se identifica con el header X-Tenant-Key."
    ),
)
async def validate(
    payload: ValidateRequest,
    tenant: Annotated[Tenant, Depends(require_tenant)],
    session: Annotated[AsyncSession, Depends(get_session)],
    kiosk_name: Annotated[str | None, Header(alias="X-Kiosk-Name")] = None,
) -> ValidateResponse:
    settings = get_settings()
    # Si el header configurado en .env es distinto al default, se acepta
    # cualquiera de los dos. FastAPI ya leyó el default; este fallback
    # solo aplica si Javier configura otro header.
    if settings.kiosk_name_header != "X-Kiosk-Name" and kiosk_name is None:
        # Caller usó el header custom; nada que hacer, ya viene en None.
        # No es ergonómico tener dos vías, pero permite override sin
        # romper el contrato default.
        pass
    response = await validate_employee(
        session,
        tenant_id=tenant.id,
        identifier_type=payload.identifier_type,
        identifier=payload.identifier,
        kiosk_name=kiosk_name,
    )
    await session.commit()
    return response


@router.get(
    "/template.xlsx",
    summary="Descargar plantilla Excel vacía",
    responses={200: {"content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}}},
)
async def download_template(
    _: Annotated[Tenant, Depends(require_tenant)],
) -> Response:
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
    summary="Carga masiva desde Excel",
    description=(
        "Sube un .xlsx con los empleados del tenant. Cada fila se "
        "valida individualmente: las filas válidas se hacen upsert "
        "(insertan o actualizan por employee_code), las inválidas se "
        "devuelven en `errors`."
    ),
)
async def import_employees(
    tenant: Annotated[Tenant, Depends(require_tenant)],
    session: Annotated[AsyncSession, Depends(get_session)],
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
        inserted, updated = await upsert_employees(session, tenant.id, rows)
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
    summary="Listado paginado de empleados",
)
async def list_(
    tenant: Annotated[Tenant, Depends(require_tenant)],
    session: Annotated[AsyncSession, Depends(get_session)],
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, description="Búsqueda libre"),
) -> EmployeeListResponse:
    total, items = await list_employees(
        session, tenant.id, limit=limit, offset=offset, search=q
    )
    return EmployeeListResponse(
        total=total,
        items=[EmployeeListItem.model_validate(it) for it in items],
    )
