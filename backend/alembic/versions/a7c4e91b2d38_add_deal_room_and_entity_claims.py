"""Add Deal Room tables and the member-entity identity bridge.

Creates the thirteen tables backing the Deal Room plus ``member_entity_links``,
which is what lets the backend prove which startup a member represents.

Written to be safe to run against the hosted PostgreSQL database: every table is
created only if absent, so re-running after a partial deploy is a no-op rather
than an error. Foreign keys to legacy tables use their original quoted column
names (``Startups."Startup Id"``, ``User.user_id``).

Revision ID: a7c4e91b2d38
Revises: f1b2c3d4e5a6
Create Date: 2026-08-18
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a7c4e91b2d38"
down_revision: str | Sequence[str] | None = "f1b2c3d4e5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _existing_tables() -> set[str]:
    """Return the set of tables already present in the target database."""
    return set(sa.inspect(op.get_bind()).get_table_names())


def upgrade() -> None:
    """Create the Deal Room schema."""
    present = _existing_tables()

    if "member_entity_links" not in present:
        op.create_table(
            "member_entity_links",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("entity_type", sa.String(20), nullable=False),
            sa.Column("entity_id", sa.Integer(), nullable=False),
            sa.Column("entity_role", sa.String(20), nullable=False, server_default="owner"),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
            sa.Column("approved_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["member_id"], ["pulse_members.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["approved_by_user_id"], ["User.UserId"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "member_id", "entity_type", "entity_id", name="uq_member_entity_link"
            ),
        )
        op.create_index(
            "ix_member_entity_links_member_id", "member_entity_links", ["member_id"]
        )
        op.create_index("ix_member_entity_links_status", "member_entity_links", ["status"])
        op.create_index(
            "ix_member_entity_links_entity",
            "member_entity_links",
            ["entity_type", "entity_id", "status"],
        )

    if "deal_rooms" not in present:
        op.create_table(
            "deal_rooms",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("startup_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(200), nullable=True),
            sa.Column("summary", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column(
                "nda_required", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("nda_version", sa.String(40), nullable=True),
            sa.Column("nda_body", sa.Text(), nullable=True),
            sa.Column(
                "watermark_enabled", sa.Boolean(), nullable=False, server_default=sa.true()
            ),
            sa.Column(
                "default_permission",
                sa.String(30),
                nullable=False,
                server_default="view_watermark",
            ),
            sa.Column(
                "allow_downloads", sa.Boolean(), nullable=False, server_default=sa.false()
            ),
            sa.Column("created_by_member_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["startup_id"], ["Startups.Startup Id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["created_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
            # One deal room per startup: the isolation boundary is the startup.
            sa.UniqueConstraint("startup_id", name="uq_deal_room_startup"),
        )
        op.create_index("ix_deal_rooms_status", "deal_rooms", ["status"])

    if "deal_room_folders" not in present:
        op.create_table(
            "deal_room_folders",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("parent_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(160), nullable=False),
            sa.Column("category", sa.String(40), nullable=False, server_default="other"),
            sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by_member_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["parent_id"], ["deal_room_folders.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["created_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_folders_deal_room_id", "deal_room_folders", ["deal_room_id"]
        )
        op.create_index("ix_deal_room_folders_parent_id", "deal_room_folders", ["parent_id"])
        op.create_index(
            "ix_deal_room_folders_room_parent",
            "deal_room_folders",
            ["deal_room_id", "parent_id"],
        )

    if "deal_room_documents" not in present:
        op.create_table(
            "deal_room_documents",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("folder_id", sa.Integer(), nullable=True),
            sa.Column("title", sa.String(255), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("category", sa.String(40), nullable=False, server_default="other"),
            sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
            sa.Column("current_version_id", sa.Integer(), nullable=True),
            sa.Column("created_by_member_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["folder_id"], ["deal_room_folders.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["created_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_documents_deal_room_id", "deal_room_documents", ["deal_room_id"]
        )
        op.create_index("ix_deal_room_documents_folder_id", "deal_room_documents", ["folder_id"])
        op.create_index("ix_deal_room_documents_status", "deal_room_documents", ["status"])
        op.create_index(
            "ix_deal_room_documents_deleted_at", "deal_room_documents", ["deleted_at"]
        )
        op.create_index(
            "ix_deal_room_documents_room_status",
            "deal_room_documents",
            ["deal_room_id", "status", "deleted_at"],
        )

    if "deal_room_document_versions" not in present:
        op.create_table(
            "deal_room_document_versions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("version_no", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("storage_key", sa.String(512), nullable=False),
            sa.Column("original_filename", sa.String(255), nullable=False),
            sa.Column("content_type", sa.String(120), nullable=False),
            sa.Column("byte_size", sa.BigInteger(), nullable=False, server_default="0"),
            sa.Column("sha256", sa.String(64), nullable=True),
            sa.Column("page_count", sa.Integer(), nullable=True),
            sa.Column("uploaded_by_member_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["document_id"], ["deal_room_documents.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["uploaded_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "document_id", "version_no", name="uq_deal_room_document_version"
            ),
        )
        op.create_index(
            "ix_deal_room_document_versions_document_id",
            "deal_room_document_versions",
            ["document_id"],
        )
        op.create_index(
            "ix_deal_room_document_versions_sha256", "deal_room_document_versions", ["sha256"]
        )

    if "deal_room_participants" not in present:
        op.create_table(
            "deal_room_participants",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("investor_id", sa.Integer(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="invited"),
            sa.Column(
                "permission", sa.String(30), nullable=False, server_default="view_watermark"
            ),
            sa.Column("expires_at", sa.DateTime(), nullable=True),
            sa.Column("nda_accepted_at", sa.DateTime(), nullable=True),
            sa.Column("nda_version", sa.String(40), nullable=True),
            sa.Column("invited_by_member_id", sa.Integer(), nullable=True),
            sa.Column("invite_token_hash", sa.String(64), nullable=True),
            sa.Column("invite_expires_at", sa.DateTime(), nullable=True),
            sa.Column("last_activity_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_id"], ["pulse_members.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["invited_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("deal_room_id", "member_id", name="uq_deal_room_participant"),
        )
        op.create_index(
            "ix_deal_room_participants_deal_room_id", "deal_room_participants", ["deal_room_id"]
        )
        op.create_index(
            "ix_deal_room_participants_member_id", "deal_room_participants", ["member_id"]
        )
        op.create_index("ix_deal_room_participants_status", "deal_room_participants", ["status"])
        op.create_index(
            "ix_deal_room_participants_expires_at", "deal_room_participants", ["expires_at"]
        )
        op.create_index(
            "ix_deal_room_participants_invite_token_hash",
            "deal_room_participants",
            ["invite_token_hash"],
        )
        op.create_index(
            "ix_deal_room_participants_room_status",
            "deal_room_participants",
            ["deal_room_id", "status"],
        )

    if "deal_room_access_grants" not in present:
        op.create_table(
            "deal_room_access_grants",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("participant_id", sa.Integer(), nullable=False),
            sa.Column("resource_type", sa.String(20), nullable=False),
            sa.Column("resource_id", sa.Integer(), nullable=False),
            sa.Column(
                "permission", sa.String(30), nullable=False, server_default="view_watermark"
            ),
            sa.Column("created_by_member_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["participant_id"], ["deal_room_participants.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["created_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "participant_id",
                "resource_type",
                "resource_id",
                name="uq_deal_room_access_grant",
            ),
        )
        op.create_index(
            "ix_deal_room_access_grants_participant_id",
            "deal_room_access_grants",
            ["participant_id"],
        )

    if "deal_room_access_requests" not in present:
        op.create_table(
            "deal_room_access_requests",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("message", sa.Text(), nullable=True),
            sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
            sa.Column("decision_note", sa.Text(), nullable=True),
            sa.Column("decided_by_member_id", sa.Integer(), nullable=True),
            sa.Column("decided_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_id"], ["pulse_members.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["decided_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_access_requests_deal_room_id",
            "deal_room_access_requests",
            ["deal_room_id"],
        )
        op.create_index(
            "ix_deal_room_access_requests_member_id", "deal_room_access_requests", ["member_id"]
        )
        op.create_index(
            "ix_deal_room_access_requests_status", "deal_room_access_requests", ["status"]
        )
        op.create_index(
            "ix_deal_room_access_requests_room_status",
            "deal_room_access_requests",
            ["deal_room_id", "status"],
        )

    if "deal_room_nda_acceptances" not in present:
        op.create_table(
            "deal_room_nda_acceptances",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("member_id", sa.Integer(), nullable=False),
            sa.Column("participant_id", sa.Integer(), nullable=True),
            sa.Column("nda_version", sa.String(40), nullable=False),
            sa.Column("nda_body_sha256", sa.String(64), nullable=True),
            sa.Column("signature_name", sa.String(160), nullable=True),
            sa.Column("accepted_at", sa.DateTime(), nullable=True),
            sa.Column("ip", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(255), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["member_id"], ["pulse_members.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["participant_id"], ["deal_room_participants.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_nda_acceptances_deal_room_id",
            "deal_room_nda_acceptances",
            ["deal_room_id"],
        )
        op.create_index(
            "ix_deal_room_nda_acceptances_member_id", "deal_room_nda_acceptances", ["member_id"]
        )
        op.create_index(
            "ix_deal_room_nda_room_member",
            "deal_room_nda_acceptances",
            ["deal_room_id", "member_id"],
        )

    if "deal_room_questions" not in present:
        op.create_table(
            "deal_room_questions",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=True),
            sa.Column("asked_by_member_id", sa.Integer(), nullable=False),
            sa.Column("participant_id", sa.Integer(), nullable=True),
            sa.Column("question", sa.Text(), nullable=False),
            sa.Column("status", sa.String(20), nullable=False, server_default="open"),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.Column("updated_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["document_id"], ["deal_room_documents.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["asked_by_member_id"], ["pulse_members.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["participant_id"], ["deal_room_participants.id"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_questions_deal_room_id", "deal_room_questions", ["deal_room_id"]
        )
        op.create_index("ix_deal_room_questions_document_id", "deal_room_questions", ["document_id"])
        op.create_index(
            "ix_deal_room_questions_asked_by_member_id",
            "deal_room_questions",
            ["asked_by_member_id"],
        )
        op.create_index("ix_deal_room_questions_status", "deal_room_questions", ["status"])
        op.create_index(
            "ix_deal_room_questions_room_status",
            "deal_room_questions",
            ["deal_room_id", "status"],
        )

    if "deal_room_answers" not in present:
        op.create_table(
            "deal_room_answers",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("question_id", sa.Integer(), nullable=False),
            sa.Column("answered_by_member_id", sa.Integer(), nullable=True),
            sa.Column("answered_by_user_id", sa.Integer(), nullable=True),
            sa.Column("answer", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(
                ["question_id"], ["deal_room_questions.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["answered_by_member_id"], ["pulse_members.id"], ondelete="SET NULL"
            ),
            sa.ForeignKeyConstraint(
                ["answered_by_user_id"], ["User.UserId"], ondelete="SET NULL"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_deal_room_answers_question_id", "deal_room_answers", ["question_id"])

    if "deal_room_audit_events" not in present:
        op.create_table(
            "deal_room_audit_events",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=True),
            sa.Column("startup_id", sa.Integer(), nullable=True),
            sa.Column("actor_member_id", sa.Integer(), nullable=True),
            sa.Column("actor_user_id", sa.Integer(), nullable=True),
            sa.Column("actor_email", sa.String(255), nullable=True),
            sa.Column("actor_role", sa.String(20), nullable=True),
            sa.Column("action", sa.String(60), nullable=False),
            sa.Column("resource_type", sa.String(30), nullable=True),
            sa.Column("resource_id", sa.Integer(), nullable=True),
            sa.Column("meta", sa.Text(), nullable=True),
            sa.Column("ip", sa.String(45), nullable=True),
            sa.Column("user_agent", sa.String(255), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_audit_events_deal_room_id", "deal_room_audit_events", ["deal_room_id"]
        )
        op.create_index(
            "ix_deal_room_audit_events_startup_id", "deal_room_audit_events", ["startup_id"]
        )
        op.create_index(
            "ix_deal_room_audit_events_actor_member_id",
            "deal_room_audit_events",
            ["actor_member_id"],
        )
        op.create_index("ix_deal_room_audit_events_action", "deal_room_audit_events", ["action"])
        op.create_index(
            "ix_deal_room_audit_events_created_at", "deal_room_audit_events", ["created_at"]
        )
        op.create_index(
            "ix_deal_room_audit_room_created",
            "deal_room_audit_events",
            ["deal_room_id", "created_at"],
        )
        op.create_index(
            "ix_deal_room_audit_room_action",
            "deal_room_audit_events",
            ["deal_room_id", "action"],
        )

    if "deal_room_document_views" not in present:
        op.create_table(
            "deal_room_document_views",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("deal_room_id", sa.Integer(), nullable=False),
            sa.Column("document_id", sa.Integer(), nullable=False),
            sa.Column("document_version_id", sa.Integer(), nullable=True),
            sa.Column("participant_id", sa.Integer(), nullable=True),
            sa.Column("member_id", sa.Integer(), nullable=True),
            sa.Column("event", sa.String(20), nullable=False, server_default="view"),
            sa.Column("duration_ms", sa.Integer(), nullable=True),
            sa.Column("pages_viewed", sa.Integer(), nullable=True),
            sa.Column("ip", sa.String(45), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(["deal_room_id"], ["deal_rooms.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(
                ["document_id"], ["deal_room_documents.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["participant_id"], ["deal_room_participants.id"], ondelete="CASCADE"
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_deal_room_document_views_deal_room_id",
            "deal_room_document_views",
            ["deal_room_id"],
        )
        op.create_index(
            "ix_deal_room_document_views_document_id",
            "deal_room_document_views",
            ["document_id"],
        )
        op.create_index(
            "ix_deal_room_document_views_participant_id",
            "deal_room_document_views",
            ["participant_id"],
        )
        op.create_index(
            "ix_deal_room_document_views_member_id", "deal_room_document_views", ["member_id"]
        )
        op.create_index(
            "ix_deal_room_document_views_created_at",
            "deal_room_document_views",
            ["created_at"],
        )
        op.create_index(
            "ix_deal_room_views_room_doc",
            "deal_room_document_views",
            ["deal_room_id", "document_id"],
        )
        op.create_index(
            "ix_deal_room_views_participant",
            "deal_room_document_views",
            ["participant_id", "created_at"],
        )


def downgrade() -> None:
    """Drop the Deal Room schema, children before parents."""
    for table in (
        "deal_room_document_views",
        "deal_room_audit_events",
        "deal_room_answers",
        "deal_room_questions",
        "deal_room_nda_acceptances",
        "deal_room_access_requests",
        "deal_room_access_grants",
        "deal_room_participants",
        "deal_room_document_versions",
        "deal_room_documents",
        "deal_room_folders",
        "deal_rooms",
        "member_entity_links",
    ):
        op.drop_table(table)
