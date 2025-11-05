"""create core tables"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_create_core_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candles",
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("timeframe", sa.String(length=8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(12, 4), nullable=False),
        sa.Column("high", sa.Numeric(12, 4), nullable=False),
        sa.Column("low", sa.Numeric(12, 4), nullable=False),
        sa.Column("close", sa.Numeric(12, 4), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint("ticker", "timeframe", "ts"),
    )

    op.create_table(
        "levels",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("premarket_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("premarket_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("prior_high", sa.Numeric(12, 4), nullable=True),
        sa.Column("prior_low", sa.Numeric(12, 4), nullable=True),
        sa.Column("prior_close", sa.Numeric(12, 4), nullable=True),
        sa.Column("open_print", sa.Numeric(12, 4), nullable=True),
        sa.PrimaryKeyConstraint("day", "ticker"),
    )

    op.create_table(
        "option_snapshots",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer, "sqlite"), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contract", sa.String(length=32), nullable=False),
        sa.Column("bid", sa.Numeric(12, 4), nullable=False),
        sa.Column("ask", sa.Numeric(12, 4), nullable=False),
        sa.Column("mid", sa.Numeric(12, 4), nullable=False),
        sa.Column("oi", sa.Integer(), nullable=True),
        sa.Column("vol", sa.Integer(), nullable=True),
        sa.Column("iv", sa.Numeric(8, 4), nullable=True),
        sa.Column("delta", sa.Numeric(6, 4), nullable=True),
        sa.Column("gamma", sa.Numeric(6, 4), nullable=True),
        sa.Column("theta", sa.Numeric(6, 4), nullable=True),
        sa.Column("vega", sa.Numeric(6, 4), nullable=True),
        sa.Index("ix_option_snapshots_ticker_ts", "ticker", "ts"),
    )

    op.create_table(
        "snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("regime", sa.String(length=16), nullable=False),
        sa.Column("score", sa.Numeric(6, 2), nullable=False),
        sa.Column("prob", sa.JSON(), nullable=False),
        sa.Column("bands", sa.JSON(), nullable=False),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("orb", sa.JSON(), nullable=False),
        sa.Column("patience", sa.JSON(), nullable=False),
        sa.Column("penalties", sa.JSON(), nullable=False),
        sa.Column("bonuses", sa.JSON(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("rationale", sa.JSON(), nullable=False),
        sa.Index("ix_snapshots_ticker_ts", "ticker", "ts"),
    )


def downgrade() -> None:
    op.drop_table("snapshots")
    op.drop_table("option_snapshots")
    op.drop_table("levels")
    op.drop_table("candles")
