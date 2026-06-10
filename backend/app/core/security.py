"""Auth helpers.

Tras feedback de Javier 2026-06-09:
- `/validate` queda PÚBLICO (Qapp se encarga de la comunicación
  segura desde su lado y el tenant_id viene en el body de cada
  request).
- Los endpoints administrativos (subir Excel, listar empleados,
  descargar plantilla) siguen detrás de `X-Admin-Token` para evitar
  que cualquiera con la URL pueda escribir en la base.
"""
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def require_admin(
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    expected = get_settings().admin_token
    if not x_admin_token or not secrets.compare_digest(
        x_admin_token.strip(), expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
