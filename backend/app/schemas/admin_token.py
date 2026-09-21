"""Respuesta del botón de generar token.

Nunca incluye el token: el endpoint es público y el token viaja solo
por correo a TECHBOT.
"""
from pydantic import BaseModel, ConfigDict, Field


class AdminTokenRequestResponse(BaseModel):
    success: bool
    message: str

    model_config = ConfigDict(populate_by_name=True)


class AdminTokenRequest(BaseModel):
    """Lo que manda la pantalla al pedir un token.

    El tenant es solo informativo, para que el correo diga con qué
    cliente estaba trabajando quien apretó el botón. No decide nada:
    el destinatario del correo es fijo y está en la configuración.
    """

    tenant_id: int | None = Field(default=None, alias="tenantId")

    model_config = ConfigDict(populate_by_name=True)
