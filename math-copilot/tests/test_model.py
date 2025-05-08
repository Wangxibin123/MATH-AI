import pytest
from sqlmodel import select

from apps.gateway.db import DB_FILE, get_session
from apps.gateway.models import Block, Problem  # Added Problem


@pytest.fixture(scope="module", autouse=True)
def _fresh_db():
    # Ensure a clean state before tests
    if DB_FILE.exists():
        DB_FILE.unlink()

    # Alembic should have created the tables via 'alembic upgrade head'.
    # The seed script also calls init_db(), which is idempotent.
    # init_db() # Not strictly necessary here if alembic ran, but harmless.

    # Run the seed script to populate data
    # Ensure scripts directory is in python path for import
    # This usually works if tests are run from project root
    from scripts import seed

    seed.main()

    yield  # séparation entre la configuration et le nettoyage

    # Clean up the database file after tests
    if DB_FILE.exists():
        DB_FILE.unlink(missing_ok=True)


def test_block_count():
    with get_session() as s:
        # results = s.exec(select(Block)).count() # Deprecated
        block_list = s.exec(select(Block)).all()
        assert len(block_list) == 2


def test_problem_exists_and_has_blocks():
    with get_session() as s:
        problem = s.exec(select(Problem).where(Problem.rawLatex == r"\frac{x}{y}")).first()
        assert problem is not None, "Problem should exist after seeding"
        assert problem.id is not None, "Problem ID should not be None"

        # Verify related blocks through the relationship
        # SQLModel loads relationships lazily by default
        assert len(problem.blocks) == 2, "Problem should have 2 blocks"

        # Optional: verify content of blocks if needed for more robustness
        block_latex_values = sorted([b.latex for b in problem.blocks])  # Sort to make order independent
        expected_latex_values = sorted([r"\frac{x}{y}", r"x/y"])
        assert block_latex_values == expected_latex_values, "Block latex content mismatch"

        assert problem.blocks[0].orderIndex == 0 or problem.blocks[1].orderIndex == 0
        assert problem.blocks[0].orderIndex == 1 or problem.blocks[1].orderIndex == 1
