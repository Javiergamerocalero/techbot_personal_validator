"""Auth helpers.

Dos tipos de credenciales:
- `X-Tenant-Key`: API key por tenant — el quiosco Qapp la usa para
  consumir el endpoint público de validación. El tenant_id se
  resuelve a partir de la key vs. la tabla `tenants`.
- `X-Admin-Token`: token único compartido (en `.env`) para endpoints
  administrativos. NO compartir con clientes.
"""
import hashlib
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.models.tenant import Tenant


def generate_api_key() -> tuple[str, str]:
    """Devuelve (raw_key, sha256_hash). Solo el hash se guarda en DB.

    El raw_key se muestra UNA SOLA VEZ al crear el tenant — después no
    se puede recuperar. Si se pierde hay que rotarla.
    """
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return raw, hashed


def hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def require_tenant(
    session: Annotated[AsyncSession, Depends(get_session)],
    x_tenant_key: Annotated[str | None, Header()] = None,
) -> Tenant:
    """Resuelve el tenant a partir del header X-Tenant-Key.

    401 si falta o no matchea. La key se compara en su forma hasheada
    (la DB guarda el sha256, no el raw).
    """
    if not x_tenant_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Tenant-Key header",
            headers={"WWW-Authenticate": "TenantKey"},
        )
    hashed = hash_api_key(x_tenant_key.strip())
    result = await session.execute(
        select(Tenant).where(
            Tenant.api_key_hash == hashed, Tenant.is_active.is_(True)
        )
    )
    tenant = result.scalar_one_or_none()
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive tenant key",
            headers={"WWW-Authenticate": "TenantKey"},
        )
    return tenant


async def require_admin(
    x_admin_token: Annotated[str | None, Header()] = None,
) -> None:
    """Auth para endpoints administrativos.

    Comparación constant-time para evitar timing attacks.
    """
    expected = get_settings().admin_token
    if not x_admin_token or not secrets.compare_digest(
        x_admin_token.strip(), expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
        )
