"""Create daily_summaries table with JSONB support

Revision ID: 004_create_daily_summaries
Revises: 003_create_transactions
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_create_daily_summaries'
down_revision = '003_create_transactions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create daily_summaries table with computed net_cash_flow column."""
    # Create table
    op.create_table(
        'daily_summaries',
        sa.Column('summary_id', sa.Integer(), nullable=False),
        sa.Column('summary_date', sa.Date(), nullable=False),
        sa.Column('total_income', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('total_expenses', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0'),
        sa.Column('transaction_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('income_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('expense_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('category_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('report_delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('total_income >= 0 AND total_expenses >= 0',
                          name='chk_amounts_non_negative'),
        sa.PrimaryKeyConstraint('summary_id'),
        sa.UniqueConstraint('summary_date')
    )

    # Add computed column for net_cash_flow
    op.execute("""
        ALTER TABLE daily_summaries
        ADD COLUMN net_cash_flow NUMERIC(15, 2)
        GENERATED ALWAYS AS (total_income - total_expenses) STORED
    """)

    # Create indexes
    op.create_index('idx_daily_summaries_date', 'daily_summaries', ['summary_date'],
                    postgresql_ops={'summary_date': 'DESC'})
    op.create_index('idx_daily_summaries_breakdown', 'daily_summaries', ['category_breakdown'],
                    postgresql_using='gin')


def downgrade() -> None:
    """Drop daily_summaries table."""
    op.drop_index('idx_daily_summaries_breakdown', table_name='daily_summaries')
    op.drop_index('idx_daily_summaries_date', table_name='daily_summaries')
    op.drop_table('daily_summaries')
