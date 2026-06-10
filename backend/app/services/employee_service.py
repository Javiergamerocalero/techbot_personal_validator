"""Lógica de empleados: lookup + upsert + listado."""
import logging
from collections.abc import Iterable

from sqlalchemy import func, select
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
) -> tuple[int, list[Employee]]:
    base_filter = Employee.tenant_id == tenant_id
    if search:
        s = f"%{search.strip().lower()}%"
        base_filter = base_filter & (
            func.lower(Employee.full_name).like(s)
            | func.lower(Employee.employee_code).like(s)
            | func.lower(Employee.document_number).like(s)
        )

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
