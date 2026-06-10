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
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
    # Comparamos en bytes para evitar el TypeError de
    # `compare_digest` cuando entran caracteres non-ASCII en el
    # header (ej. paste con NBSP o guiones tipográficos).
    received = x_admin_token.strip().encode("utf-8")
    expected_bytes = expected.encode("utf-8")
    if not secrets.compare_digest(received, expected_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
