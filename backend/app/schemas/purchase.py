"""Pydantic schemas para Purchase.

Endpoints:
- POST /api/v1/employees/{employee_id}/purchases  → registra compra.
- GET  /api/v1/employees/{employee_id}/purchases/today-total?tenantId=22
       → total del día del empleado (para checks de límite futuros).

Convención camelCase en el body/alias para consistencia con el
resto del API que consume Qapp.
"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class PurchaseCreateRequest(BaseModel):
    tenant_id: int = Field(alias="tenantId", gt=0)
    amount_cents: int = Field(alias="amountCents", gt=0)
    currency: Annotated[str, Field(min_length=3, max_length=3)] = "PEN"
    kiosk_name: str | None = Field(default=None, alias="kioskName", max_length=100)
    external_reference: str | None = Field(
        default=None, alias="externalReference", max_length=100
    )

    model_config = ConfigDict(populate_by_name=True)


class PurchaseOut(BaseModel):
    id: int
    tenant_id: int = Field(serialization_alias="tenantId")
    employee_id: int = Field(serialization_alias="employeeId")
    amount_cents: int = Field(serialization_alias="amountCents")
    currency: str
    purchased_at: datetime = Field(serialization_alias="purchasedAt")
    kiosk_name: str | None = Field(serialization_alias="kioskName")
    external_reference: str | None = Field(serialization_alias="externalReference")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class PurchaseCreateResponse(BaseModel):
    success: bool = True
    purchase: PurchaseOut


class TodayTotalResponse(BaseModel):
    tenant_id: int = Field(serialization_alias="tenantId")
    employee_id: int = Field(serialization_alias="employeeId")
    date: str  # YYYY-MM-DD en zona local (America/Lima)
    count: int
    total_cents: int = Field(serialization_alias="totalCents")
    currency: str = "PEN"
