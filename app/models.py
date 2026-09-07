import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class CertificationStatus(str, enum.Enum):
    completed = "completed"
    in_progress = "in_progress"
    planned = "planned"


class Certification(Base):
    """Una certificación profesional: ya conseguida, en curso o objetivo futuro."""

    __tablename__ = "certifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[CertificationStatus] = mapped_column(
        Enum(CertificationStatus, name="certification_status"), nullable=False
    )
    issued_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Goal(Base):
    """Un objetivo diario configurable (ej. "Inglés", 30 min/día)."""

    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    target_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    check_ins: Mapped[list["GoalCheckIn"]] = relationship(
        back_populates="goal", cascade="all, delete-orphan"
    )


class GoalCheckIn(Base):
    """Registro diario de minutos dedicados a un objetivo concreto.

    Un check-in por objetivo y día (UniqueConstraint más abajo) — la
    ausencia de fila para un día es justo lo que distingue "no marcado" de
    "marcado, 0 minutos", que era el requisito real (ver wiki/log.md).
    """

    __tablename__ = "goal_check_ins"
    __table_args__ = (UniqueConstraint("goal_id", "date", name="uq_goal_check_in_goal_date"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal: Mapped["Goal"] = relationship(back_populates="check_ins")
