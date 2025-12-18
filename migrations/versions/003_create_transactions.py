"""Create transactions table with all indexes

Revision ID: 003_create_transactions
Revises: 002_create_categories
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_create_transactions'
down_revision = '002_create_categories'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create transactions table with comprehensive indexing."""
    # Create table
    op.create_table(
        'transactions',
        sa.Column('transaction_id', sa.String(length=50), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('transaction_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='recorded'),
        sa.Column('is_duplicate_confirmed', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('amount > 0', name='chk_amount_positive'),
        sa.CheckConstraint('amount <= 10000000000', name='chk_amount_max'),
        sa.CheckConstraint("type IN ('income', 'expense')", name='chk_type'),
        sa.CheckConstraint("status IN ('recorded', 'archived', 'deleted')", name='chk_status'),
        sa.ForeignKeyConstraint(['category_id'], ['categories.category_id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('transaction_id')
    )

    # Create performance indexes for common queries
    op.create_index('idx_transactions_date', 'transactions', ['transaction_date'],
                    postgresql_ops={'transaction_date': 'DESC'})
    op.create_index('idx_transactions_user', 'transactions', ['user_id'])
    op.create_index('idx_transactions_category', 'transactions', ['category_id'])
    op.create_index('idx_transactions_timestamp', 'transactions', ['timestamp'])

    # Partial index for active (non-archived) data - speeds up recent queries
    op.create_index('idx_transactions_active', 'transactions', ['transaction_date'],
                    postgresql_where=sa.text("status = 'recorded' AND transaction_date > CURRENT_DATE - INTERVAL '1 year'"))

    # Composite index for daily summary generation
    op.create_index('idx_transactions_daily_summary', 'transactions',
                    ['transaction_date', 'type', 'category_id'],
                    postgresql_where=sa.text("status = 'recorded'"))

    # Full-text search index for transaction descriptions
    op.execute("""
        CREATE INDEX idx_transactions_description_fts ON transactions
        USING gin(to_tsvector('indonesian', COALESCE(description, '')))
    """)


def downgrade() -> None:
    """Drop transactions table."""
    op.drop_index('idx_transactions_description_fts', table_name='transactions')
    op.drop_index('idx_transactions_daily_summary', table_name='transactions')
    op.drop_index('idx_transactions_active', table_name='transactions')
    op.drop_index('idx_transactions_timestamp', table_name='transactions')
    op.drop_index('idx_transactions_category', table_name='transactions')
    op.drop_index('idx_transactions_user', table_name='transactions')
    op.drop_index('idx_transactions_date', table_name='transactions')
    op.drop_table('transactions')
