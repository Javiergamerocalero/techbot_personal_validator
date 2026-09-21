"""add purchases table

Per Javier 2026-08-06: registrar cada compra del kiosco por
empleado para poder aplicar límites diario/mensual a futuro.

Revision ID: 20260806_0002
Revises: 20260609_0001
Create Date: 2026-08-06 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260806_0002"
down_revision: Union[str, None] = "20260609_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "purchases",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column(
            "employee_id",
            sa.BigInteger(),
            sa.ForeignKey("employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column(
            "currency",
            sa.String(length=3),
            nullable=False,
            server_default="PEN",
        ),
        sa.Column(
            "purchased_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("kiosk_name", sa.String(length=100), nullable=True),
        sa.Column("external_reference", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_purchases_tenant_id", "purchases", ["tenant_id"]
    )
    op.create_index(
        "ix_purchases_tenant_employee_date",
        "purchases",
        ["tenant_id", "employee_id", "purchased_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_purchases_tenant_employee_date", table_name="purchases")
    op.drop_index("ix_purchases_tenant_id", table_name="purchases")
    op.drop_table("purchases")
