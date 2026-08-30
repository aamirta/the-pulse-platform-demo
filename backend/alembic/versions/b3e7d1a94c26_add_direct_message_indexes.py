"""Index direct_messages for inbox reads.

The inbox filters every query on ``from_email``/``to_email`` and orders by
``created_at``. The table carried no index at all on those columns, so listing
conversations and opening a thread were both sequential scans that grew with the
whole platform's message volume rather than with the actor's own mailbox.

Revision ID: b3e7d1a94c26
Revises: a7c4e91b2d38
Create Date: 2026-08-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "b3e7d1a94c26"
down_revision: str | Sequence[str] | None = "a7c4e91b2d38"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _existing_indexes(table: str) -> set[str]:
    """Return the index names already present, so a re-run is a no-op."""
    from sqlalchemy import inspect

    inspector = inspect(op.get_bind())
    if table not in inspector.get_table_names():
        return set()
    return {index["name"] for index in inspector.get_indexes(table) if index.get("name")}


def upgrade() -> None:
    """Add the composite indexes the inbox queries actually use."""
    existing = _existing_indexes("direct_messages")

    # Thread reads filter on one side of the pair and sort by time, so the sort
    # column belongs in the index rather than in a separate step.
    if "ix_direct_messages_to_created" not in existing:
        op.create_index(
            "ix_direct_messages_to_created",
            "direct_messages",
            ["to_email", "created_at"],
        )
    if "ix_direct_messages_from_created" not in existing:
        op.create_index(
            "ix_direct_messages_from_created",
            "direct_messages",
            ["from_email", "created_at"],
        )
    # The unread badge counts rows addressed to the actor that are still unread.
    if "ix_direct_messages_to_unread" not in existing:
        op.create_index(
            "ix_direct_messages_to_unread",
            "direct_messages",
            ["to_email", "is_read"],
        )


def downgrade() -> None:
    """Drop the indexes added by :func:`upgrade`."""
    existing = _existing_indexes("direct_messages")
    for name in (
        "ix_direct_messages_to_unread",
        "ix_direct_messages_from_created",
        "ix_direct_messages_to_created",
    ):
        if name in existing:
            op.drop_index(name, table_name="direct_messages")
