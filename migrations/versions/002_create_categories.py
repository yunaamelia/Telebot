"""Create categories table with seed data.

Revision ID: 002_create_categories
Revises: 001_create_users
Create Date: 2025-12-18

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '002_create_categories'
down_revision = '001_create_users'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create categories table and seed with default categories."""
    # Create table
    op.create_table(
        'categories',
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('emoji', sa.String(length=10), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('NOW()'),
            nullable=True,
        ),
        sa.CheckConstraint("type IN ('income', 'expense')", name='chk_category_type'),
        sa.PrimaryKeyConstraint('category_id'),
        sa.UniqueConstraint('name')
    )

    # Create index
    op.create_index('idx_categories_type', 'categories', ['type'])

    # Seed default categories
    op.execute("""
        INSERT INTO categories (name, type, emoji, sort_order) VALUES
        ('Income', 'income', '💰', 1),
        ('Operational', 'expense', '🏢', 2),
        ('Salaries', 'expense', '👔', 3),
        ('Supplies', 'expense', '📦', 4),
        ('Marketing', 'expense', '📢', 5),
        ('Other', 'expense', '➕', 6)
    """)


def downgrade() -> None:
    """Drop categories table."""
    op.drop_index('idx_categories_type', table_name='categories')
    op.drop_table('categories')
