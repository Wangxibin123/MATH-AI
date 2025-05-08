import datetime
import uuid
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .problem import Problem


class Block(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    problemId: uuid.UUID = Field(foreign_key="problem.id", nullable=False)
    orderIndex: int = Field(index=True)

    latex: str
    html: Optional[str] = None
    author: str = Field(default="assistant")
    isTerminal: bool = Field(default=False)
    createdAt: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)
    updatedAt: datetime.datetime = Field(default_factory=datetime.datetime.utcnow, nullable=False)

    # relationship
    problem: "Problem" = Relationship(back_populates="blocks")
