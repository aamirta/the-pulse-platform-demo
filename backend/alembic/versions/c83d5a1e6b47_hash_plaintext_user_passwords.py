"""Replace plaintext User passwords with Argon2id hashes.

The seeded administrator row stored its password as literal plaintext. Two
consequences: the credential was readable by anyone with database access, and
``passlib`` raised ``UnknownHashError`` during verification, so POST
/api/v1/auth/login answered 500 instead of 401.

This migration hashes any stored value that is not already a recognised hash,
keeping the existing credential working while fixing how it is stored. It is
idempotent: rows that already hold a known hash format are left untouched.

Operators should still rotate any credential that was previously stored in
plaintext, since its value was exposed for as long as it lived in the database.

Revision ID: c83d5a1e6b47
Revises: b71c3f0d9a24
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c83d5a1e6b47"
down_revision: str | Sequence[str] | None = "b71c3f0d9a24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Prefixes of password formats this application already understands.
_KNOWN_HASH_PREFIXES = (
    "$argon2",
    "$2a$",
    "$2b$",
    "$2y$",
    "$scrypt$",
    "scrypt:",
    "pbkdf2:",
    "$pbkdf2",
)


def _is_hashed(value: str) -> bool:
    """Return True when the stored value already looks like a password hash."""
    return value.startswith(_KNOWN_HASH_PREFIXES)


def upgrade() -> None:
    """Hash any User.Password still stored in a non-hash format."""
    # Imported lazily so this module stays importable without the app configured.
    from backend.core.security import hash_password

    connection = op.get_bind()
    rows = connection.execute(sa.text('SELECT "UserId", "Password" FROM "User"')).fetchall()

    for user_id, password in rows:
        if not password or _is_hashed(password):
            continue
        connection.execute(
            sa.text('UPDATE "User" SET "Password" = :hashed WHERE "UserId" = :user_id'),
            {"hashed": hash_password(password), "user_id": user_id},
        )


def downgrade() -> None:
    """No-op: hashing is one-way, so the plaintext cannot be restored."""
