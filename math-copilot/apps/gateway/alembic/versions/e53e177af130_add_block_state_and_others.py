"""add_block_state_and_others

Revision ID: e53e177af130
Revises: a9757885287a
Create Date: 2025-05-12 12:07:19.296600

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "e53e177af130"
down_revision: Union[str, None] = "a9757885287a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("block", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "state", sa.String(length=16), nullable=False, server_default="active"
            )
        )
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "problemId",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
        )

    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )
        batch_op.alter_column(
            "problemId",
            existing_type=sa.NUMERIC(),
            type_=sa.UUID(),
            existing_nullable=False,
        )

    with op.batch_alter_table("problem", schema=None) as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.NUMERIC(), type_=sa.UUID(), existing_nullable=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("problem", schema=None) as batch_op:
        batch_op.alter_column(
            "id", existing_type=sa.UUID(), type_=sa.NUMERIC(), existing_nullable=False
        )

    with op.batch_alter_table("event", schema=None) as batch_op:
        batch_op.alter_column(
            "problemId",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "id", existing_type=sa.UUID(), type_=sa.NUMERIC(), existing_nullable=False
        )

    with op.batch_alter_table("block", schema=None) as batch_op:
        batch_op.alter_column(
            "problemId",
            existing_type=sa.UUID(),
            type_=sa.NUMERIC(),
            existing_nullable=False,
        )
        batch_op.alter_column(
            "id", existing_type=sa.UUID(), type_=sa.NUMERIC(), existing_nullable=False
        )
        batch_op.drop_column("state")
