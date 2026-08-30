"""phase8 add password reset post likes comments user email

Revision ID: 07945b624739
Revises: 6d9a4f5c8b10
Create Date: 2026-07-30 23:20:18.106772

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "07945b624739"
down_revision: str | Sequence[str] | None = "6d9a4f5c8b10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema with idempotent checks for legacy databases."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "post_likes" not in tables:
        op.create_table(
            "post_likes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("actor_type", sa.String(length=10), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["post_id"], ["posts.post_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("post_id", "actor_type", "actor_id", name="uq_post_like_actor"),
        )
        op.create_index(op.f("ix_post_likes_post_id"), "post_likes", ["post_id"], unique=False)

    if "post_comments" not in tables:
        op.create_table(
            "post_comments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("post_id", sa.Integer(), nullable=False),
            sa.Column("actor_type", sa.String(length=10), nullable=False),
            sa.Column("actor_id", sa.Integer(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["post_id"], ["posts.post_id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            op.f("ix_post_comments_post_id"), "post_comments", ["post_id"], unique=False
        )

    if "User" in tables:
        user_cols = {c["name"] for c in inspector.get_columns("User")}
        with op.batch_alter_table("User", schema=None) as batch_op:
            if "Email" not in user_cols:
                batch_op.add_column(sa.Column("Email", sa.String(length=255), nullable=True))
                batch_op.create_unique_constraint("uq_user_email", ["Email"])

    if "pulse_members" in tables:
        pm_cols = {c["name"] for c in inspector.get_columns("pulse_members")}
        with op.batch_alter_table("pulse_members", schema=None) as batch_op:
            if "reset_token" not in pm_cols:
                batch_op.add_column(sa.Column("reset_token", sa.String(length=100), nullable=True))
            if "reset_token_expires_at" not in pm_cols:
                batch_op.add_column(
                    sa.Column("reset_token_expires_at", sa.DateTime(), nullable=True)
                )
            if "reset_token" not in pm_cols:
                batch_op.create_unique_constraint("uq_pulse_member_reset_token", ["reset_token"])


def downgrade() -> None:
    """Downgrade schema with idempotent checks."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if "pulse_members" in tables:
        pm_cols = {c["name"] for c in inspector.get_columns("pulse_members")}
        with op.batch_alter_table("pulse_members", schema=None) as batch_op:
            if "reset_token" in pm_cols:
                batch_op.drop_constraint("uq_pulse_member_reset_token", type_="unique")
            if "reset_token_expires_at" in pm_cols:
                batch_op.drop_column("reset_token_expires_at")
            if "reset_token" in pm_cols:
                batch_op.drop_column("reset_token")

    if "User" in tables:
        user_cols = {c["name"] for c in inspector.get_columns("User")}
        with op.batch_alter_table("User", schema=None) as batch_op:
            if "Email" in user_cols:
                batch_op.drop_constraint("uq_user_email", type_="unique")
                batch_op.drop_column("Email")

    if "post_likes" in tables:
        op.drop_index(op.f("ix_post_likes_post_id"), table_name="post_likes")
        op.drop_table("post_likes")

    if "post_comments" in tables:
        op.drop_index(op.f("ix_post_comments_post_id"), table_name="post_comments")
        op.drop_table("post_comments")
