import pytest
from sqlmodel import select
from sqlalchemy import delete

from apps.gateway.db import get_session
from apps.gateway.models import Block, Problem  # Added Problem


@pytest.fixture(scope="module", autouse=True)
def _fresh_db():
    # Database file creation and deletion is handled by the CI script
    # (rm /tmp/math_copilot_dev.db and alembic upgrade head).
    # This fixture's main role is now to ensure seed data is populated after clearing tables.

    # Alembic should have created the tables via 'alembic upgrade head'.
    # The seed script also calls init_db(), which is idempotent and now uses the
    # engine configured for /tmp (or DB_URL env var).

    # Clear existing data from tables before seeding to ensure a clean slate for this module's tests
    with get_session() as s:
        s.execute(delete(Block))
        s.execute(delete(Problem))
        s.commit()

    from scripts import seed

    seed.main()

    yield

    # No cleanup of DB file here; CI script handles it on next run.


def test_block_count():
    with get_session() as s:
        # results = s.exec(select(Block)).count() # Deprecated
        block_list = s.exec(select(Block)).all()
        assert len(block_list) == 2


def test_problem_exists_and_has_blocks():
    with get_session() as s:
        problem = s.exec(
            select(Problem).where(Problem.rawLatex == r"\frac{x}{y}")
        ).first()
        assert problem is not None, "Problem should exist after seeding"
        assert problem.id is not None, "Problem ID should not be None"

        # Verify related blocks through the relationship
        # SQLModel loads relationships lazily by default
        assert len(problem.blocks) == 2, "Problem should have 2 blocks"

        # Optional: verify content of blocks if needed for more robustness
        block_latex_values = sorted(
            [b.latex for b in problem.blocks]
        )  # Sort to make order independent
        expected_latex_values = sorted([r"\frac{x}{y}", r"x/y"])
        assert (
            block_latex_values == expected_latex_values
        ), "Block latex content mismatch"

        assert problem.blocks[0].orderIndex == 0 or problem.blocks[1].orderIndex == 0
        assert problem.blocks[0].orderIndex == 1 or problem.blocks[1].orderIndex == 1
