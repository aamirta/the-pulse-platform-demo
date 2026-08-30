"""link founders to member accounts

Adds ``Founders.member_id``, the account behind a founder profile.

Founder ids are strings: a scraped row carries a numeric id, a row created at
onboarding carries a random token. Neither fits ``member_entity_links``, whose
``entity_id`` is an integer — which is why founders, alone among the directory
entities, had no way to be resolved to an account and so no Message button on
their profile page.

Going forward the column is stamped where the identity is known rather than
inferred: ``POST /members/onboard`` builds the Founder row from the member's own
details, so it records who that member is.

The backfill is deliberately narrow, because a wrong link here would put a
"message this person" button on a stranger's profile:

  * only rows whose id is *not* numeric are considered — a numeric id can only
    have come from the scraped import, never from onboarding;
  * only where exactly one confirmed member's name matches, so an ambiguous
    pair is left NULL rather than guessed at.

Everything it does not match stays NULL, which reads as "nobody has claimed this
profile" and simply renders no button.

Revision ID: e665ab5af170
Revises: 2e8937d4b5e3
Create Date: 2026-08-27 10:41:03.118942
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e665ab5af170"
down_revision: str | Sequence[str] | None = "2e8937d4b5e3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# The two dialects spell "this id is not a plain number" differently. Kept as
# one statement per dialect rather than one clever portable expression, because
# a subtly wrong pattern here would mislink real people.
_BACKFILL = """
    UPDATE "Founders"
       SET member_id = (
             SELECT m.id
               FROM pulse_members m
              WHERE LOWER(TRIM(m.full_name)) = LOWER(TRIM("Founders".name))
                AND m.is_confirmed = {true_literal}
           )
     WHERE member_id IS NULL
       AND name IS NOT NULL
       AND TRIM(name) <> ''
       AND {not_numeric}
       AND (
             SELECT COUNT(*)
               FROM pulse_members m
              WHERE LOWER(TRIM(m.full_name)) = LOWER(TRIM("Founders".name))
                AND m.is_confirmed = {true_literal}
           ) = 1
"""


def upgrade() -> None:
    """Add the column, then link the onboarding-created rows we can be sure of."""
    op.add_column("Founders", sa.Column("member_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_Founders_member_id"), "Founders", ["member_id"])

    dialect = op.get_bind().dialect.name
    # SQLite cannot ALTER a table to add a constraint; doing it there would mean
    # rewriting the whole table through batch mode. The tests run on SQLite and
    # only need the column, while production is PostgreSQL and gets the real
    # referential guarantee, so the constraint is created where it is supported.
    if dialect != "sqlite":
        op.create_foreign_key(
            "fk_founders_member_id",
            "Founders",
            "pulse_members",
            ["member_id"],
            ["id"],
            ondelete="SET NULL",
        )

    if dialect == "sqlite":
        not_numeric = '"Founder Id" GLOB \'*[^0-9]*\''
        true_literal = "1"
    else:
        not_numeric = '"Founder Id" !~ \'^[0-9]+$\''
        true_literal = "TRUE"

    op.execute(
        sa.text(_BACKFILL.format(not_numeric=not_numeric, true_literal=true_literal))
    )


def downgrade() -> None:
    """Drop the link. The founder rows themselves are untouched."""
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("fk_founders_member_id", "Founders", type_="foreignkey")
    op.drop_index(op.f("ix_Founders_member_id"), table_name="Founders")
    op.drop_column("Founders", "member_id")
