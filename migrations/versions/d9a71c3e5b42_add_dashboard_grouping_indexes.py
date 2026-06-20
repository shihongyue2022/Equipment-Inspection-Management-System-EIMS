"""add dashboard grouping indexes

Revision ID: d9a71c3e5b42
Revises: b28638c85152
Create Date: 2026-06-20 00:00:00.000000

"""
from alembic import op


revision = "d9a71c3e5b42"
down_revision = "b28638c85152"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_employee_base", "employee", ["base"])
    op.create_index(
        "idx_inspection_latest",
        "inspection_records",
        ["equipment_id", "inspected_at", "id"],
    )


def downgrade():
    op.drop_index("idx_inspection_latest", table_name="inspection_records")
    op.drop_index("idx_employee_base", table_name="employee")
