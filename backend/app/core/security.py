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

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.services.admin_token_service import token_vigente


async def require_admin(
    session: Annotated[AsyncSession, Depends(get_session)],
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    if not x_admin_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )

    # Comparamos en bytes para evitar el TypeError de
    # `compare_digest` cuando entran caracteres non-ASCII en el
    # header (ej. paste con NBSP o guiones tipográficos).
    recibido = x_admin_token.strip().encode("utf-8")

    # Vale el token generado desde el panel y, siempre, el del `.env`:
    # ese queda como llave de respaldo para TECHBOT si el correo con el
    # token nuevo no llega.
    aceptados = [get_settings().admin_token]
    generado = await token_vigente(session)
    if generado is not None:
        aceptados.append(generado.token)

    for esperado in aceptados:
        if secrets.compare_digest(recibido, esperado.encode("utf-8")):
            return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin token",
    )
