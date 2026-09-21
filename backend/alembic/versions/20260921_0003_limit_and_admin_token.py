"""limite de compra por empleado + tabla de tokens de administracion

Per Javier 2026-09-21:
- Tope de consumo por empleado, editable desde el panel.
- Boton para generar un token de administracion y recibirlo por correo,
  lo que exige poder rotarlo sin entrar al servidor.

Revision ID: 20260921_0003
Revises: 20260806_0002
Create Date: 2026-09-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260921_0003"
down_revision: Union[str, None] = "20260806_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NULL = sin tope. Se deja nullable a proposito: la mayoria de los
    # empleados no tiene limite y un 0 significaria "no puede comprar".
    op.add_column(
        "employees",
        sa.Column("purchase_limit_cents", sa.Integer(), nullable=True),
    )

    op.create_table(
        "admin_tokens",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.Column("sent_to", sa.String(length=200), nullable=True),
        sa.Column("requested_from", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    # Se consulta siempre el mas reciente.
    op.create_index(
        "ix_admin_tokens_created_at", "admin_tokens", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_admin_tokens_created_at", table_name="admin_tokens")
    op.drop_table("admin_tokens")
    op.drop_column("employees", "purchase_limit_cents")
