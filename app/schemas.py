import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models import CertificationStatus


class CertificationBase(BaseModel):
    name: str
    issuer: str
    status: CertificationStatus
    issued_date: date | None = None
    target_date: date | None = None
    notes: str | None = None


class CertificationCreate(CertificationBase):
    pass


class CertificationOut(CertificationBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class GoalBase(BaseModel):
    name: str
    target_minutes: int
    active: bool = True


class GoalCreate(GoalBase):
    pass


class GoalOut(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime


class GoalCheckInBase(BaseModel):
    date: date
    minutes: int
    notes: str | None = None


class GoalCheckInCreate(GoalCheckInBase):
    pass


class GoalCheckInOut(GoalCheckInBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    goal_id: uuid.UUID
    created_at: datetime


class GoalTodayStatus(BaseModel):
    goal_id: uuid.UUID
    goal_name: str
    date: date
    target_minutes: int
    checked_in: bool
    minutes: int = 0
    goal_met: bool = False
