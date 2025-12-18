"""Create users table

Revision ID: 001_create_users
Revises:
Create Date: 2025-12-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_create_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create users table with registration approval workflow support."""
    op.create_table(
        'users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.BigInteger(), nullable=False),
        sa.Column('telegram_username', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('employee_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='staff'),
        sa.Column('registration_request_date', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('approved_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='chk_status'),
        sa.CheckConstraint("role IN ('staff', 'management', 'admin')", name='chk_role'),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.user_id'], ),
        sa.PrimaryKeyConstraint('user_id')
    )

    # Create indexes
    op.create_index('idx_users_telegram_id', 'users', ['telegram_id'], unique=True)
    op.create_index('idx_users_status', 'users', ['status'],
                    postgresql_where=sa.text("status = 'approved'"))


def downgrade() -> None:
    """Drop users table."""
    op.drop_index('idx_users_status', table_name='users')
    op.drop_index('idx_users_telegram_id', table_name='users')
    op.drop_table('users')
