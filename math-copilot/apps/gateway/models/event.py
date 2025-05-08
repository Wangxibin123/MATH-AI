from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.types import JSON
import uuid, datetime
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .problem import Problem

class Event(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    problemId: uuid.UUID = Field(foreign_key="problem.id", nullable=False)
    type: str
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    ts: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)

    problem: "Problem" = Relationship(back_populates="events") 