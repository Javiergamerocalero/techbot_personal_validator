"""initial schema — tenants, employees, validation_logs

Revision ID: 20260609_0001
Revises:
Create Date: 2026-06-09 12:00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20260609_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
        sa.UniqueConstraint("api_key_hash", name="uq_tenants_api_key_hash"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"])
    op.create_index("ix_tenants_api_key_hash", "tenants", ["api_key_hash"])

    op.create_table(
        "employees",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("employee_code", sa.String(length=64), nullable=False),
        sa.Column("document_number", sa.String(length=32), nullable=False),
        sa.Column(
            "document_type",
            sa.String(length=16),
            nullable=False,
            server_default="DNI",
        ),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column(
            "status",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "status_reason",
            sa.String(length=32),
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column("cost_center", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint(
            "tenant_id", "employee_code", name="uq_employee_tenant_code"
        ),
        sa.UniqueConstraint(
            "tenant_id", "document_number", name="uq_employee_tenant_doc"
        ),
    )
    op.create_index("ix_employees_tenant_id", "employees", ["tenant_id"])
    op.create_index(
        "ix_employee_tenant_code", "employees", ["tenant_id", "employee_code"]
    )
    op.create_index(
        "ix_employee_tenant_doc", "employees", ["tenant_id", "document_number"]
    )

    op.create_table(
        "validation_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), nullable=False),
        sa.Column("identifier_type", sa.String(length=16), nullable=False),
        sa.Column("identifier", sa.String(length=64), nullable=False),
        sa.Column("result", sa.String(length=32), nullable=False),
        sa.Column("kiosk_name", sa.String(length=100), nullable=True),
        sa.Column("employee_id", sa.BigInteger(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], ["tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["employee_id"], ["employees.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "ix_validation_logs_tenant_id", "validation_logs", ["tenant_id"]
    )
    op.create_index(
        "ix_validation_tenant_created",
        "validation_logs",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_validation_tenant_created", table_name="validation_logs")
    op.drop_index("ix_validation_logs_tenant_id", table_name="validation_logs")
    op.drop_table("validation_logs")
    op.drop_index("ix_employee_tenant_doc", table_name="employees")
    op.drop_index("ix_employee_tenant_code", table_name="employees")
    op.drop_index("ix_employees_tenant_id", table_name="employees")
    op.drop_table("employees")
    op.drop_index("ix_tenants_api_key_hash", table_name="tenants")
    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
