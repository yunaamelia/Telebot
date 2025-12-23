# Quick Start Guide: Cash Flow Bot Development

**Feature**: 001-cashflow-bot  
**Last Updated**: 2025-12-18  
**Target Audience**: Developers setting up local environment

## Overview

This guide will help you set up a complete development environment for the Telegram Cash Flow Management Bot in under 2 hours. You'll have a working local instance with database, test data, and all development tools configured.

---

## Prerequisites

### Required Software

| Tool | Version | Installation | Verification |
|------|---------|--------------|--------------|
| Python | 3.11+ | `sudo apt install python3.11` | `python3 --version` |
| PostgreSQL | 15+ | `sudo apt install postgresql-15` | `psql --version` |
| Docker | 24+ | [docs.docker.com/install](https://docs.docker.com/install) | `docker --version` |
| Git | 2.x | `sudo apt install git` | `git --version` |

### Telegram Bot Setup

1. **Create Bot** (one-time setup):

   ```bash
   # Message @BotFather on Telegram
   /newbot
   # Follow prompts, save the bot token
   ```

2. **Get Chat IDs**:

   ```bash
   # Your Telegram user ID
   # Message @userinfobot: /start

   # Create a test management group
   # Add @RawDataBot to get group chat ID
   ```

---

## Step 1: Clone & Environment Setup (15 minutes)

### 1.1 Clone Repository

```bash
cd ~/projects
git clone https://github.com/your-org/cashflow-bot.git
cd cashflow-bot
git checkout 001-cashflow-bot
```

### 1.2 Create Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Verify
which python  # Should show venv/bin/python
```

### 1.3 Install Dependencies

```bash
# Production dependencies
pip install -r requirements.txt

# Development dependencies (testing, linting)
pip install -r requirements-dev.txt

# Verify installation
pip list | grep -E "python-telegram-bot|sqlalchemy|pytest"
```

**Expected output**:

```
python-telegram-bot  20.7
SQLAlchemy          2.0.25
pytest              7.4.3
pytest-asyncio      0.21.1
pytest-cov          4.1.0
```

---

## Step 2: Database Setup (10 minutes)

### 2.1 Start PostgreSQL with Docker

```bash
# Start PostgreSQL container
docker-compose up -d postgres

# Wait for startup (5-10 seconds)
docker-compose logs -f postgres
# Look for: "database system is ready to accept connections"

# Verify
docker ps | grep postgres
```

### 2.2 Create Database

```bash
# Option A: Using docker exec
docker exec -it cashflow-bot-postgres-1 psql -U dev -c "CREATE DATABASE cashflow_dev;"

# Option B: Using psql directly (if installed locally)
psql -h localhost -U dev -c "CREATE DATABASE cashflow_dev;"
# Password: dev_password (from docker-compose.yml)
```

### 2.3 Run Migrations

```bash
# Initialize Alembic
alembic upgrade head

# Verify tables created
psql -h localhost -U dev -d cashflow_dev -c "\dt"
```

**Expected tables**:

```
 public | users
 public | categories
 public | transactions
 public | daily_summaries
 public | reports
```

### 2.4 Seed Test Data

```bash
# Run seed script
python scripts/seed_dev_data.py

# Verify
psql -h localhost -U dev -d cashflow_dev -c "SELECT name, emoji FROM categories;"
```

**Expected output**:

```
    name      | emoji
--------------+-------
 Income       | 💰
 Operational  | 🏢
 Salaries     | 👔
 Supplies     | 📦
 Marketing    | 📢
 Other        | ➕
```

---

## Step 3: Configuration (5 minutes)

### 3.1 Create Environment File

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

### 3.2 Configure Variables

```bash
# .env file content
# ===================

# Telegram Bot
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
MANAGEMENT_CHAT_ID=-1001234567890

# Database
DATABASE_URL=postgresql://dev:dev_password@localhost:5432/cashflow_dev

# Timezone
TIMEZONE=Asia/Makassar  # WITA (UTC+8)

# Logging
LOG_LEVEL=DEBUG  # Use INFO for production

# Rate Limiting
MAX_TRANSACTIONS_PER_DAY=100
MAX_COMMANDS_PER_MINUTE=60

# Admin User (Your Telegram ID for initial setup)
ADMIN_TELEGRAM_ID=YOUR_TELEGRAM_USER_ID
```

**How to get your Telegram User ID**:

1. Message @userinfobot on Telegram
2. Send `/start`
3. Copy your user ID

### 3.3 Verify Configuration

```bash
# Test database connection
python -c "from src.database.connection import create_engine; print('DB Connected!' if create_engine() else 'Failed')"

# Test environment loading
python -c "from src.config.settings import Settings; s = Settings(); print(f'Bot Token: {s.telegram_bot_token[:10]}...')"
```

---

## Step 4: Run Tests (10 minutes)

### 4.1 Run Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term

# Expected output:
# ==================== test session starts ====================
# collected 45 items
#
# tests/unit/test_validators.py ........
# tests/unit/test_formatters.py .......
# tests/integration/test_database.py .....
#
# ==================== 45 passed in 2.34s ====================
#
# Coverage: 82%
```

### 4.2 Run Specific Test Suites

```bash
# Unit tests only
pytest tests/unit/

# Integration tests (requires running PostgreSQL)
pytest tests/integration/

# E2E tests (requires bot token)
pytest tests/e2e/ -v
```

### 4.3 Check Code Quality

```bash
# Linting
pylint src/

# Code formatting check
black --check src/

# Type checking
mypy src/
```

**Fix formatting issues**:

```bash
black src/  # Auto-format code
```

---

## Step 5: Run Bot Locally (5 minutes)

### 5.1 Bootstrap Admin User

```bash
# Register yourself as admin (one-time)
python scripts/bootstrap_admin.py --telegram-id YOUR_TELEGRAM_ID

# Verify
psql -h localhost -U dev -d cashflow_dev \
  -c "SELECT telegram_id, status, role FROM users;"
```

**Expected output**:

```
 telegram_id | status   | role
-------------+----------+-------
 123456789   | approved | admin
```

### 5.2 Start Bot

```bash
# Terminal 1: Start bot
python -m src.main

# Expected output:
# INFO: Bot started successfully
# INFO: Polling for updates...
# INFO: Connected to database: cashflow_dev
# INFO: Scheduler started (WITA timezone)
```

### 5.3 Test Bot Interaction

Open Telegram and message your bot:

```
You: /start

Bot: 👋 Welcome to Cash Flow Manager!
     [Shows main menu keyboard]

You: /income 500000 Test payment

Bot: 💰 Income Recorded
     Amount: Rp 500,000
     Category: Income
     Description: Test payment
     Date: 18 Dec 2025 14:30 WITA
     ID: TX20251218001
     ✅ Transaction saved successfully

You: /summary

Bot: 📊 Daily Financial Summary
     Date: 18 Dec 2025
     ...
```

---

## Step 6: Development Workflow (Reference)

### 6.1 Create New Feature Branch

```bash
git checkout -b feature/add-export-function
```

### 6.2 TDD Workflow Example

```bash
# 1. Write failing test
cat > tests/unit/services/test_export.py << 'EOF'
import pytest
from src.bot.services.export_service import ExportService

def test_export_to_csv():
    """Test CSV export functionality"""
    service = ExportService()
    result = service.export_transactions(format='csv')
    assert result.endswith('.csv')
    assert len(result) > 0
EOF

# 2. Run test (should fail)
pytest tests/unit/services/test_export.py -v
# FAILED - ModuleNotFoundError: No module named 'src.bot.services.export_service'

# 3. Implement minimal code
mkdir -p src/bot/services
cat > src/bot/services/export_service.py << 'EOF'
class ExportService:
    def export_transactions(self, format='csv'):
        return "transactions.csv"
EOF

# 4. Run test (should pass)
pytest tests/unit/services/test_export.py -v
# PASSED

# 5. Refactor while tests pass
# (improve implementation, add error handling, etc.)
```

### 6.3 Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add export_logs table"

# Review generated migration
cat migrations/versions/002_add_export_logs.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

### 6.4 Running Bot with Hot Reload

```bash
# Install watchdog
pip install watchdog

# Run with auto-reload on file changes
watchmedo auto-restart --patterns="*.py" --recursive -- python -m src.main
```

---

## Test Scenarios

### Scenario 1: Record Income Flow

**Goal**: Test complete income recording workflow

**Steps**:

1. Send `/income 500000 Client payment`
2. Verify confirmation message
3. Send `/summary`
4. Verify income appears in summary

**Expected Database State**:

```sql
SELECT transaction_id, amount, description FROM transactions WHERE type = 'income';
-- TX20251218001 | 500000.00 | Client payment
```

### Scenario 2: Expense with Category

**Goal**: Test expense recording with category selection

**Steps**:

1. Send `/expense 250000 Office rent`
2. Click "🏢 Operational" button
3. Verify confirmation
4. Send `/summary`
5. Verify expense appears under Operational

**Expected Database State**:

```sql
SELECT t.transaction_id, t.amount, c.name
FROM transactions t
JOIN categories c ON t.category_id = c.category_id
WHERE t.type = 'expense';
-- TX20251218002 | 250000.00 | Operational
```

### Scenario 3: Interactive Input Flow

**Goal**: Test sequential prompt conversation

**Steps**:

1. Send `/income` (no arguments)
2. Bot: "Enter amount:"
3. Reply: `500000`
4. Bot: "Enter description:"
5. Reply: `Test income`
6. Verify confirmation

**Conversation State Tracking**:

```python
# ConversationHandler states:
# WAITING_AMOUNT → WAITING_DESCRIPTION → END
```

### Scenario 4: Duplicate Detection

**Goal**: Test duplicate transaction warning

**Steps**:

1. Send `/income 500000 Test`
2. Wait 10 seconds
3. Send `/income 500000 Test` (identical)
4. Bot: "⚠️ Possible Duplicate Transaction"
5. Click "✅ Yes, Confirm"
6. Verify both transactions saved

**Database Verification**:

```sql
SELECT COUNT(*) FROM transactions WHERE amount = 500000 AND description = 'Test';
-- Should be 2
```

### Scenario 5: Daily Report Generation

**Goal**: Test automated 24:00 WITA report

**Steps**:

1. Record some transactions during the day
2. Set system time to 23:59:50 WITA (for testing)
3. Wait for 24:00:00
4. Verify report sent to management chat
5. Check `daily_summaries` table for generated summary

**Manual Trigger for Testing**:

```python
# Python console
from src.scheduler.daily_report import generate_daily_report
import asyncio

asyncio.run(generate_daily_report())
```

---

## Troubleshooting

### Issue: Bot doesn't respond to commands

**Check**:

```bash
# 1. Verify bot is running
ps aux | grep "python -m src.main"

# 2. Check logs
tail -f logs/bot.log

# 3. Test bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

**Solution**:

- Verify `TELEGRAM_BOT_TOKEN` in `.env`
- Check network connectivity
- Ensure bot isn't blocked by firewall

### Issue: Database connection errors

**Check**:

```bash
# 1. PostgreSQL running?
docker ps | grep postgres

# 2. Can connect manually?
psql -h localhost -U dev -d cashflow_dev

# 3. Check connection string
echo $DATABASE_URL
```

**Solution**:

```bash
# Restart PostgreSQL
docker-compose restart postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

### Issue: Tests failing

**Check**:

```bash
# Run with verbose output
pytest -vv -s

# Run specific failing test
pytest tests/unit/test_validators.py::test_amount_validation -vv
```

**Common Causes**:

- Missing test dependencies: `pip install -r requirements-dev.txt`
- Database not running: `docker-compose up -d postgres`
- Environment variables not set: `source .env` or `export $(cat .env | xargs)`

### Issue: Timezone incorrect

**Check**:

```bash
# Verify timezone setting
python -c "from src.config.settings import Settings; print(Settings().timezone)"

# Check system timezone
timedatectl  # Linux
date  # Any OS
```

**Solution**:

```bash
# Set TIMEZONE in .env
TIMEZONE=Asia/Makassar

# Verify WITA offset
python -c "import pytz; tz = pytz.timezone('Asia/Makassar'); print(tz)"
```

---

## Development Tools Reference

### Useful Commands

```bash
# Database
docker-compose exec postgres psql -U dev -d cashflow_dev  # DB console
alembic history  # Migration history
alembic current  # Current migration version

# Testing
pytest -k "test_income"  # Run tests matching pattern
pytest --lf  # Re-run last failed tests
pytest --pdb  # Drop into debugger on failure

# Code Quality
pylint src/bot/handlers/  # Lint specific directory
black src/ --diff  # Preview formatting changes
mypy src/ --show-error-codes  # Type checking with error codes

# Git
git log --oneline --graph  # Visual commit history
git diff HEAD~1 src/  # Show changes since last commit
```

### VS Code Settings

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

### Debug Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Bot",
      "type": "python",
      "request": "launch",
      "module": "src.main",
      "console": "integratedTerminal",
      "envFile": "${workspaceFolder}/.env"
    },
    {
      "name": "Python: Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v"],
      "console": "integratedTerminal"
    }
  ]
}
```

---

## Test Scenarios Validation

This section provides validation procedures for all critical user workflows. Run these scenarios to verify bot functionality before deploying to production.

### Prerequisites for Testing

1. **Bot is running** (either via `python -m src.main` or `docker-compose up`)
2. **Database is populated** with seed data (`scripts/seed_dev_data.py`)
3. **Your Telegram account** is registered and approved
4. **Test environment variables** are configured in `.env`

### Validation Checklist

Use this checklist to track test scenario completion:

- [ ] Scenario 1: Income Recording Flow
- [ ] Scenario 2: Expense Recording with Category
- [ ] Scenario 3: Interactive Input Flow
- [ ] Scenario 4: Duplicate Detection Warning
- [ ] Scenario 5: Daily Summary Generation
- [ ] Scenario 6: Transaction History Pagination
- [ ] Scenario 7: WITA Timezone Edge Cases
- [ ] Scenario 8: Error Handling and Validation
- [ ] Scenario 9: User Registration Workflow
- [ ] Scenario 10: Automated Report Delivery

---

### Scenario 1: Record Income Flow

**Goal**: Test complete income recording workflow

**Steps**:

1. Send `/income 500000 Client payment`
2. Verify confirmation message displays:
   - Transaction ID (format: TX20251223001)
   - Amount formatted with Rp prefix (Rp 500.000)
   - Description
   - Timestamp in WITA
3. Send `/summary`
4. Verify income appears in today's summary

**Expected Telegram Response**:

```
✅ Income Recorded Successfully

Transaction ID: TX20251223001
Amount: Rp 500.000
Category: Income
Description: Client payment
Date: 2025-12-23 14:30:00 WITA

Your balance has been updated.
```

**Database Verification**:

```sql
SELECT transaction_id, amount, description, type
FROM transactions
WHERE type = 'income'
ORDER BY timestamp DESC
LIMIT 1;

-- Expected:
-- TX20251223001 | 500000.00 | Client payment | income
```

**Success Criteria**:

- ✅ Transaction ID generated correctly
- ✅ Amount formatted with thousand separators
- ✅ Timestamp shows WITA timezone
- ✅ Transaction appears in database
- ✅ Transaction appears in `/summary`

---

### Scenario 2: Expense with Category

**Goal**: Test expense recording with category selection

**Steps**:

1. Send `/expense 250000 Office rent`
2. Bot displays category selection keyboard with buttons:
   - 🏢 Operational
   - 👥 Salaries
   - 📦 Supplies
   - 📢 Marketing
   - ❓ Other
3. Click "🏢 Operational" button
4. Verify confirmation message
5. Send `/summary`
6. Verify expense appears under Operational category

**Expected Telegram Response (after button click)**:

```
✅ Expense Recorded Successfully

Transaction ID: TX20251223002
Amount: Rp 250.000
Category: Operational
Description: Office rent
Date: 2025-12-23 14:35:00 WITA

Your balance has been updated.
```

**Database Verification**:

```sql
SELECT t.transaction_id, t.amount, c.name as category
FROM transactions t
JOIN categories c ON t.category_id = c.category_id
WHERE t.type = 'expense'
ORDER BY t.timestamp DESC
LIMIT 1;

-- Expected:
-- TX20251223002 | 250000.00 | Operational
```

**Success Criteria**:

- ✅ Category keyboard displays correctly
- ✅ Selected category saved to database
- ✅ Category appears in confirmation
- ✅ Category breakdown correct in `/summary`

---

### Scenario 3: Interactive Input Flow

**Goal**: Test sequential prompt conversation for transaction entry

**Steps**:

1. Send `/income` (no arguments)
2. Bot replies: "💰 Enter the income amount:"
3. Reply: `500000`
4. Bot replies: "📝 Enter a description (optional, send /skip to skip):"
5. Reply: `Test income`
6. Verify confirmation message

**Expected Conversation Flow**:

```
You: /income

Bot: 💰 Enter the income amount:
(Please enter a number without currency symbols)

You: 500000

Bot: ✅ Amount confirmed: Rp 500.000

📝 Enter a description (optional, send /skip to skip):

You: Test income

Bot: ✅ Income Recorded Successfully
[... full confirmation message ...]
```

**ConversationHandler State Tracking**:

```python
# Expected state transitions:
# WAITING_AMOUNT → WAITING_DESCRIPTION → END
```

**Success Criteria**:

- ✅ Bot guides user through each step
- ✅ Amount validation works (rejects invalid input)
- ✅ Description is optional (/skip works)
- ✅ Transaction saved after all inputs provided

---

### Scenario 4: Duplicate Detection

**Goal**: Test duplicate transaction warning system

**Steps**:

1. Send `/income 500000 Test transaction`
2. Wait for confirmation
3. Wait 10 seconds (within duplicate detection window)
4. Send `/income 500000 Test transaction` (identical)
5. Bot displays duplicate warning with buttons:
   - ✅ Yes, Confirm
   - ❌ No, Cancel
6. Click "✅ Yes, Confirm"
7. Verify both transactions are saved

**Expected Warning Message**:

```
⚠️ Possible Duplicate Transaction

A similar transaction was recorded 15 seconds ago:

Previous Transaction:
• Amount: Rp 500.000
• Description: Test transaction
• Time: 14:45:00 WITA

Do you want to record this transaction anyway?
```

**Database Verification**:

```sql
SELECT COUNT(*) as count
FROM transactions
WHERE amount = 500000
  AND description = 'Test transaction'
  AND timestamp > NOW() - INTERVAL '5 minutes';

-- Expected: 2 (both transactions saved)
```

**Success Criteria**:

- ✅ Duplicate detection triggers within time window
- ✅ User can confirm or cancel duplicate
- ✅ Both transactions saved if confirmed
- ✅ No transaction saved if cancelled

---

### Scenario 5: Daily Report Generation

**Goal**: Test automated 24:00 WITA daily report

**Manual Test Method** (without waiting until midnight):

```bash
# Run manual report generation
docker-compose exec bot python -c "
from src.scheduler.daily_report import generate_daily_report
import asyncio
asyncio.run(generate_daily_report())
"
```

**Steps**:

1. Record various transactions during the day (mix of income/expenses)
2. Trigger manual report generation (command above)
3. Check management chat for report message
4. Verify `daily_summaries` table has new entry

**Expected Report Message** (sent to MANAGEMENT_CHAT_ID):

```
📊 Daily Financial Report
Date: 2025-12-23

💰 Total Income: Rp 1.500.000
💸 Total Expenses: Rp 850.000
💵 Net Cash Flow: Rp 650.000

📈 Expense Breakdown:
• Operational: Rp 400.000 (47%)
• Salaries: Rp 300.000 (35%)
• Supplies: Rp 100.000 (12%)
• Marketing: Rp 50.000 (6%)

📝 Transaction Count: 15 transactions

Previous Day Comparison:
↗️ Net flow increased by Rp 100.000 (+18%)
```

**Database Verification**:

```sql
SELECT summary_date, total_income, total_expenses, net_cash_flow, transaction_count
FROM daily_summaries
WHERE summary_date = CURRENT_DATE
ORDER BY created_at DESC
LIMIT 1;

-- Verify values match report message
```

**Automated Test** (for 24:00 WITA trigger):

```bash
# Set system time to 23:59:50 WITA for testing
# NOTE: Requires root access, run in isolated test environment
sudo timedatectl set-time "23:59:50"
# Wait 10 seconds for scheduler to trigger
# Verify report is sent
```

**Success Criteria**:

- ✅ Report generated at exactly 24:00 WITA
- ✅ All transactions from day included
- ✅ Category breakdown accurate
- ✅ Percentage calculations correct
- ✅ Previous day comparison shown
- ✅ Report saved to `daily_summaries` table

---

### Scenario 6: Transaction History Pagination

**Goal**: Test transaction history retrieval with pagination

**Steps**:

1. Ensure database has 20+ transactions
2. Send `/history`
3. Bot displays first page (10 transactions)
4. Click "Next ▶️" button
5. Verify page 2 displays next 10 transactions
6. Click "◀️ Previous" button
7. Verify returns to page 1

**Expected Response (Page 1)**:

```
📜 Transaction History
Page 1 of 3

2025-12-23 14:30:00 WITA
💰 Income - Rp 500.000
Client payment
ID: TX20251223001

2025-12-23 14:25:00 WITA
💸 Operational - Rp 250.000
Office rent
ID: TX20251223002

[... 8 more transactions ...]

Showing 1-10 of 25 transactions
```

**Success Criteria**:

- ✅ Pagination shows 10 transactions per page
- ✅ Navigation buttons work correctly
- ✅ Page numbers accurate
- ✅ Transactions sorted by timestamp (newest first)
- ✅ All transaction details displayed correctly

---

### Scenario 7: WITA Timezone Edge Cases

**Goal**: Test timezone handling at day boundaries

**Edge Case 1: Transaction at 23:59:59 WITA**

```bash
# Set time to 23:59:55 WITA
sudo timedatectl set-time "23:59:55"

# Record transaction
# Send: /income 100000 End of day test

# Verify transaction date is CURRENT day (not next day)
```

**Edge Case 2: Daily Report at 00:00:00 WITA**

```bash
# Report should only include transactions from PREVIOUS day
# Transaction at 23:59:59 should be in today's report
# Transaction at 00:00:01 should be in tomorrow's report
```

**Database Verification**:

```sql
-- Check transaction date conversion
SELECT
    transaction_id,
    timestamp AT TIME ZONE 'UTC' as utc_time,
    timestamp AT TIME ZONE 'Asia/Makassar' as wita_time,
    DATE(timestamp AT TIME ZONE 'Asia/Makassar') as wita_date
FROM transactions
WHERE description LIKE '%End of day test%';

-- Verify WITA date matches expected day
```

**Success Criteria**:

- ✅ Transactions recorded with correct WITA date
- ✅ Daily reports use WITA date boundaries
- ✅ No off-by-one errors at midnight
- ✅ UTC ↔ WITA conversion accurate

---

### Scenario 8: Error Handling and Validation

**Goal**: Test input validation and error messages

**Test Cases**:

1. **Invalid amount format:**

   ```
   /income abc123

   Expected: ❌ Invalid amount. Please enter a valid number.
   Example: /income 500000 Client payment
   ```

2. **Negative amount:**

   ```
   /income -500000

   Expected: ❌ Amount must be positive.
   ```

3. **Amount exceeds maximum (10 billion):**

   ```
   /income 15000000000

   Expected: ❌ Amount exceeds maximum allowed value (Rp 10.000.000.000)
   ```

4. **Missing required parameters:**

   ```
   /expense

   Expected: Bot starts interactive flow (not error)
   ```

5. **Database connection error:**

   ```
   # Stop database
   docker-compose stop postgres

   # Try to record transaction
   /income 100000 Test

   Expected: ❌ System error. Please try again later.
   (Error logged, management notified if critical)
   ```

**Success Criteria**:

- ✅ All validation errors show user-friendly messages
- ✅ Error messages include examples
- ✅ System errors don't expose technical details
- ✅ Critical errors trigger management alerts

---

### Scenario 9: User Registration Workflow

**Goal**: Test new user registration and approval process

**Steps**:

1. **New user** sends `/register EMP12345` (from unregistered Telegram account)
2. Bot responds with pending approval message
3. **Admin** receives notification in management chat
4. Admin reviews user details
5. Admin sends `/approve <user_id>` or `/reject <user_id>`
6. New user receives approval/rejection notification
7. If approved, user can now use bot commands

**Expected Messages**:

**New User (after `/register EMP12345`)**:

```
✅ Registration Request Submitted

Your request has been sent to administrators.
Employee ID: EMP12345

You will receive a notification once your request is reviewed.
Please wait for approval before using the bot.
```

**Admin Notification**:

```
🔔 New Registration Request

User: John Doe (@johndoe)
Telegram ID: 123456789
Employee ID: EMP12345
Request Time: 2025-12-23 15:00:00 WITA

Actions:
[Approve] [Reject]
```

**After Approval**:

```
🎉 Registration Approved

Your access has been approved!
You can now use the Cash Flow Bot.

Available commands:
/income - Record income
/expense - Record expense
/summary - View daily summary
/history - View transaction history
```

**Success Criteria**:

- ✅ Unregistered users can only use `/register`
- ✅ Admin receives notification with user details
- ✅ Approval/rejection updates user status
- ✅ Approved users can access all commands
- ✅ Rejected users remain blocked

---

### Scenario 10: Automated Report Delivery

**Goal**: Test scheduled report delivery to management

**Test Method** (manual trigger):

```bash
# Method 1: Python console
docker-compose exec bot python << EOF
from src.scheduler.daily_report import generate_daily_report
import asyncio
asyncio.run(generate_daily_report())
EOF

# Method 2: Direct script execution
docker-compose exec bot python -m src.scheduler.daily_report
```

**Verification Steps**:

1. Trigger report generation (manual or wait for 24:00 WITA)
2. Check management chat for report
3. Verify report contains all required sections
4. Check `daily_summaries` table for saved data
5. Verify notification sent even if no transactions

**Expected Report (No Transactions)**:

```
📊 Daily Financial Report
Date: 2025-12-23

💰 Total Income: Rp 0
💸 Total Expenses: Rp 0
💵 Net Cash Flow: Rp 0

📝 Transaction Count: 0 transactions

ℹ️ No transactions recorded today.
```

**Success Criteria**:

- ✅ Report sent at exactly 24:00 WITA
- ✅ Report sent even with zero transactions
- ✅ All calculations accurate
- ✅ Report persisted to database
- ✅ Errors trigger management alert

---

## Validation Automation

### Automated Test Suite

Run the complete validation suite with pytest:

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run specific scenario
pytest tests/e2e/test_user_workflows.py::test_income_recording_flow -v

# Run with coverage
pytest tests/e2e/ --cov=src --cov-report=term-missing
```

### Integration Test Coverage

```bash
# Database operations
pytest tests/integration/test_database.py -v

# Telegram API interactions
pytest tests/integration/test_telegram_api.py -v

# Scheduler jobs
pytest tests/integration/test_scheduler.py -v

# Timezone handling
pytest tests/integration/test_timezone_edge_cases.py -v
```

### Manual Validation Script

Create a validation script that runs all scenarios:

```bash
#!/bin/bash
# scripts/validate_scenarios.sh

echo "Running test scenario validation..."

# Scenario 1: Income recording
echo "Test 1: Income recording..."
# Add test commands here

# Scenario 2: Expense recording
echo "Test 2: Expense recording..."
# Add test commands here

# ... continue for all scenarios

echo "Validation complete!"
```

---

## Troubleshooting Test Scenarios

### Issue: Bot doesn't respond to test commands

**Diagnosis:**

```bash
# Check bot is running
ps aux | grep "python -m src.main"

# Check logs for errors
tail -f logs/bot.log

# Verify bot token
curl https://api.telegram.org/bot<YOUR_TOKEN>/getMe
```

**Solutions:**

- Restart bot: `docker-compose restart bot`
- Check `.env` file has correct `TELEGRAM_BOT_TOKEN`
- Verify network connectivity to api.telegram.org

### Issue: Timezone calculations incorrect

**Diagnosis:**

```bash
# Check system timezone
timedatectl

# Check PostgreSQL timezone
docker-compose exec db psql -U cashflow_bot -c "SHOW timezone;"

# Verify WITA timezone in code
docker-compose exec bot python -c "
from src.bot.utils.timezone import now_wita
print(now_wita())
"
```

**Solutions:**

- Set system timezone: `sudo timedatectl set-timezone Asia/Makassar`
- Verify `pytz` installed: `pip list | grep pytz`
- Check timezone conversion functions in `src/bot/utils/timezone.py`

### Issue: Database verification queries fail

**Diagnosis:**

```bash
# Check database connectivity
docker-compose exec db psql -U cashflow_bot -d cashflow_bot -c "SELECT 1;"

# Check table exists
docker-compose exec db psql -U cashflow_bot -d cashflow_bot -c "\dt"

# Check migrations applied
docker-compose exec bot alembic current
```

**Solutions:**

- Run migrations: `docker-compose exec bot alembic upgrade head`
- Restart database: `docker-compose restart db`
- Check database URL in `.env`

---

## Test Data Reset

To reset test data between validation runs:

```bash
# Method 1: Drop and recreate database
docker-compose exec db psql -U cashflow_bot -c "DROP DATABASE cashflow_bot;"
docker-compose exec db psql -U cashflow_bot -c "CREATE DATABASE cashflow_bot;"
docker-compose exec bot alembic upgrade head
python scripts/seed_dev_data.py

# Method 2: Delete test transactions
docker-compose exec db psql -U cashflow_bot -d cashflow_bot << EOF
DELETE FROM daily_summaries;
DELETE FROM transactions;
ALTER SEQUENCE transactions_transaction_id_seq RESTART WITH 1;
EOF

# Method 3: Testcontainers (automated in integration tests)
pytest tests/integration/ --use-testcontainers
```

---

## Validation Sign-Off

After completing all test scenarios, sign off on validation:

```markdown
## Validation Sign-Off

- Date: _________________
- Tester: _________________
- Environment: [ ] Local [ ] Staging [ ] Production
- Bot Version: _________________

### Scenario Results

- [x] Scenario 1: Income Recording Flow - PASS
- [x] Scenario 2: Expense Recording with Category - PASS
- [x] Scenario 3: Interactive Input Flow - PASS
- [x] Scenario 4: Duplicate Detection - PASS
- [x] Scenario 5: Daily Report Generation - PASS
- [x] Scenario 6: Transaction History - PASS
- [x] Scenario 7: Timezone Edge Cases - PASS
- [x] Scenario 8: Error Handling - PASS
- [x] Scenario 9: User Registration - PASS
- [x] Scenario 10: Automated Reports - PASS

### Overall Assessment

- [ ] All scenarios pass
- [ ] Ready for production deployment
- [ ] Issues found (document below)

### Issues Found

(List any issues discovered during validation)

### Recommendations

(Any recommendations before production deployment)

Signed: _________________
```

---

## Next Steps

**After completing quickstart**:

1. ✅ **Review Architecture**: Read [plan.md](plan.md) for system design
2. ✅ **Understand Data Model**: Study [data-model.md](data-model.md) for database schema
3. ✅ **Read Contracts**: Review [contracts/commands.yaml](contracts/commands.yaml) for command specifications
4. ✅ **Validate Scenarios**: Complete all test scenarios above
5. **Start Development**: Pick a task from `tasks.md` (generated via `/speckit.tasks`)
6. **Follow TDD**: Red → Green → Refactor workflow per Constitution Principle II

**Resources**:

- [python-telegram-bot docs](https://docs.python-telegram-bot.org/)
- [SQLAlchemy 2.0 tutorial](https://docs.sqlalchemy.org/en/20/tutorial/)
- [PostgreSQL documentation](https://www.postgresql.org/docs/15/)
- [pytest documentation](https://docs.pytest.org/)

---

## Quick Reference

### Environment Ports

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | `localhost:5432` |
| Prometheus (future) | 9090 | `http://localhost:9090` |
| Grafana (future) | 3000 | `http://localhost:3000` |

### Log Locations

```
logs/
├── bot.log          # Main application log
├── database.log     # Database queries (DEBUG mode)
├── scheduler.log    # APScheduler jobs
└── error.log        # Critical errors only
```

### Test Data Defaults

After running `seed_dev_data.py`:

| Entity | Count | Details |
|--------|-------|---------|
| Admin Users | 1 | Your Telegram ID (approved) |
| Categories | 6 | Income + 5 expense categories |
| Sample Transactions | 20 | Mixed income/expenses for testing |
| Daily Summaries | 7 | Last 7 days of data |

---

**Setup Time**: ~45-60 minutes  
**Status**: ✅ Ready for development  
**Next Command**: `pytest` to verify everything works

Happy coding! 🚀
