"""Pydantic schemas para Tenant (endpoints administrativos)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TenantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(
        min_length=2,
        max_length=64,
        pattern=r"^[a-z0-9-]+$",
        description="Slug usado en URLs/logs. Lowercase, dígitos y guiones.",
    )


class TenantOut(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool = Field(alias="isActive")
    created_at: datetime = Field(alias="createdAt")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class TenantCreated(BaseModel):
    """Devuelve el tenant + la API key en RAW. Mostrar UNA SOLA VEZ."""

    tenant: TenantOut
    api_key: str = Field(
        alias="apiKey",
        description=(
            "Raw API key — guardala ahora, no se puede recuperar después. "
            "Si se pierde, hay que rotarla con POST /tenants/{id}/rotate."
        ),
    )

    model_config = ConfigDict(populate_by_name=True)
