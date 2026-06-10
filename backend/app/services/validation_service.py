"""Lógica del endpoint /validate."""
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.validation_log import (
    IdentifierType,
    ValidationLog,
    ValidationResult,
)
from app.schemas.employee import EmployeeOut, ValidateResponse
from app.services.employee_service import find_employee

log = logging.getLogger(__name__)

_MSG_AUTHORIZED = "Empleado validado"
_MSG_NOT_AUTHORIZED = "Empleado no autorizado para realizar compras"


async def validate_employee(
    session: AsyncSession,
    *,
    tenant_id: int,
    identifier_type: IdentifierType,
    identifier: str,
    kiosk_name: str | None = None,
) -> ValidateResponse:
    """Caso de uso completo del /validate.

    Devuelve la respuesta lista para serializar + persiste el log.
    El caller solo tiene que `await session.commit()` para cerrar el
    write.
    """
    employee = await find_employee(
        session, tenant_id, identifier_type, identifier
    )

    if employee is None:
        await _log(
            session,
            tenant_id=tenant_id,
            identifier_type=identifier_type,
            identifier=identifier,
            result=ValidationResult.NOT_FOUND,
            kiosk_name=kiosk_name,
            employee_id=None,
        )
        return ValidateResponse(
            success=False, employee=None, message=_MSG_NOT_AUTHORIZED
        )

    if not employee.status:
        await _log(
            session,
            tenant_id=tenant_id,
            identifier_type=identifier_type,
            identifier=identifier,
            result=ValidationResult.NOT_AUTHORIZED,
            kiosk_name=kiosk_name,
            employee_id=employee.id,
        )
        return ValidateResponse(
            success=False, employee=None, message=_MSG_NOT_AUTHORIZED
        )

    await _log(
        session,
        tenant_id=tenant_id,
        identifier_type=identifier_type,
        identifier=identifier,
        result=ValidationResult.AUTHORIZED,
        kiosk_name=kiosk_name,
        employee_id=employee.id,
    )
    return ValidateResponse(
        success=True,
        employee=EmployeeOut.model_validate(employee),
        message=_MSG_AUTHORIZED,
    )


async def _log(
    session: AsyncSession,
    *,
    tenant_id: int,
    identifier_type: IdentifierType,
    identifier: str,
    result: ValidationResult,
    kiosk_name: str | None,
    employee_id: int | None,
) -> None:
    entry = ValidationLog(
        tenant_id=tenant_id,
        identifier_type=identifier_type,
        identifier=identifier,
        result=result,
        kiosk_name=kiosk_name,
        employee_id=employee_id,
    )
    session.add(entry)
    log.info(
        "validation",
        extra={
            "tenant_id": tenant_id,
            "identifier_type": identifier_type.value,
            "identifier": identifier,
            "result": result.value,
            "kiosk_name": kiosk_name or "unknown",
        },
    )
