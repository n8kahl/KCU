"""add watchlist table

Revision ID: 0003
Revises: 0002_add_percentile_baselines
Create Date: 2025-02-14 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0003_add_watchlist_table"
down_revision = "0002_add_percentile_baselines"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "watchlist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("timezone('utc', now())")),
        sa.UniqueConstraint("ticker", name="uq_watchlist_ticker"),
    )
    op.execute("ALTER TABLE watchlist ALTER COLUMN position DROP DEFAULT")
    op.execute("ALTER TABLE watchlist ALTER COLUMN created_at DROP DEFAULT")


def downgrade() -> None:
    op.drop_table("watchlist")
