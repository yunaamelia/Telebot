# Data Model: Telegram Cash Flow Management Bot

**Feature**: 001-cashflow-bot  
**Phase**: 1 - Core Design  
**Date**: 2025-12-18

## Overview

PostgreSQL 15+ database schema supporting financial transaction recording, user management, automated reporting, and 3-year data retention policy. Designed for ACID compliance, concurrent writes (20 users), and efficient querying of 180k+ active transactions.

## Entity Relationship Diagram

```
┌─────────────┐         ┌──────────────────┐         ┌────────────┐
│   User      │1       *│   Transaction    │*       1│  Category  │
│─────────────│─────────│──────────────────│─────────│────────────│
│ user_id (PK)│         │ transaction_id   │         │ category_id│
│ telegram_id │         │ user_id (FK)     │         │ name       │
│ employee_id │         │ category_id (FK) │         │ type       │
│ status      │         │ amount           │         │ emoji      │
│ role        │         │ type             │         │ sort_order │
└─────────────┘         │ description      │         └────────────┘
                        │ timestamp        │
                        │ transaction_date │
                        │ status           │
                        └──────────────────┘
                                 │
                                 │ *
                        ┌────────┴────────┐
                        │  Daily Summary  │
                        │─────────────────│
                        │ summary_id (PK) │
                        │ summary_date    │
                        │ total_income    │
                        │ total_expenses  │
                        │ transaction_count│
                        │ category_breakdown (JSONB)│
                        └──────────────────┘
```

## Table Definitions

### 1. users

Stores authorized bot users with registration workflow support.

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL UNIQUE,
    telegram_username VARCHAR(255),
    display_name VARCHAR(255),
    employee_id VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  
        -- Values: 'pending', 'approved', 'rejected'
    role VARCHAR(20) NOT NULL DEFAULT 'staff',  
        -- Values: 'staff', 'management', 'admin'
    registration_request_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    approved_date TIMESTAMP WITH TIME ZONE,
    approved_by_user_id INT REFERENCES users(user_id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_status CHECK (status IN ('pending', 'approved', 'rejected')),
    CONSTRAINT chk_role CHECK (role IN ('staff', 'management', 'admin'))
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_status ON users(status) WHERE status = 'approved';
```

**Field Descriptions**:

- `telegram_id`: Telegram user ID (from Update.effective_user.id)
- `employee_id`: Company employee ID/code for registration verification
- `status`: Registration approval status
- `role`: Access level (future: role-based permissions)

---

### 2. categories

Expense classification types (fixed in MVP, no user-defined categories).

```sql
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    type VARCHAR(20) NOT NULL,  
        -- Values: 'income', 'expense'
    emoji VARCHAR(10),
    sort_order INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_category_type CHECK (type IN ('income', 'expense'))
);

CREATE INDEX idx_categories_type ON categories(type);
```

**Seed Data**:

```sql
INSERT INTO categories (name, type, emoji, sort_order) VALUES
    ('Income', 'income', '💰', 1),
    ('Operational', 'expense', '🏢', 2),
    ('Salaries', 'expense', '👔', 3),
    ('Supplies', 'expense', '📦', 4),
    ('Marketing', 'expense', '📢', 5),
    ('Other', 'expense', '➕', 6);
```

---

### 3. transactions

Core financial records with WITA timezone handling and audit trail.

```sql
CREATE TABLE transactions (
    transaction_id VARCHAR(50) PRIMARY KEY,  
        -- Format: TX20251218001 (TXYYYYMMDDNNN)
    user_id INT NOT NULL REFERENCES users(user_id),
    category_id INT NOT NULL REFERENCES categories(category_id),
    amount NUMERIC(15, 2) NOT NULL,  
        -- Max: 10,000,000,000.00 (10 billion per FR-022)
    type VARCHAR(20) NOT NULL,  
        -- Values: 'income', 'expense'
    description TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),  
        -- Stored in UTC, displayed in WITA
    transaction_date DATE NOT NULL,  
        -- Computed from timestamp in WITA timezone for daily reports
    status VARCHAR(20) NOT NULL DEFAULT 'recorded',  
        -- Values: 'recorded', 'archived', 'deleted' (soft delete)
    is_duplicate_confirmed BOOLEAN DEFAULT FALSE,  
        -- True if user confirmed duplicate warning
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    CONSTRAINT chk_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_amount_max CHECK (amount <= 10000000000),
    CONSTRAINT chk_type CHECK (type IN ('income', 'expense')),
    CONSTRAINT chk_status CHECK (status IN ('recorded', 'archived', 'deleted'))
);

-- Performance indexes for common queries
CREATE INDEX idx_transactions_date ON transactions(transaction_date DESC);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_category ON transactions(category_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);

-- Partial index for active (non-archived) data - speeds up recent queries
CREATE INDEX idx_transactions_active ON transactions(transaction_date)
    WHERE status = 'recorded' AND transaction_date > CURRENT_DATE - INTERVAL '1 year';

-- Composite index for daily summary generation
CREATE INDEX idx_transactions_daily_summary
    ON transactions(transaction_date, type, category_id)
    WHERE status = 'recorded';

-- Full-text search index for transaction descriptions
CREATE INDEX idx_transactions_description_fts ON transactions
    USING gin(to_tsvector('indonesian', description));
```

**Field Descriptions**:

- `transaction_id`: Sequential ID with date prefix for easy human readability
- `timestamp`: UTC timestamp of when transaction recorded
- `transaction_date`: WITA date (computed from timestamp) for grouping in daily reports
- `is_duplicate_confirmed`: Tracks if duplicate warning was acknowledged (FR-023)

**Transaction ID Generation**:

```python
def generate_transaction_id(date: datetime.date, sequence: int) -> str:
    """Generate sequential transaction ID: TX20251218001"""
    return f"TX{date.strftime('%Y%m%d')}{sequence:03d}"
```

---

### 4. daily_summaries

Pre-computed daily aggregates for fast report generation.

```sql
CREATE TABLE daily_summaries (
    summary_id SERIAL PRIMARY KEY,
    summary_date DATE NOT NULL UNIQUE,
    total_income NUMERIC(15, 2) NOT NULL DEFAULT 0,
    total_expenses NUMERIC(15, 2) NOT NULL DEFAULT 0,
    net_cash_flow NUMERIC(15, 2) GENERATED ALWAYS AS (total_income - total_expenses) STORED,
    transaction_count INT NOT NULL DEFAULT 0,
    income_count INT NOT NULL DEFAULT 0,
    expense_count INT NOT NULL DEFAULT 0,
    category_breakdown JSONB,  
        -- Format: {"Operational": 150000, "Salaries": 500000, ...}
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    report_delivered_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_amounts_non_negative CHECK (
        total_income >= 0 AND total_expenses >= 0
    )
);

CREATE INDEX idx_daily_summaries_date ON daily_summaries(summary_date DESC);
CREATE INDEX idx_daily_summaries_breakdown ON daily_summaries USING gin(category_breakdown);
```

**Field Descriptions**:

- `net_cash_flow`: Computed column (total_income - total_expenses)
- `category_breakdown`: JSONB for flexible category aggregation
- `report_delivered_at`: Tracks successful 24:00 WITA report delivery

**Example category_breakdown**:

```json
{
  "Income": 2500000,
  "Operational": 500000,
  "Salaries": 1000000,
  "Supplies": 150000,
  "Marketing": 200000,
  "Other": 50000
}
```

---

### 5. reports (Optional - Future Enhancement)

Archive of generated reports for audit trail.

```sql
CREATE TABLE reports (
    report_id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    report_type VARCHAR(50) NOT NULL,  
        -- Values: 'daily', 'weekly', 'monthly', 'manual'
    summary_id INT REFERENCES daily_summaries(summary_id),
    recipient_chat_id BIGINT,  
        -- Telegram chat ID where report was sent
    delivery_status VARCHAR(20) NOT NULL DEFAULT 'pending',  
        -- Values: 'pending', 'sent', 'failed', 'retrying'
    retry_count INT DEFAULT 0,
    error_message TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,

    CONSTRAINT chk_report_type CHECK (report_type IN ('daily', 'weekly', 'monthly', 'manual')),
    CONSTRAINT chk_delivery_status CHECK (delivery_status IN ('pending', 'sent', 'failed', 'retrying'))
);

CREATE INDEX idx_reports_date ON reports(report_date DESC);
CREATE INDEX idx_reports_status ON reports(delivery_status);
```

---

## SQLAlchemy ORM Models

### User Model

```python
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    telegram_username = Column(String(255))
    display_name = Column(String(255))
    employee_id = Column(String(100))
    status = Column(String(20), nullable=False, default='pending')
    role = Column(String(20), nullable=False, default='staff')
    registration_request_date = Column(DateTime(timezone=True), server_default=func.now())
    approved_date = Column(DateTime(timezone=True))
    approved_by_user_id = Column(Integer, ForeignKey('users.user_id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    approver = relationship("User", remote_side=[user_id])

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected')", name='chk_status'),
        CheckConstraint("role IN ('staff', 'management', 'admin')", name='chk_role'),
    )

    def is_authorized(self) -> bool:
        """Check if user can access bot features"""
        return self.status == 'approved'
```

### Transaction Model

```python
from decimal import Decimal
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Date, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.database import Base

class Transaction(Base):
    __tablename__ = 'transactions'

    transaction_id = Column(String(50), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.category_id'), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    type = Column(String(20), nullable=False)
    description = Column(String)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    transaction_date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False, default='recorded')
    is_duplicate_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="transactions")
    category = relationship("Category")

    __table_args__ = (
        CheckConstraint('amount > 0', name='chk_amount_positive'),
        CheckConstraint('amount <= 10000000000', name='chk_amount_max'),
        CheckConstraint("type IN ('income', 'expense')", name='chk_type'),
        CheckConstraint("status IN ('recorded', 'archived', 'deleted')", name='chk_status'),
    )

    @property
    def formatted_amount(self) -> str:
        """Format amount with Rupiah formatting"""
        return f"Rp {self.amount:,.0f}"
```

### Category Model

```python
class Category(Base):
    __tablename__ = 'categories'

    category_id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    type = Column(String(20), nullable=False)
    emoji = Column(String(10))
    sort_order = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')", name='chk_category_type'),
    )
```

### DailySummary Model

```python
from sqlalchemy.dialects.postgresql import JSONB

class DailySummary(Base):
    __tablename__ = 'daily_summaries'

    summary_id = Column(Integer, primary_key=True)
    summary_date = Column(Date, unique=True, nullable=False)
    total_income = Column(Numeric(15, 2), nullable=False, default=0)
    total_expenses = Column(Numeric(15, 2), nullable=False, default=0)
    # net_cash_flow computed by PostgreSQL
    transaction_count = Column(Integer, nullable=False, default=0)
    income_count = Column(Integer, nullable=False, default=0)
    expense_count = Column(Integer, nullable=False, default=0)
    category_breakdown = Column(JSONB)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    report_delivered_at = Column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint('total_income >= 0 AND total_expenses >= 0',
                       name='chk_amounts_non_negative'),
    )
```

---

## Data Retention & Archival Strategy

Per FR-031: 1-year active retention + 2-year archive + deletion after 3 years.

### Archival Process

```sql
-- Monthly archival job (run on 1st of each month)
UPDATE transactions
SET status = 'archived'
WHERE transaction_date < CURRENT_DATE - INTERVAL '1 year'
  AND status = 'recorded';

-- Delete after 3 years total retention
DELETE FROM transactions
WHERE transaction_date < CURRENT_DATE - INTERVAL '3 years'
  AND status = 'archived';
```

### Query Performance Optimization

**Active Data Queries** (use partial index):

```sql
SELECT * FROM transactions
WHERE transaction_date > CURRENT_DATE - INTERVAL '1 year'
  AND status = 'recorded';  -- Uses idx_transactions_active
```

**Archived Data Access** (slower, for audits only):

```sql
SELECT * FROM transactions
WHERE status = 'archived'
  AND transaction_date BETWEEN '2023-01-01' AND '2023-12-31';
```

---

## Migration Strategy

Using Alembic for version-controlled schema changes.

### Initial Migration

```python
# migrations/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create users table
    op.create_table('users', ...)

    # Create categories table
    op.create_table('categories', ...)

    # Create transactions table
    op.create_table('transactions', ...)

    # Create daily_summaries table
    op.create_table('daily_summaries', ...)

    # Seed categories
    op.execute("""
        INSERT INTO categories (name, type, emoji, sort_order) VALUES
        ('Income', 'income', '💰', 1),
        ('Operational', 'expense', '🏢', 2),
        ('Salaries', 'expense', '👔', 3),
        ('Supplies', 'expense', '📦', 4),
        ('Marketing', 'expense', '📢', 5),
        ('Other', 'expense', '➕', 6)
    """)

def downgrade():
    op.drop_table('daily_summaries')
    op.drop_table('transactions')
    op.drop_table('categories')
    op.drop_table('users')
```

---

## Data Integrity Rules

### Business Logic Constraints

1. **Amount Validation**: 0 < amount ≤ 10,000,000,000 (FR-022)
2. **User Authorization**: Only `status='approved'` users can record transactions
3. **Category Consistency**: Transaction type must match category type
4. **Date Accuracy**: transaction_date derived from timestamp in WITA timezone
5. **Duplicate Detection**: Check for identical (amount, description, category, user) within 60 seconds (FR-023)

### Referential Integrity

- Transactions CASCADE delete when user deleted (preserve audit trail: use soft delete instead)
- Categories RESTRICT delete if transactions exist
- Daily summaries ON DELETE SET NULL for summary_id in reports

---

## Performance Benchmarks

**Expected Query Performance** (with proper indexes):

| Query | Expected Time | Volume |
|-------|--------------|--------|
| Record single transaction | <10ms | 500/day |
| Daily summary (current day) | <50ms | Active: ~500 tx |
| Transaction history (paginated) | <30ms | 10 records |
| Category aggregation | <20ms | 6 categories |
| Duplicate detection lookup | <15ms | 60-second window |

**Index Maintenance**:

- Reindex monthly: `REINDEX INDEX CONCURRENTLY idx_transactions_active;`
- VACUUM ANALYZE weekly: `VACUUM ANALYZE transactions;`

---

**Data Model Complete** ✅  
**Schema Version**: 1.0.0  
**Next**: contracts/commands.yaml and quickstart.md
