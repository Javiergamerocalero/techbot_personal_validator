"""Pydantic schemas para Employee."""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.employee import DocumentType, StatusReason
from app.models.validation_log import IdentifierType


# ── In ──────────────────────────────────────────────────────────────────
class ValidateRequest(BaseModel):
    """Lo que manda Qapp para validar un empleado.

    Post-cambio Javier 2026-06-09: el tenant_id viene en el body
    (antes se derivaba de X-Tenant-Key). El endpoint queda público
    porque Qapp ya asegura la comunicación desde su lado.

    Body shape:
        {
          "tenantId": 22,
          "identifierType": "DNI",
          "identifier": "12345678"
        }
    """

    tenant_id: int = Field(alias="tenantId", gt=0)
    identifier_type: IdentifierType = Field(alias="identifierType")
    identifier: Annotated[str, Field(min_length=1, max_length=64)]

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("identifier")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


# ── Out ─────────────────────────────────────────────────────────────────
class EmployeeOut(BaseModel):
    employee_code: str = Field(alias="employeeCode")
    document_number: str = Field(alias="documentNumber")
    full_name: str = Field(alias="fullName")
    status: bool
    status_reason: StatusReason = Field(alias="statusReason")
    cost_center: str | None = Field(default=None, alias="costCenter")
    tenant_name: str | None = Field(default=None, alias="tenantName")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class ValidateResponse(BaseModel):
    success: bool
    employee: EmployeeOut | None = None
    message: str

    model_config = ConfigDict(populate_by_name=True)


class EmployeeListItem(BaseModel):
    id: int
    tenant_id: int = Field(alias="tenantId")
    tenant_name: str | None = Field(default=None, alias="tenantName")
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
    """Una fila válida del Excel."""

    employee_code: str
    document_number: str
    document_type: DocumentType = DocumentType.DNI
    full_name: str
    status: bool = True
    status_reason: StatusReason = StatusReason.ACTIVE
    cost_center: str | None = None
    tenant_name: str | None = None


class ImportError(BaseModel):
    row: int
    column: str | None = None
    reason: str


class ImportSummary(BaseModel):
    received: int
    inserted: int
    updated: int
    failed: int
    errors: list[ImportError]
