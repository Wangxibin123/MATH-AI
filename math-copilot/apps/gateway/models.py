import uuid
from datetime import datetime
from typing import Optional
from enum import Enum

from sqlmodel import Field, SQLModel

class BlockAuthor(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class BlockState(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"
    ARCHIVED = "archived"

class BlockBase(SQLModel):
    problemId: uuid.UUID = Field(index=True) # Added index for potential filtering
    parentId: Optional[uuid.UUID] = Field(default=None, index=True)
    orderIndex: int = Field(default=0)
    latex: str
    html: Optional[str] = Field(default=None) # Made optional for simplicity first
    author: BlockAuthor
    state: BlockState = Field(default=BlockState.ACTIVE)
    isTerminal: bool = Field(default=False)
    collapsed: bool = Field(default=False)
    modelUsed: Optional[str] = Field(default=None)
    # altOutputs can be added later if needed, e.g., as JSON or Text field

class Block(BlockBase, table=True):
    # SQLModel will use the class name "block" as the table name by default
    id: Optional[uuid.UUID] = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updatedAt: datetime = Field(default_factory=datetime.utcnow, nullable=False) # Consider SQLAlchemy events for auto-update later

class BlockCreate(BlockBase):
    # This model is used when creating a new block via API.
    # It inherits all fields from BlockBase.
    pass

class BlockRead(BlockBase):
    # This model is used when returning a block from the API.
    id: uuid.UUID
    createdAt: datetime
    updatedAt: datetime 