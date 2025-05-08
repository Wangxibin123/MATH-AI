import datetime
import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .block import Block
    from .event import Event


class Problem(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    rawLatex: Optional[str] = None
    imageUrl: Optional[str] = None
    audioUrl: Optional[str] = None
    createdAt: datetime.datetime = Field(
        default_factory=datetime.datetime.utcnow, nullable=False
    )

    # back refs (lazy loaded)
    blocks: List["Block"] = Relationship(back_populates="problem")
    events: List["Event"] = Relationship(back_populates="problem")
