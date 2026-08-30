"""add member password_hash and referred_by_id

Revision ID: 6d9a4f5c8b10
Revises: e2a5f949e58a
Create Date: 2026-07-30 22:46:35.188517

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6d9a4f5c8b10"
down_revision: str | Sequence[str] | None = "e2a5f949e58a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add password_hash and referred_by_id columns to pulse_members if missing."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("pulse_members")}
    if "password_hash" not in cols:
        op.add_column("pulse_members", sa.Column("password_hash", sa.String(255), nullable=True))
    if "referred_by_id" not in cols:
        op.add_column("pulse_members", sa.Column("referred_by_id", sa.Integer, nullable=True))


def downgrade() -> None:
    """Remove the added columns if they exist."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = {c["name"] for c in inspector.get_columns("pulse_members")}
    if "referred_by_id" in cols:
        op.drop_column("pulse_members", "referred_by_id")
    if "password_hash" in cols:
        op.drop_column("pulse_members", "password_hash")
