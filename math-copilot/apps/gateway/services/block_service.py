from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Session, select
from apps.gateway.models import (
    Block,
)  # Assuming models/__init__.py or direct path works
from apps.gateway.services.event_bus import publish


class BlockService:
    """负责 Block CRUD + 事件发布，保证 orderIndex 连续。"""

    def __init__(self, db: Session):
        self.db = db

    # ---------- internal ----------
    def _next_index(self, problem_id: uuid.UUID) -> int:
        idxs = self.db.exec(
            select(Block.orderIndex).where(
                (Block.problemId == problem_id) & (Block.state == "active")
            )
        ).all()
        return (max(idxs) + 1) if idxs else 0

    # ---------- public API ----------
    def create(
        self,
        *,
        problem_id: uuid.UUID,
        latex: str,
        author: str = "assistant",
        **extra: Any,
    ) -> Block:
        blk = Block(
            problemId=problem_id,
            orderIndex=self._next_index(problem_id),
            latex=latex,
            author=author,
            createdAt=datetime.utcnow(),  # Ensure this is handled as per model or here
            updatedAt=datetime.utcnow(),  # Ensure this is handled as per model or here
            **extra,
        )
        self.db.add(blk)
        self.db.commit()
        self.db.refresh(blk)

        publish("block_create", {"id": str(blk.id), "idx": blk.orderIndex})
        return blk

    def update(self, block_id: uuid.UUID, **fields: Any) -> Block:
        blk = self.db.get(Block, block_id)
        if not blk:
            raise ValueError(
                f"Block with id {block_id} not found"
            )  # Added not found check
        if blk.state != "active":
            raise ValueError("cannot update deleted block")
        for k, v in fields.items():
            setattr(blk, k, v)
        blk.updatedAt = datetime.utcnow()
        self.db.commit()
        self.db.refresh(blk)  # Refresh to get latest state from DB if needed

        publish("block_edit", {"id": str(block_id)})
        return blk

    def soft_delete(self, block_id: uuid.UUID) -> None:
        blk = self.db.get(Block, block_id)
        if not blk:  # Added not found check
            # Or raise ValueError, depending on desired behavior for deleting non-existent block
            return
        if blk.state == "deleted":
            return
        blk.state = "deleted"
        blk.updatedAt = datetime.utcnow()  # Also update updatedAt on soft delete
        self.db.commit()

        publish("block_delete", {"id": str(block_id)})
