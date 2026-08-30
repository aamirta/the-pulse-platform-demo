"""Resync identity sequences with existing table contents.

The production data was bulk-imported with explicit primary keys (see
``import_data.py`` and ``scrapers/``), which does not advance the owning
sequence. Every sequence therefore still handed out low values that collided
with imported rows, so any INSERT relying on the column default raised
``UniqueViolation`` and surfaced as an HTTP 500. Confirmed breakages: creating a
newsfeed post, onboarding a member whose role maps to a Startup or Incubator,
and creating articles/resources.

This migration walks every sequence owned by a column and fast-forwards it past
``max(column)``. It is idempotent and safe to re-run.

Revision ID: b71c3f0d9a24
Revises: 07945b624739
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b71c3f0d9a24"
down_revision: str | Sequence[str] | None = "07945b624739"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Finds every sequence owned by a table column, then sets it to max(column).
# ``setval(..., false)`` on an empty table leaves the sequence at its start
# value so the next nextval() still returns 1.
_RESYNC_SQL = """
DO $$
DECLARE
    rec RECORD;
    max_id BIGINT;
BEGIN
    FOR rec IN
        SELECT
            quote_ident(seq_ns.nspname) || '.' || quote_ident(seq.relname) AS seq_name,
            quote_ident(tbl_ns.nspname) || '.' || quote_ident(tbl.relname) AS tbl_name,
            quote_ident(col.attname) AS col_name
        FROM pg_class seq
        JOIN pg_namespace seq_ns ON seq_ns.oid = seq.relnamespace
        JOIN pg_depend dep ON dep.objid = seq.oid AND dep.classid = 'pg_class'::regclass
        JOIN pg_class tbl ON tbl.oid = dep.refobjid
        JOIN pg_namespace tbl_ns ON tbl_ns.oid = tbl.relnamespace
        JOIN pg_attribute col ON col.attrelid = tbl.oid AND col.attnum = dep.refobjsubid
        WHERE seq.relkind = 'S'
          AND dep.deptype IN ('a', 'i')
          AND tbl_ns.nspname = 'public'
    LOOP
        EXECUTE format('SELECT max(%s) FROM %s', rec.col_name, rec.tbl_name) INTO max_id;
        IF max_id IS NULL THEN
            EXECUTE format('SELECT setval(%L, 1, false)', rec.seq_name);
        ELSE
            EXECUTE format('SELECT setval(%L, %s, true)', rec.seq_name, max_id);
        END IF;
    END LOOP;
END
$$;
"""


def upgrade() -> None:
    """Fast-forward every column-owned sequence past the largest existing key."""
    # SQLite (used by the test suite) has no sequences; rowid handles this natively.
    if op.get_bind().dialect.name != "postgresql":
        return
    op.execute(sa.text(_RESYNC_SQL))


def downgrade() -> None:
    """No-op: rewinding sequences would reintroduce primary-key collisions."""
