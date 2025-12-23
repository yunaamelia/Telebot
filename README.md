# Telegram Cash Flow Management Bot

Real-time cash flow tracking bot for company financial management. Record transactions, generate automated daily
reports, and maintain complete audit trails through Telegram.

## Features

- 💰 **Transaction Recording**: Quick income/expense entry via commands or interactive keyboards
- 📊 **Automated Reports**: Daily financial summaries delivered at 24:00 WITA
- 🔍 **Transaction History**: Paginated history with date/category filters
- 👥 **User Management**: Registration workflow with admin approval
- 🔒 **Security**: Role-based access, audit logging, whitelist-based authentication
- ⏰ **Timezone Support**: WITA (Asia/Makassar, UTC+8) native operation

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Docker & Docker Compose (optional, recommended)

### Local Development Setup

1. **Clone and navigate to project**:

   ```bash
   cd cashflow-bot
   ```

2. **Create virtual environment**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Configure environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your Telegram bot token and database credentials
   ```

5. **Start database** (Docker):

   ```bash
   docker-compose up -d postgres
   ```

6. **Run migrations**:

   ```bash
   alembic upgrade head
   ```

7. **Install Git hooks** (recommended):

   ```bash
   make install-hooks
   ```

8. **Start bot**:

   ```bash
   python -m src.main
   ```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f bot

# Stop services
docker-compose down
```

## Development

### Git Hooks & Quality Checks

This project uses pre-commit hooks for automatic code quality checks. See
[docs/HOOKS_QUICKSTART.md](docs/HOOKS_QUICKSTART.md) for complete guide.

```bash
# Install hooks (one-time setup)
make install-hooks

# Hooks run automatically on:
# - git commit (format, lint, security)
# - git push (tests, coverage)
# - commit message (conventional commits)

# Manual execution
pre-commit run --all-files
make lint
make format
make preflight  # Pre-deployment checks
```

**Quality Standards:**

- ✅ Code formatting (Black, isort)
- ✅ Linting (Flake8 + plugins)
- ✅ Security scanning (Bandit, detect-secrets)
- ✅ Test coverage ≥80%
- ✅ Type checking (mypy)
- ✅ Conventional commits

### Running Tests

```bash
# All tests with coverage
pytest

# Unit tests only
pytest -m unit

# Integration tests (requires database)
pytest -m integration

# E2E tests
pytest -m e2e

# Coverage report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### Code Quality

```bash
# Lint
pylint src/

# Format
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

## Architecture

```
┌─────────────────────────────────────────────┐
│            Telegram Bot API                  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│               Handlers Layer                 │
│  (Commands, Callbacks, Message Processing)  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│              Services Layer                  │
│   (Business Logic, Validation, Formatting)  │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│            Repositories Layer                │
│         (Data Access, Queries)              │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│            PostgreSQL Database               │
│  (Transactions, Users, Categories, Reports) │
└─────────────────────────────────────────────┘
```

## Configuration

See [.env.example](.env.example) for all available environment variables:

- `TELEGRAM_BOT_TOKEN`: Bot API token from @BotFather
- `MANAGEMENT_CHAT_ID`: Chat ID for automated reports
- `DATABASE_URL`: PostgreSQL connection string
- `TIMEZONE`: Default timezone (Asia/Makassar)
- `LOG_LEVEL`: Logging verbosity (INFO, DEBUG, WARNING)

## Commands

### User Commands

- `/start` - Initialize bot and show main menu
- `/income <amount> [description]` - Record income transaction
- `/expense <amount> <category> [description]` - Record expense transaction
- `/summary` - Get today's financial summary
- `/history [YYYY-MM-DD]` - View transaction history
- `/register <employee_id>` - Request bot access

### Admin Commands

- `/approve <user_id>` - Approve registration request
- `/reject <user_id>` - Reject registration request
- `/report [YYYY-MM-DD]` - Generate manual report for specific date

## Project Structure

See [plan.md](../specs/001-cashflow-bot/plan.md) for detailed architecture documentation.

## Testing Strategy

- **Unit Tests**: Services, utilities, validators (≥80% coverage)
- **Integration Tests**: Database operations, API integrations
- **E2E Tests**: Complete user workflows from command to confirmation
- **Financial Tests**: 100% coverage requirement for calculations

## Deployment

### Pre-deployment Checks

```bash
# Run comprehensive pre-flight checks
./scripts/preflight.sh

# Or using Make
make preflight
```

This validates:

- Environment configuration
- Database migrations
- Test suite passes
- Code quality standards
- Security vulnerabilities
- Docker build success

### Production Checklist

- [ ] Run `make preflight` successfully
- [ ] Set strong `POSTGRES_PASSWORD` in production
- [ ] Configure `TELEGRAM_BOT_TOKEN` from environment
- [ ] Enable SSL for database connections
- [ ] Set `LOG_LEVEL=WARNING` for production
- [ ] Configure backup strategy for PostgreSQL
- [ ] Set up monitoring and alerting
- [ ] Review `.env` file for secure secret management
- [ ] Verify Git hooks are installed (`make install-hooks`)

### Systemd Service (Linux)

```ini
[Unit]
Description=Telegram Cash Flow Bot
After=network.target postgresql.service

[Service]
Type=simple
User=botuser
WorkingDirectory=/opt/cashflow-bot
EnvironmentFile=/opt/cashflow-bot/.env
ExecStart=/opt/cashflow-bot/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Contributing

1. Create feature branch from `main`
2. Write tests first (TDD approach)
3. Implement feature
4. Ensure tests pass and coverage ≥80%
5. Run linters and formatters
6. Submit pull request

## License

Internal company project - All rights reserved

## Support

For issues or questions, contact the development team or create an issue in the repository.
