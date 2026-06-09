"""Pydantic schemas para Employee.

In: ValidateRequest, EmployeeImportRow.
Out: ValidateResponse, EmployeeOut, EmployeeListResponse.
"""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.employee import DocumentType, StatusReason
from app.models.validation_log import IdentifierType


# ── In ──────────────────────────────────────────────────────────────────
class ValidateRequest(BaseModel):
    """Lo que manda Qapp para validar un empleado.

    Shape exacto del documento original de Javier:
        { "identifierType": "DNI", "identifier": "12345678" }
    """

    identifier_type: IdentifierType = Field(
        alias="identifierType",
        description="DNI o EMPLOYEE_CODE — define qué columna se consulta",
    )
    identifier: Annotated[str, Field(min_length=1, max_length=64)]

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("identifier")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


# ── Out ─────────────────────────────────────────────────────────────────
class EmployeeOut(BaseModel):
    """Versión consumible del empleado, alineada con el doc de Javier."""

    employee_code: str = Field(alias="employeeCode")
    document_number: str = Field(alias="documentNumber")
    full_name: str = Field(alias="fullName")
    status: bool
    status_reason: StatusReason = Field(alias="statusReason")
    cost_center: str | None = Field(default=None, alias="costCenter")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ValidateResponse(BaseModel):
    success: bool
    employee: EmployeeOut | None = None
    message: str

    model_config = ConfigDict(populate_by_name=True)


class EmployeeListItem(BaseModel):
    id: int
    employee_code: str = Field(alias="employeeCode")
    document_number: str = Field(alias="documentNumber")
    document_type: DocumentType = Field(alias="documentType")
    full_name: str = Field(alias="fullName")
    status: bool
    status_reason: StatusReason = Field(alias="statusReason")
    cost_center: str | None = Field(default=None, alias="costCenter")
    updated_at: datetime = Field(alias="updatedAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class EmployeeListResponse(BaseModel):
    total: int
    items: list[EmployeeListItem]


# ── Import ──────────────────────────────────────────────────────────────
class EmployeeImportRow(BaseModel):
    """Una fila válida del Excel — el parser convierte cada row a esto."""

    employee_code: str
    document_number: str
    document_type: DocumentType = DocumentType.DNI
    full_name: str
    status: bool = True
    status_reason: StatusReason = StatusReason.ACTIVE
    cost_center: str | None = None


class ImportError(BaseModel):
    """Una fila que el parser rechazó. Muestra al usuario qué corregir."""

    row: int
    column: str | None = None
    reason: str


class ImportSummary(BaseModel):
    """Respuesta del POST /employees/import."""

    received: int
    inserted: int
    updated: int
    failed: int
    errors: list[ImportError]
