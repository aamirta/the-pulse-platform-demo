"""Add resource_applications for event registrations and opportunity applications.

The Events and Opportunities pages rendered a success message on submit and then
discarded the input — there was nowhere to store it. This table backs both flows.

Revision ID: d94e7c2f1a58
Revises: c83d5a1e6b47
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d94e7c2f1a58"
down_revision: str | Sequence[str] | None = "c83d5a1e6b47"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the resource_applications table."""
    if "resource_applications" in sa.inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        "resource_applications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["resource_id"], ["resources.resource_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["member_id"], ["pulse_members.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("resource_id", "member_id", name="uq_resource_application_member"),
    )
    op.create_index(
        "ix_resource_applications_resource_id", "resource_applications", ["resource_id"]
    )
    op.create_index("ix_resource_applications_member_id", "resource_applications", ["member_id"])


def downgrade() -> None:
    """Drop the resource_applications table."""
    op.drop_index("ix_resource_applications_member_id", table_name="resource_applications")
    op.drop_index("ix_resource_applications_resource_id", table_name="resource_applications")
    op.drop_table("resource_applications")
