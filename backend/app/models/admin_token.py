"""Token de administración vigente, guardado en base.

Hasta ahora el token vivía solo en `ADMIN_TOKEN` del `.env`, así que
rotarlo obligaba a entrar al servidor y reiniciar el servicio. Javier
pidió el 2026-09-21 un botón que genere uno nuevo y se lo mande por
correo, y para eso el token tiene que poder cambiar en caliente.

Convive con el del `.env`: si no hay ninguna fila acá, sigue valiendo
el del archivo. Así nada se rompe antes de la primera generación, y el
del `.env` queda como llave de respaldo si el correo falla.
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AdminToken(Base):
    __tablename__ = "admin_tokens"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)

    token: Mapped[str] = mapped_column(String(128), nullable=False)

    # A qué correo se envió, para poder rastrear quién lo tiene.
    sent_to: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Desde dónde se pidió. Sirve para ver si alguien está abusando del
    # botón, que es público por necesidad.
    requested_from: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
