"""add percentile baselines and market micro column

Revision ID: 0002_add_percentile_baselines
Revises: 0001_create_core_tables
Create Date: 2025-11-04
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0002_add_percentile_baselines"
down_revision = "0001_create_core_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("snapshots", sa.Column("market_micro", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.create_table(
        "percentile_baselines",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("metric", sa.String(length=64), nullable=False),
        sa.Column("bucket_key", sa.String(length=128), nullable=False),
        sa.Column("p50", sa.Float(), nullable=False),
        sa.Column("p75", sa.Float(), nullable=False),
        sa.Column("p90", sa.Float(), nullable=False),
        sa.Column("p95", sa.Float(), nullable=False),
        sa.Column("asof", sa.Date(), nullable=False),
    )
    op.create_index("ix_percentile_baselines_metric", "percentile_baselines", ["metric"])
    op.create_index("ix_percentile_baselines_bucket_key", "percentile_baselines", ["bucket_key"])
    op.create_index("ix_percentile_baselines_asof", "percentile_baselines", ["asof"])


def downgrade() -> None:
    op.drop_index("ix_percentile_baselines_asof", table_name="percentile_baselines")
    op.drop_index("ix_percentile_baselines_bucket_key", table_name="percentile_baselines")
    op.drop_index("ix_percentile_baselines_metric", table_name="percentile_baselines")
    op.drop_table("percentile_baselines")
    op.drop_column("snapshots", "market_micro")
