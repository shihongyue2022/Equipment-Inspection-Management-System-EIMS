"""initial schema

Revision ID: b28638c85152
Revises: 
Create Date: 2026-06-20 12:15:47.382797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b28638c85152'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "base",
        sa.Column("base_number", sa.String(50), primary_key=True),
        sa.Column("base_place", sa.String(50), nullable=True),
    )
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("employee_no", sa.String(20), nullable=False),
        sa.Column("last_name", sa.String(50), nullable=False),
        sa.Column("first_name", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("base", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_employee_no", "employee", ["employee_no"], unique=True)
    op.create_index("idx_employee_email", "employee", ["email"], unique=True)
    op.create_index("idx_employee_role", "employee", ["role"])
    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("equipment_type", sa.String(50), nullable=False),
        sa.Column("manufacturer", sa.String(100), nullable=False),
        sa.Column("model_number", sa.String(100), nullable=False),
        sa.Column("installed_at", sa.Date(), nullable=False),
        sa.Column("inspection_interval_months", sa.Integer(), nullable=False),
        sa.Column("assigned_user_id", sa.Integer(), nullable=True),
        sa.Column("next_inspection_date", sa.Date(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["assigned_user_id"], ["employee.id"], ondelete="SET NULL"
        ),
    )
    op.create_index(
        "idx_equipment_assigned_user", "equipment", ["assigned_user_id"]
    )
    op.create_index(
        "idx_equipment_next_inspection", "equipment", ["next_inspection_date"]
    )
    op.create_table(
        "inspection_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("engineer_id", sa.Integer(), nullable=False),
        sa.Column("inspected_at", sa.Date(), nullable=False),
        sa.Column("status", sa.String(10), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["equipment_id"], ["equipment.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["engineer_id"], ["employee.id"], ondelete="RESTRICT"
        ),
    )
    op.create_index(
        "idx_inspection_equipment", "inspection_records", ["equipment_id"]
    )
    op.create_index(
        "idx_inspection_engineer", "inspection_records", ["engineer_id"]
    )
    op.create_index(
        "idx_inspection_inspected_at", "inspection_records", ["inspected_at"]
    )


def downgrade():
    op.drop_table("inspection_records")
    op.drop_table("equipment")
    op.drop_table("employee")
    op.drop_table("base")
