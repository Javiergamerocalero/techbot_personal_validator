"""Respuesta del botón de generar token.

Nunca incluye el token: el endpoint es público y el token viaja solo
por correo a TECHBOT.
"""
from pydantic import BaseModel, ConfigDict


class AdminTokenRequestResponse(BaseModel):
    success: bool
    message: str

    model_config = ConfigDict(populate_by_name=True)
