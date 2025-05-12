import uuid
import pytest
from sqlmodel import Session

from apps.gateway.db import init_db, engine  # Assuming db.py exists and is configured
from apps.gateway.models import (
    Problem,
    Block,
)  # Assuming models/__init__.py or direct path
from apps.gateway.services.block_service import BlockService
from apps.gateway.services.event_bus import (
    pop,
    _event_q,
)  # Import _event_q for clearing


@pytest.fixture(
    scope="function", autouse=True
)  # Changed to function scope for isolation
def db_session():  # Renamed for clarity and to avoid conflict with _db if used elsewhere
    init_db()  # Ensures tables are created
    # Clear the event queue before each test to ensure test isolation
    while not _event_q.empty():
        _event_q.get_nowait()
    yield
    # Teardown: Clear the event queue after each test as well
    while not _event_q.empty():
        _event_q.get_nowait()


def test_block_crud(db_session):  # Added db_session fixture dependency
    with Session(engine) as s:
        pb = Problem(id=uuid.uuid4(), rawLatex="x+y")
        s.add(pb)
        s.commit()
        s.refresh(pb)

        svc = BlockService(s)

        # 1️⃣ create
        blk = svc.create(problem_id=pb.id, latex="x+y")
        assert blk.orderIndex == 0
        evt = pop()
        assert evt and evt["type"] == "block_create"
        assert evt["payload"]["id"] == str(blk.id)
        assert evt["payload"]["idx"] == 0

        # Check block in DB
        db_blk = s.get(Block, blk.id)
        assert db_blk is not None
        assert db_blk.latex == "x+y"
        assert db_blk.state == "active"

        # 2️⃣ update
        updated_fields = {"latex": "x"}
        blk2 = svc.update(blk.id, **updated_fields)
        assert blk2.latex == "x"
        evt2 = pop()
        assert evt2 and evt2["type"] == "block_edit"
        assert evt2["payload"]["id"] == str(blk.id)

        # Check updated block in DB
        s.refresh(blk)
        assert blk.latex == "x"

        # 3️⃣ soft delete
        svc.soft_delete(blk.id)
        evt3 = pop()
        assert evt3 and evt3["type"] == "block_delete"
        assert evt3["payload"]["id"] == str(blk.id)

        s.refresh(blk)  # Refresh to get the updated state from DB
        assert blk.state == "deleted"

        # Try to update a deleted block - should raise error
        with pytest.raises(ValueError, match="cannot update deleted block"):
            svc.update(blk.id, latex="z")

        # Test _next_index logic by creating another block
        blk_another = svc.create(problem_id=pb.id, latex="x+y+z")
        # The service's _next_index filters by state == "active".
        # Since `blk` was soft-deleted, its state is "deleted".
        # Thus, when creating `blk_another`, there are no other *active* blocks for this problem_id.
        # So, `_next_index` should return 0.
        assert (
            blk_another.orderIndex == 0
        ), "If first block is deleted, next active block should get index 0"
        evt4 = pop()
        assert evt4 and evt4["type"] == "block_create"

        # Test soft deleting a non-existent block (should not error if service handles it gracefully)
        non_existent_uuid = uuid.uuid4()
        svc.soft_delete(
            non_existent_uuid
        )  # Expect no error based on current service impl
        assert pop() is None  # No event should be published for non-existent delete
