"""Runtime configuration.

Las variables vienen de `.env` o del entorno. Pydantic Settings hace
validación + tipos + defaults. Inmutable después del import — si
hay que cambiar algo en runtime, no es acá.
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = Field(
        ...,
        description="Postgres async connection string (asyncpg).",
    )

    admin_token: str = Field(
        ...,
        min_length=12,
        description=(
            "Token para endpoints administrativos (creación de tenants, "
            "rotación de claves). NO compartir con clientes."
        ),
    )

    # ── Correo (botón de generar token del panel admin) ─────────────
    smtp_host: str = Field(default="", description="Servidor SMTP.")
    smtp_port: int = Field(default=587)
    smtp_user: str = Field(default="")
    smtp_password: str = Field(default="")
    smtp_use_ssl: bool = Field(
        default=False, description="SMTP directo sobre SSL (puerto 465)."
    )
    smtp_use_starttls: bool = Field(default=True)
    mail_from: str = Field(default="", description="Remitente de los correos.")

    admin_token_mail_to: str = Field(
        default="",
        description=(
            "A quién se le manda el token generado. Es fijo a propósito: "
            "el botón que lo dispara es público, así que el destino no "
            "puede venir del cliente."
        ),
    )

    admin_token_min_minutes: int = Field(
        default=10,
        ge=1,
        description=(
            "Espera mínima entre generaciones de token. Evita que alguien "
            "rote el token en bucle y deje al administrador fuera."
        ),
    )

    cors_origins: str = Field(
        default="http://localhost:5173",
        description="Orígenes permitidos para CORS, separados por coma.",
    )

    log_level: str = Field(default="INFO")

    kiosk_name_header: str = Field(
        default="X-Kiosk-Name",
        description=(
            "Header opcional que Qapp manda con el nombre del quiosco "
            "para rastreo en validation_log."
        ),
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Singleton — la configuración se carga una sola vez por proceso."""
    return Settings()  # type: ignore[call-arg]
