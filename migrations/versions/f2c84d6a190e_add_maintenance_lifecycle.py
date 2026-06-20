"""add maintenance lifecycle

Revision ID: f2c84d6a190e
Revises: d9a71c3e5b42
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f2c84d6a190e"
down_revision = "d9a71c3e5b42"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "maintenance_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("source_inspection_id", sa.Integer(), nullable=True),
        sa.Column("engineer_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("action", sa.String(255), nullable=False),
        sa.Column("started_at", sa.Date(), nullable=True),
        sa.Column("completed_at", sa.Date(), nullable=True),
        sa.Column("result", sa.Text(), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["source_inspection_id"], ["inspection_records.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["engineer_id"], ["employee.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint(
            "source_inspection_id", name="uq_maintenance_source_inspection"
        ),
    )
    op.create_index("idx_maintenance_equipment", "maintenance_records", ["equipment_id"])
    op.create_index("idx_maintenance_engineer", "maintenance_records", ["engineer_id"])
    op.create_index("idx_maintenance_status", "maintenance_records", ["status"])
    op.create_index(
        "idx_maintenance_completed_at", "maintenance_records", ["completed_at"]
    )


def downgrade():
    op.drop_table("maintenance_records")
