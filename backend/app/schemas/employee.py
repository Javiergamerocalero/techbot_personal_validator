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


class EmployeeUpdateRequest(BaseModel):
    """PATCH parcial: solo los campos presentes se actualizan.

    Todos opcionales, pero al menos uno debe venir o el server
    responde 400.
    """

    employee_code: str | None = Field(
        default=None, alias="employeeCode", min_length=1, max_length=64
    )
    document_number: str | None = Field(
        default=None, alias="documentNumber", min_length=1, max_length=32
    )
    document_type: DocumentType | None = Field(
        default=None, alias="documentType"
    )
    full_name: str | None = Field(
        default=None, alias="fullName", min_length=1, max_length=100
    )
    status: str | None = Field(default=None, min_length=1, max_length=16)
    status_reason: str | None = Field(
        default=None, alias="statusReason", max_length=100
    )
    tenant_name: str | None = Field(
        default=None, alias="tenantName", max_length=100
    )

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("status")
    @classmethod
    def _normalize_status(cls, v: str | None) -> str | None:
        if v is None:
            return None
        clean = v.strip().lower()
        if clean in {"active", "activo", "a", "1", "true"}:
            return STATUS_ACTIVE
        if clean in {"inactive", "inactivo", "i", "0", "false"}:
            return STATUS_INACTIVE
        raise ValueError(
            f"status debe ser 'Active' o 'Inactive' (recibido: {v!r})"
        )


class TenantSummary(BaseModel):
    """Resumen por tenant_name para poblar el dropdown del admin web.

    `tenantName` puede ser null cuando el operador no cargó nombre en
    la plantilla del Excel — igual devolvemos la row para poder
    filtrar por "sin nombre" desde el UI.
    """

    tenant_name: str | None = Field(default=None, alias="tenantName")
    count: int

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class TenantListResponse(BaseModel):
    items: list[TenantSummary]


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
