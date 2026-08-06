"""Pydantic schemas para Employee.

Confirmado con Javier 2026-06-09 21:03:
- `status` es string ("Active" / "Inactive").
- `status_reason` es varchar libre nullable (motivo del Inactive).
- Sin `cost_center`.
"""
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.employee import (
    STATUS_ACTIVE,
    STATUS_INACTIVE,
    DocumentType,
)
from app.models.validation_log import IdentifierType


# ── In ──────────────────────────────────────────────────────────────────
class ValidateRequest(BaseModel):
    """Body del POST /employees/validate consumido por Qapp.

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
    # id agregado 2026-08-06 para que el kiosco San Fernando pueda
    # registrar compras contra POST /employees/{id}/purchases sin
    # tener que hacer un lookup adicional por (tenant, code).
    id: int
    employee_code: str = Field(alias="employeeCode")
    document_number: str = Field(alias="documentNumber")
    full_name: str = Field(alias="fullName")
    status: str
    status_reason: str | None = Field(default=None, alias="statusReason")
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
    status: str
    status_reason: str | None = Field(default=None, alias="statusReason")
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
    status: str = STATUS_ACTIVE
    status_reason: str | None = None
    tenant_name: str | None = None

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, v: str) -> str:
        """Acepta variantes case-insensitive ("active", "ACTIVE", etc.)
        y las normaliza a 'Active' / 'Inactive'. Rechaza otros valores.
        """
        clean = (v or "").strip().lower()
        if clean in {"active", "activo", "a", "1", "true"}:
            return STATUS_ACTIVE
        if clean in {"inactive", "inactivo", "i", "0", "false"}:
            return STATUS_INACTIVE
        raise ValueError(
            f"status debe ser 'Active' o 'Inactive' (recibido: {v!r})"
        )


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
