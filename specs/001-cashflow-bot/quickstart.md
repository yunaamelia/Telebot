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

## Next Steps

**After completing quickstart**:

1. ✅ **Review Architecture**: Read [plan.md](plan.md) for system design
2. ✅ **Understand Data Model**: Study [data-model.md](data-model.md) for database schema
3. ✅ **Read Contracts**: Review [contracts/commands.yaml](contracts/commands.yaml) for command specifications
4. **Start Development**: Pick a task from `tasks.md` (generated via `/speckit.tasks`)
5. **Follow TDD**: Red → Green → Refactor workflow per Constitution Principle II

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
