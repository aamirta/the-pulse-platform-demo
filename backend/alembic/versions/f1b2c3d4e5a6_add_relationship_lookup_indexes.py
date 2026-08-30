"""Add reverse-lookup indexes on relationship foreign keys.

Every association table had only its composite primary key, which indexes the
leading column alone. Lookups driven by the trailing column -- notably
``StartupFounders."Founder Id"``, executed once per row when rendering the
founders directory -- fell back to sequential scans. These indexes also cover
the ecosystem graph joins, which now include IncubatorFounders.

Revision ID: f1b2c3d4e5a6
Revises: d94e7c2f1a58
"""

from collections.abc import Sequence

from alembic import op

revision: str = "f1b2c3d4e5a6"
down_revision: str | None = "d94e7c2f1a58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: (index name, table, column)
INDEXES: list[tuple[str, str, str]] = [
    ("ix_startupfounders_founder_id", "StartupFounders", "Founder Id"),
    ("ix_startupincubators_incubator_id", "StartupIncubators", "Incubator Id"),
    ("ix_incubatorfounders_founder_id", "IncubatorFounders", "Founder Id"),
    ("ix_investements_investor_id", "Investements", "Investor Id"),
    ("ix_investements_funding_round_id", "Investements", "Funding_Round_Id"),
    ("ix_fundingrounds_startup_id", "FundingRounds", "Startup Id"),
    ("ix_education_founder_id", "Education", "Founder Id"),
    ("ix_education_institute_id", "Education", "Institute Id"),
    ("ix_experiences_founder_id", "Experiences", "Founder Id"),
]


def upgrade() -> None:
    for name, table, column in INDEXES:
        op.create_index(name, table, [column], unique=False, if_not_exists=True)


def downgrade() -> None:
    for name, table, _column in INDEXES:
        op.drop_index(name, table_name=table, if_exists=True)
