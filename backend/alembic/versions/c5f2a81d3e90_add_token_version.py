"""Give every account a token version so sessions can actually be ended.

Access and refresh tokens are stateless JWTs, so before this there was nothing
the server could do to stop honouring one: signing out cleared the browser but
left a refresh token valid for its full lifetime, and changing a password did
not evict sessions opened with the old one. Each account now carries a counter
that is embedded in its tokens and bumped whenever every session should end.

Revision ID: c5f2a81d3e90
Revises: b3e7d1a94c26
Create Date: 2026-08-21
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c5f2a81d3e90"
down_revision: str | Sequence[str] | None = "b3e7d1a94c26"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _columns(table: str) -> set[str]:
    """Return the column names of a table, or an empty set if it is absent."""
    from sqlalchemy import inspect

    inspector = inspect(op.get_bind())
    if table not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table)}


def upgrade() -> None:
    """Add ``token_version`` to both account tables."""
    for table in ("pulse_members", "User"):
        if "token_version" not in _columns(table):
            op.add_column(
                table,
                # Existing tokens carry no version claim and are read as 0, so
                # the default keeps every live session working across deploy.
                sa.Column(
                    "token_version",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                ),
            )


def downgrade() -> None:
    """Drop the column again."""
    for table in ("pulse_members", "User"):
        if "token_version" in _columns(table):
            op.drop_column(table, "token_version")
