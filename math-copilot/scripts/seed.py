# type: ignore
from apps.gateway.db import get_session, init_db
from apps.gateway.models import Block, Problem


def main() -> None:
    init_db()  # Ensures tables are created, though Alembic should have done this. Idempotent.
    with get_session() as s:
        problem = Problem(rawLatex=r"\frac{x}{y}")
        s.add(problem)
        s.flush()  # Ensure problem.id is available

        s.add_all(
            [
                Block(problemId=problem.id, orderIndex=0, latex=r"\frac{x}{y}"),
                Block(problemId=problem.id, orderIndex=1, latex=r"x/y"),
            ]
        )
        s.commit()
    print("Seed OK")


if __name__ == "__main__":
    main()
