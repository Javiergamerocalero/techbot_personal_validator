"""Botón "generar token" del panel de administración.

Pedido por Javier el 2026-09-21: cuando alguien entra al panel sin token
válido, debe poder pedir uno; el token **no se muestra en pantalla**, se
le manda por correo a TECHBOT y al que lo pidió se le dice que contacte
a TECHBOT para que se lo facilite.

Este endpoint es público por necesidad —se usa justo cuando no se tiene
token—, así que trae dos defensas:

1. El destinatario del correo es fijo (`ADMIN_TOKEN_MAIL_TO`), nunca
   viene del cliente. Si viniera, cualquiera pediría el token a su
   propio correo.
2. Hay una espera mínima entre generaciones (`ADMIN_TOKEN_MIN_MINUTES`).
   Sin eso, cualquiera podría rotar el token en bucle y dejar al
   administrador afuera, además de inundarle la bandeja.
"""
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.admin_token import (
    AdminTokenRequest,
    AdminTokenRequestResponse,
)
from app.services.admin_token_service import (
    generar_token,
    segundos_para_poder_generar,
)
from app.services.mailer import (
    MailNotConfigured,
    MailSendFailed,
    enviar,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin-token")

MENSAJE_AL_USUARIO = (
    "Se generó un token nuevo y se envió a TECHBOT. "
    "Contacta a TECHBOT para que te facilite el token generado."
)


@router.post(
    "/request",
    response_model=AdminTokenRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Genera un token de administración y lo envía por correo",
)
async def request_token(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    datos: AdminTokenRequest | None = None,
) -> AdminTokenRequestResponse:
    cfg = get_settings()

    faltan = await segundos_para_poder_generar(
        session, cfg.admin_token_min_minutes
    )
    if faltan > 0:
        # No es un error del que pide: ya hay un token recién generado
        # viajando por correo. Se le dice lo mismo, para no convertir
        # esto en una forma de averiguar si alguien más lo pidió.
        logger.info("admin_token.request_throttled", extra={"wait_s": faltan})
        return AdminTokenRequestResponse(
            success=True,
            message=MENSAJE_AL_USUARIO,
        )

    origen = request.client.host if request.client else None
    destino = cfg.admin_token_mail_to

    token = await generar_token(
        session, enviado_a=destino, pedido_desde=origen
    )

    tenant = datos.tenant_id if datos else None
    cuerpo = (
        "Un usuario de la webapp de validación de usuarios de TECHBOT "
        "generó un token de administración.\n\n"
        f"Tenant: {tenant if tenant is not None else 'no indicado'}\n"
        f"Token: {token}\n"
        f"Pedido desde: {origen or 'desconocido'}\n\n"
        "El token anterior generado desde el panel deja de servir. "
        "La llave de respaldo del servidor (ADMIN_TOKEN del .env) sigue "
        "funcionando.\n"
    )

    try:
        enviar(
            asunto=(
                "Validador de Empleados · token de administración"
                + (f" · tenant {tenant}" if tenant is not None else "")
            ),
            cuerpo=cuerpo,
            destinatario=destino,
        )
    except (MailNotConfigured, MailSendFailed) as exc:
        # El token YA quedó generado y es el válido. Si el correo falla,
        # decirle al usuario "listo" sería mentirle: nadie lo recibió.
        logger.error("admin_token.mail_failed", extra={"error": str(exc)})
        return AdminTokenRequestResponse(
            success=False,
            message=(
                "Se generó el token pero no se pudo enviar el correo. "
                "Contacta a TECHBOT para que te lo facilite."
            ),
        )

    logger.info("admin_token.generated", extra={"sent_to": destino})
    return AdminTokenRequestResponse(
        success=True,
        message=MENSAJE_AL_USUARIO,
    )
