"""Generación y validación del token de administración.

El token vive en base (`admin_tokens`) para poder rotarlo sin entrar al
servidor. El del `.env` sigue valiendo siempre, como llave de respaldo:
si el correo falla o la base se vacía, TECHBOT todavía puede entrar.
"""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.admin_token import AdminToken


async def token_vigente(session: AsyncSession) -> AdminToken | None:
    """El último token generado, o None si nunca se generó ninguno."""
    resultado = await session.execute(
        select(AdminToken).order_by(desc(AdminToken.created_at)).limit(1)
    )
    return resultado.scalar_one_or_none()


async def segundos_para_poder_generar(
    session: AsyncSession, espera_minutos: int
) -> int:
    """Cuánto falta para poder generar otro token. 0 = se puede ya.

    El botón que lo dispara es público por necesidad —se usa justo
    cuando no se tiene token—, así que sin esta espera cualquiera
    podría rotar el token en bucle y dejar al administrador afuera,
    además de inundarle el correo.
    """
    ultimo = await token_vigente(session)
    if ultimo is None:
        return 0

    creado = ultimo.created_at
    if creado.tzinfo is None:
        creado = creado.replace(tzinfo=timezone.utc)

    listo = creado + timedelta(minutes=espera_minutos)
    faltan = (listo - datetime.now(timezone.utc)).total_seconds()
    return max(0, int(faltan))


async def generar_token(
    session: AsyncSession,
    *,
    enviado_a: str | None = None,
    pedido_desde: str | None = None,
) -> str:
    """Crea un token nuevo, lo guarda y lo devuelve en claro.

    En claro porque hay que mandarlo por correo. No se muestra nunca en
    la respuesta HTTP: quien aprieta el botón puede ser cualquiera.
    """
    valor = secrets.token_urlsafe(36)
    session.add(
        AdminToken(
            token=valor,
            sent_to=enviado_a,
            requested_from=pedido_desde,
        )
    )
    await session.commit()
    return valor
