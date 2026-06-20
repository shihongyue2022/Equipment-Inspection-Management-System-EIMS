from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.utils import get_deadline_status


class ServiceBase(db.Model):
    __tablename__ = "base"

    base_number: Mapped[str] = mapped_column(String(50), primary_key=True)
    base_place: Mapped[str | None] = mapped_column(String(50))


class User(db.Model):
    __tablename__ = "employee"
    __table_args__ = (
        Index("idx_employee_no", "employee_no", unique=True),
        Index("idx_employee_email", "email", unique=True),
        Index("idx_employee_role", "role"),
        Index("idx_employee_base", "base"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_no: Mapped[str] = mapped_column(String(20))
    last_name: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255))
    password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(10))
    phone: Mapped[str | None] = mapped_column(String(20))
    base: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    assigned_equipment: Mapped[list["Equipment"]] = relationship(back_populates="assigned_user")
    inspections: Mapped[list["Inspection"]] = relationship(back_populates="engineer")
    maintenance_records: Mapped[list["Maintenance"]] = relationship(
        back_populates="engineer"
    )

    @property
    def full_name(self):
        return f"{self.last_name}{self.first_name}"


class Equipment(db.Model):
    __tablename__ = "equipment"
    __table_args__ = (
        Index("idx_equipment_assigned_user", "assigned_user_id"),
        Index("idx_equipment_next_inspection", "next_inspection_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    location: Mapped[str] = mapped_column(String(200))
    equipment_type: Mapped[str] = mapped_column(String(50))
    manufacturer: Mapped[str] = mapped_column(String(100))
    model_number: Mapped[str] = mapped_column(String(100))
    installed_at: Mapped[date] = mapped_column(Date)
    inspection_interval_months: Mapped[int] = mapped_column(Integer)
    assigned_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("employee.id", ondelete="SET NULL")
    )
    next_inspection_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    assigned_user: Mapped[User | None] = relationship(back_populates="assigned_equipment")
    inspections: Mapped[list["Inspection"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by=lambda: (Inspection.inspected_at.desc(), Inspection.id.desc()),
    )
    maintenance_records: Mapped[list["Maintenance"]] = relationship(
        back_populates="equipment",
        cascade="all, delete-orphan",
        order_by=lambda: Maintenance.id.desc(),
    )

    @property
    def assigned_user_name(self):
        return self.assigned_user.full_name if self.assigned_user else None

    @property
    def deadline_status(self):
        return get_deadline_status(self.next_inspection_date)

    @property
    def latest_inspection_status(self):
        return self.inspections[0].status if self.inspections else None


class Inspection(db.Model):
    __tablename__ = "inspection_records"
    __table_args__ = (
        Index("idx_inspection_equipment", "equipment_id"),
        Index("idx_inspection_engineer", "engineer_id"),
        Index("idx_inspection_inspected_at", "inspected_at"),
        Index("idx_inspection_latest", "equipment_id", "inspected_at", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE")
    )
    engineer_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="RESTRICT")
    )
    inspected_at: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    equipment: Mapped[Equipment] = relationship(back_populates="inspections")
    engineer: Mapped[User] = relationship(back_populates="inspections")
    maintenance_records: Mapped[list["Maintenance"]] = relationship(
        back_populates="source_inspection"
    )

    @property
    def engineer_name(self):
        return self.engineer.full_name

    @property
    def status_label(self):
        return {"normal": "正常", "watch": "要観察", "repair": "要修理"}.get(
            self.status, "不明"
        )


class Maintenance(db.Model):
    __tablename__ = "maintenance_records"
    __table_args__ = (
        UniqueConstraint("source_inspection_id", name="uq_maintenance_source_inspection"),
        Index("idx_maintenance_equipment", "equipment_id"),
        Index("idx_maintenance_engineer", "engineer_id"),
        Index("idx_maintenance_status", "status"),
        Index("idx_maintenance_completed_at", "completed_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", ondelete="CASCADE")
    )
    source_inspection_id: Mapped[int | None] = mapped_column(
        ForeignKey("inspection_records.id", ondelete="SET NULL")
    )
    engineer_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", ondelete="RESTRICT")
    )
    status: Mapped[str] = mapped_column(String(20))
    action: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[date | None] = mapped_column(Date)
    result: Mapped[str | None] = mapped_column(Text)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp()
    )

    equipment: Mapped[Equipment] = relationship(back_populates="maintenance_records")
    source_inspection: Mapped[Inspection | None] = relationship(
        back_populates="maintenance_records"
    )
    engineer: Mapped[User] = relationship(back_populates="maintenance_records")

    @property
    def engineer_name(self):
        return self.engineer.full_name

    @property
    def status_label(self):
        return {
            "planned": "対応予定",
            "in_progress": "対応中",
            "completed": "完了",
            "cancelled": "取消",
        }.get(self.status, "不明")
