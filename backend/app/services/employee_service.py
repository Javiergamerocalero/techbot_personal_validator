"""Lógica de empleados: lookup + upsert + listado + edit + delete."""
import logging
from collections.abc import Iterable

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select, update as sa_update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.employee import Employee
from app.models.validation_log import IdentifierType
from app.schemas.employee import EmployeeImportRow

log = logging.getLogger(__name__)


async def find_employee(
    session: AsyncSession,
    tenant_id: int,
    identifier_type: IdentifierType,
    identifier: str,
) -> Employee | None:
    """Busca un empleado del tenant por DNI o código."""
    column = (
        Employee.document_number
        if identifier_type == IdentifierType.DNI
        else Employee.employee_code
    )
    stmt = select(Employee).where(
        Employee.tenant_id == tenant_id,
        column == identifier.strip(),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def upsert_employees(
    session: AsyncSession,
    tenant_id: int,
    rows: Iterable[EmployeeImportRow],
) -> tuple[int, int]:
    """Inserta o actualiza filas. Devuelve (inserted, updated).

    Usa INSERT ... ON CONFLICT del dialecto Postgres para hacer el
    upsert por (tenant_id, employee_code) — la unique constraint
    coincide con `uq_employee_tenant_code`.
    """
    rows = list(rows)
    if not rows:
        return 0, 0

    payload = [
        {
            "tenant_id": tenant_id,
            "tenant_name": r.tenant_name,
            "employee_code": r.employee_code,
            "document_number": r.document_number,
            "document_type": r.document_type.value,
            "full_name": r.full_name,
            "status": r.status,
            "status_reason": r.status_reason,
        }
        for r in rows
    ]

    stmt = pg_insert(Employee.__table__).values(payload)
    update_cols = {
        c.name: stmt.excluded[c.name]
        for c in Employee.__table__.columns
        if c.name
        not in {"id", "tenant_id", "employee_code", "created_at"}
    }
    update_cols["updated_at"] = func.now()
    upsert_stmt = stmt.on_conflict_do_update(
        constraint="uq_employee_tenant_code",
        set_=update_cols,
    ).returning(Employee.id, Employee.created_at, Employee.updated_at)
    result = await session.execute(upsert_stmt)
    rows_back = result.all()

    inserted = sum(1 for r in rows_back if r.created_at == r.updated_at)
    updated = len(rows_back) - inserted
    log.info(
        "employees.upsert",
        extra={"tenant_id": tenant_id, "inserted": inserted, "updated": updated},
    )
    return inserted, updated


async def list_employees(
    session: AsyncSession,
    tenant_id: int,
    *,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    tenant_name: str | None = None,
) -> tuple[int, list[Employee]]:
    base_filter = Employee.tenant_id == tenant_id
    if search:
        s = f"%{search.strip().lower()}%"
        base_filter = base_filter & (
            func.lower(Employee.full_name).like(s)
            | func.lower(Employee.employee_code).like(s)
            | func.lower(Employee.document_number).like(s)
        )
    if tenant_name is not None:
        # tenant_name puede ser cadena vacía como forma de decir "sin
        # nombre asignado". Comparamos case-insensitive contra el valor
        # limpio, y NULL == "" para que el filtro "Sin nombre" del UI
        # traiga las rows con tenant_name IS NULL.
        clean = tenant_name.strip()
        if clean:
            base_filter = base_filter & (
                func.lower(Employee.tenant_name) == clean.lower()
            )
        else:
            base_filter = base_filter & (Employee.tenant_name.is_(None))

    total = await session.scalar(
        select(func.count()).select_from(Employee).where(base_filter)
    )
    items_result = await session.execute(
        select(Employee)
        .where(base_filter)
        .order_by(Employee.full_name)
        .limit(limit)
        .offset(offset)
    )
    return int(total or 0), list(items_result.scalars())


async def get_employee(
    session: AsyncSession, tenant_id: int, employee_id: int
) -> Employee | None:
    """Lookup por PK, scoped al tenant para evitar cross-tenant edits.

    Todos los endpoints admin siguen recibiendo el tenant_id explícito
    (mismo patrón que list/import) — así la unicidad la garantiza el
    caller y no tenemos que confiar en el JWT / header solo.
    """
    result = await session.execute(
        select(Employee).where(
            Employee.tenant_id == tenant_id,
            Employee.id == employee_id,
        )
    )
    return result.scalar_one_or_none()


async def update_employee(
    session: AsyncSession,
    tenant_id: int,
    employee_id: int,
    changes: dict,
) -> Employee | None:
    """Actualiza solo las columnas presentes en `changes`.

    Devuelve la row actualizada, o None si no existía (para que el
    router devuelva 404). Los enums vienen ya validados por el
    Pydantic schema — acá solo escribimos.
    """
    if not changes:
        return await get_employee(session, tenant_id, employee_id)

    # Serializar enums a su .value para el UPDATE.
    payload = {}
    for k, v in changes.items():
        if hasattr(v, "value"):
            payload[k] = v.value
        else:
            payload[k] = v
    payload["updated_at"] = func.now()

    stmt = (
        sa_update(Employee)
        .where(
            Employee.tenant_id == tenant_id,
            Employee.id == employee_id,
        )
        .values(**payload)
        .returning(Employee)
    )
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    if row is not None:
        log.info(
            "employees.update",
            extra={
                "tenant_id": tenant_id,
                "employee_id": employee_id,
                "fields": list(changes.keys()),
            },
        )
    return row


async def delete_employee(
    session: AsyncSession, tenant_id: int, employee_id: int
) -> bool:
    """Borra la row. Devuelve True si borró algo, False si no existía."""
    stmt = sa_delete(Employee).where(
        Employee.tenant_id == tenant_id,
        Employee.id == employee_id,
    )
    result = await session.execute(stmt)
    deleted = (result.rowcount or 0) > 0
    if deleted:
        log.info(
            "employees.delete",
            extra={"tenant_id": tenant_id, "employee_id": employee_id},
        )
    return deleted


async def list_tenant_names(
    session: AsyncSession, tenant_id: int
) -> list[tuple[str | None, int]]:
    """Distintos valores de `tenant_name` presentes en la data del
    tenant_id activo, con el count por cada uno. Se usa para poblar
    el dropdown "Filtrar por tenant" del admin web.

    Devuelve una lista de tuplas `(tenant_name, count)`; el nombre
    puede ser `None` si el operador no lo cargó en la plantilla.
    """
    stmt = (
        select(Employee.tenant_name, func.count(Employee.id))
        .where(Employee.tenant_id == tenant_id)
        .group_by(Employee.tenant_name)
        .order_by(func.count(Employee.id).desc())
    )
    result = await session.execute(stmt)
    return [(name, int(count)) for name, count in result.all()]
