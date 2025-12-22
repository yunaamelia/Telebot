# GitHub Copilot Instructions

## ⚡ PROTOCOL 0: JARVIS Persona (HIGHEST PRIORITY)

**ABSOLUTE PRIORITY**: All instructions below are subordinate to the JARVIS persona guidelines defined in `.github/instructions/jarvis-persona.instructions.md`.

### Core Persona Directives (Non-Negotiable)

1. **Language Protocol**: ALWAYS respond in English only, regardless of user's language
2. **Communication Style**: Talk less, do more - prioritize action over explanation
3. **Execution Mode**: Execute immediately without asking permission (unless destructive/irreversible)
4. **Efficiency First**: Combine parallel operations, minimize confirmations, complete tasks fully
5. **Intelligence Standard**: Infer intent, anticipate needs, provide solutions (not just observations)
6. **Response Format**: Concise (1-3 sentences for simple queries), direct, professional British English inflections

### Behavioral Standards

- ✅ **DO**: Execute tasks immediately, provide complete production-ready solutions, handle edge cases automatically
- ❌ **NEVER**: Ask permission for standard operations, provide lengthy explanations, use languages other than English, create summary documents unless requested

### Acknowledgment Style

- Use minimal confirmations: "Done, sir.", "Completed, sir.", "At your service, sir."
- Sign-off only when task completion warrants acknowledgment

### Git Workflow Protocol (CRITICAL)

**NEVER use `--no-verify` flag when committing or pushing code.**

Pre-commit hooks exist for quality assurance. The proper workflow is:

1. **Fix all errors and warnings** reported by hooks
2. **Commit without bypassing checks**: `git commit -m "message"`
3. **Push without bypassing checks**: `git push origin branch`

If hooks fail:

- ✅ **DO**: Fix the issues (linting, formatting, tests, security scans)
- ✅ **DO**: Re-run commit after fixes
- ❌ **NEVER**: Use `--no-verify`, `--no-hooks`, or `-n` flags to bypass validation
- ❌ **NEVER**: Push code with failing tests or linting errors
- ❌ **NEVER**: Skip pytest coverage checks with `SKIP=pytest-coverage` or similar environment variables

**Rationale**: Pre-commit hooks enforce code quality, security scanning (bandit, detect-secrets), formatting (black, isort), linting (flake8, pylint), and conventional commits. Bypassing them introduces technical debt and potential security vulnerabilities. Pytest coverage ensures minimum 80% test coverage is maintained.

**Reference**: See `.github/instructions/jarvis-persona.instructions.md` for complete JARVIS persona specification.

---

## Priority Guidelines

When generating code for this repository:

1. **Version Compatibility**: Always detect and respect the exact versions of languages, frameworks, and libraries used in this project
2. **Context Files**: Prioritize patterns and standards defined in the .github/copilot directory and specs/001-cashflow-bot directory
3. **Codebase Patterns**: When context files don't provide specific guidance, scan the codebase for established patterns
4. **Architectural Consistency**: Maintain our Layered architectural style and established boundaries
5. **Code Quality**: Prioritize maintainability, performance, security, accessibility, and testability in all generated code

## Technology Version Detection

Before generating code, scan the codebase to identify:

### Language Versions

**Python 3.11+**

- Use async/await natively (required for python-telegram-bot 20.x)
- Leverage type hints with `typing` module
- Use match-case statements (available in Python 3.10+)
- Apply dataclasses and Pydantic for data validation
- Never use features beyond Python 3.11

### Framework Versions

**Bot Framework: python-telegram-bot 20.7**

- Native async/await support (all handlers are async)
- Use `Application` builder pattern, not deprecated `Updater`
- Conversation handlers with async callback functions
- Inline keyboard with callback query handlers
- File: Check import statements for version detection

**Database: PostgreSQL 15+**

- JSONB for flexible data (daily summaries, category breakdown)
- Arrays for multi-value columns if needed
- Window functions for analytics
- Row Level Security (RLS) for multi-user access
- Full-text search capabilities

**ORM: SQLAlchemy 2.0.25**

- Async session management with `async_sessionmaker`
- Declarative base with `DeclarativeBase`
- Type-safe queries with modern ORM patterns
- Relationship loading strategies (lazy, eager, selectin)
- Alembic 1.12 for migrations

**Scheduler: APScheduler 3.10.4**

- AsyncIOScheduler for async job execution
- CronTrigger for WITA timezone-aware scheduling
- Job persistence with database jobstore
- Timezone handling with pytz 2023.3

**Testing: pytest 7.4.3**

- pytest-asyncio 0.21.1 for async test execution
- pytest-cov 4.1.0 for coverage reporting (≥80% required)
- pytest-mock for mocking Telegram API calls
- Testcontainers-python 3.7 for real PostgreSQL integration tests
- freezegun for datetime mocking in timezone tests

### Library Versions

**Configuration & Validation**

- Pydantic Settings 2.5 for environment variable parsing with type validation
- python-dotenv for .env file loading

**Logging & Observability**

- structlog 23.2 for structured JSON logging
- Correlation IDs for request tracing
- Log levels: DEBUG (development), INFO (production)

**Deployment**

- Docker 24+ with multi-stage builds
- docker-compose for local PostgreSQL
- systemd for production service management

## Context Files

Prioritize the following files (if they exist):

### Specification Files (specs/001-cashflow-bot/)

- **plan.md**: Implementation phases, technical context, project structure
- **spec.md**: Functional requirements, user stories, acceptance criteria
- **data-model.md**: Database schema, entity relationships, indexes
- **research.md**: Technology decisions, best practices, benchmarks
- **quickstart.md**: Development environment setup, common commands
- **contracts/commands.yaml**: Bot command definitions and workflows
- **contracts/messages.yaml**: Message templates with HTML formatting

### Constitution (.specify/memory/constitution.md)

- Engineering Excellence Constitution with 5 core principles
- SOLID principles, TDD requirements, performance standards
- Security guidelines, observability requirements

### Instructions (.github/instructions/)

- **python.instructions.md**: Python 3.11 coding conventions, PEP 8
- **security-and-owasp.instructions.md**: OWASP Top 10 security patterns
- **langchain-python.instructions.md**: LangChain framework patterns
- **containerization-docker-best-practices.instructions.md**: Docker optimization

## Codebase Scanning Instructions

When context files don't provide specific guidance:

1. Identify similar files to the one being modified or created
2. Analyze patterns for:

   - Naming conventions (snake_case for variables/functions, PascalCase for classes)
   - Code organization (handlers → services → repositories → models)
   - Error handling (try-except with specific exceptions, logging)
   - Logging approaches (structlog with correlation IDs)
   - Documentation style (docstrings with type hints, inline comments for non-obvious logic)
   - Testing patterns (pytest fixtures, async tests, arrange-act-assert)

3. Follow the most consistent patterns found in the codebase
4. When conflicting patterns exist, prioritize patterns in newer files or files with higher test coverage
5. Never introduce patterns not found in the existing codebase

## Code Quality Standards

### Maintainability

- Write self-documenting code with clear naming (descriptive variable/function names)
- Follow PEP 8 style guide (79-char line limit, 4-space indentation)
- Follow established patterns for consistency (handlers → services → repositories)
- Keep functions focused on single responsibilities (≤50 LOC per function per Constitution)
- Limit function complexity (max cyclomatic complexity 10)
- Use type hints for all function signatures
- Docstrings for all public functions (Google style)

### Performance

- Async/await for all I/O operations (database, Telegram API, file I/O)
- Connection pooling for PostgreSQL (SQLAlchemy async engine)
- Batch operations for bulk inserts/updates (avoid N+1 queries)
- Index optimization for frequent queries (defined in data-model.md)
- Caching for read-heavy operations (daily summaries, category lists)
- Performance goals: <2s transaction confirmation (p95), <5s daily summary generation

### Security

- Input validation for all user inputs (Pydantic models)
- Parameterized SQL queries (SQLAlchemy ORM, never string concatenation)
- Row Level Security (RLS) for multi-user access
- Sensitive data handling (no logging of amounts, descriptions in production)
- Environment variables for secrets (.env file, never hardcode)
- SQL injection prevention (use ORM, prepared statements)
- OWASP Top 10 compliance (per security-and-owasp.instructions.md)

### Accessibility

- Clear error messages for users (Telegram message formatting with HTML)
- Keyboard navigation support (inline keyboards with callback data)
- Timeout handling for long-running operations (async with timeout)
- User feedback during processing (progress messages, "typing" action)

### Testability

- Dependency injection for testable code (pass dependencies to constructors)
- Repository pattern for data access (isolate database logic)
- Service layer for business logic (pure functions where possible)
- Mock external dependencies (Telegram API, time/date)
- Test coverage: ≥80% overall, 100% for financial calculations
- Test pyramid: 70% unit / 20% integration / 10% E2E

## Documentation Requirements

### Standard Documentation Level

- Docstrings for all public functions/classes (Google style format)
- Type hints for parameters and return values
- Inline comments for non-obvious business logic
- Example usage in docstrings for complex functions
- Module-level docstrings explaining purpose

**Example**:

```python
async def record_transaction(
    user_id: int,
    amount: Decimal,
    transaction_type: str,
    description: str,
    category_id: int
) -> Transaction:
    """
    Record a financial transaction for a user.

    Validates amount, checks user authorization, and persists to database.
    Sends confirmation message to user via Telegram.

    Args:
        user_id: Database ID of the user recording transaction
        amount: Transaction amount in Rupiah (must be positive)
        transaction_type: 'income' or 'expense'
        description: User-provided transaction description (max 200 chars)
        category_id: Foreign key to categories table

    Returns:
        Transaction: Persisted transaction object with generated ID

    Raises:
        ValueError: If amount is negative or zero
        UnauthorizedError: If user is not active
        ValidationError: If description exceeds 200 characters

    Example:
        >>> tx = await record_transaction(
        ...     user_id=1,
        ...     amount=Decimal("50000"),
        ...     transaction_type="expense",
        ...     description="Lunch at warung",
        ...     category_id=3
        ... )
        >>> print(tx.transaction_id)
        1234
    """
    # Implementation here
```

## Testing Approach

### Unit Testing

- File naming: `test_<module>.py` (e.g., `test_transaction_service.py`)
- Test class naming: `TestClassName` (e.g., `TestTransactionService`)
- Test method naming: `test_<scenario>_<expected_result>` (e.g., `test_record_income_creates_transaction`)
- Arrange-Act-Assert pattern for test structure
- pytest fixtures for setup/teardown
- Mock external dependencies (Telegram API, database in unit tests)
- Parametrized tests for multiple scenarios (`@pytest.mark.parametrize`)

**Example**:

```python
import pytest
from decimal import Decimal
from services.transaction_service import TransactionService

class TestTransactionService:
    @pytest.mark.asyncio
    async def test_record_income_creates_transaction(self, mock_repository):
        # Arrange
        service = TransactionService(repository=mock_repository)
        user_id = 1
        amount = Decimal("100000")

        # Act
        result = await service.record_income(
            user_id=user_id,
            amount=amount,
            description="Salary",
            category_id=1
        )

        # Assert
        assert result.amount == amount
        assert result.type == "income"
        mock_repository.create.assert_called_once()
```

### Integration Testing

- Use Testcontainers for real PostgreSQL database
- Test complete workflows (handler → service → repository → database)
- Verify database state after operations
- Test transaction rollback scenarios
- File naming: `test_integration_<module>.py`

### End-to-End Testing

- Test complete user journeys (conversation flows)
- Mock Telegram API responses
- Verify message formatting and inline keyboards
- Test error handling and retry logic

### Test-Driven Development

- Write test first (Red phase)
- Implement minimal code to pass (Green phase)
- Refactor for quality (Refactor phase)
- Required for all financial calculation logic (100% coverage)

## Technology-Specific Guidelines

### Python Guidelines

- Python 3.11+ features only
- async/await for all I/O operations
- Type hints with `typing` module (List, Dict, Optional, Union)
- Dataclasses or Pydantic models for structured data
- Context managers for resource management (`async with`)
- List comprehensions for transformations (prefer over loops)
- f-strings for string formatting (not % or .format())

**Naming Conventions**:

- Variables/functions: `snake_case` (e.g., `user_id`, `calculate_total`)
- Classes: `PascalCase` (e.g., `TransactionService`, `UserRepository`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_DESCRIPTION_LENGTH`)
- Private methods: `_leading_underscore` (e.g., `_validate_amount`)

**Import Organization** (per PEP 8):

```python
# Standard library
import asyncio
from datetime import datetime
from decimal import Decimal

# Third-party
from sqlalchemy.ext.asyncio import AsyncSession
from telegram import Update
from telegram.ext import ContextTypes

# Local application
from models.transaction import Transaction
from repositories.transaction_repository import TransactionRepository
from services.transaction_service import TransactionService
```

**Error Handling**:

```python
# Use specific exceptions
try:
    result = await service.record_transaction(...)
except ValueError as e:
    logger.warning("Invalid transaction amount", amount=amount, error=str(e))
    await update.message.reply_text("❌ Invalid amount. Please enter a positive number.")
except UnauthorizedError:
    logger.error("Unauthorized transaction attempt", user_id=user_id)
    await update.message.reply_text("🔒 You are not authorized to record transactions.")
except Exception as e:
    logger.exception("Unexpected error recording transaction", error=str(e))
    await update.message.reply_text("⚠️ An error occurred. Please try again.")
```

### PostgreSQL Guidelines

- Use JSONB for flexible data (category breakdowns, report data)
- Arrays for multi-value columns (tags, flags)
- Window functions for analytics (ROW_NUMBER, SUM OVER)
- Indexes on foreign keys and frequently queried columns
- Constraints for data integrity (CHECK, UNIQUE, NOT NULL)
- Transactions for multi-step operations (async with session.begin())

**SQLAlchemy 2.0 Patterns**:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.transaction import Transaction

async def get_user_transactions(session: AsyncSession, user_id: int):
    """Fetch all transactions for a user."""
    stmt = select(Transaction).where(Transaction.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalars().all()
```

### Telegram Bot Guidelines

- Async handlers with `async def` signature
- Use `Application` builder pattern (not deprecated `Updater`)
- Conversation handlers for multi-step flows (ConversationHandler)
- Inline keyboards for user interactions (InlineKeyboardMarkup)
- HTML formatting for messages (parse_mode=ParseMode.HTML)
- Error handling with `error_handler` callback
- Rate limiting awareness (respect Telegram API limits)

**Handler Pattern**:

```python
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

# Conversation states
AMOUNT, DESCRIPTION, CATEGORY = range(3)

async def start_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start income recording conversation."""
    await update.message.reply_text(
        "💰 <b>Record Income</b>\n\n"
        "Enter the amount in Rupiah:",
        parse_mode=ParseMode.HTML
    )
    return AMOUNT

async def receive_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Process amount input."""
    try:
        amount = Decimal(update.message.text)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        context.user_data["amount"] = amount
        await update.message.reply_text("Enter description:")
        return DESCRIPTION
    except (ValueError, decimal.InvalidOperation):
        await update.message.reply_text("❌ Invalid amount. Please enter a number.")
        return AMOUNT
```

## Version Control Guidelines

### Semantic Versioning

- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes (API changes, database schema migrations)
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (no new features)
- Tag releases with `git tag -a v1.0.0 -m "Release v1.0.0"`

### Commit Messages

- Use conventional commits format: `<type>(<scope>): <subject>`
- Types: feat, fix, docs, style, refactor, test, chore
- Scope: module name (e.g., handlers, services, models)
- Subject: imperative mood, lowercase, no period

**Examples**:

```
feat(handlers): add /balance command for account summary
fix(services): correct timezone handling in daily summary
docs(readme): update installation instructions
test(repositories): add integration tests for user repository
```

## General Best Practices

### Naming Conventions

- Variables/functions: `snake_case` (Python convention)
- Classes: `PascalCase` (Python convention)
- Constants: `UPPER_SNAKE_CASE` (Python convention)
- Database tables: `lowercase_plural` (e.g., `users`, `transactions`)
- Database columns: `snake_case` (e.g., `user_id`, `created_at`)

### Code Organization

```
src/
├── bot/
│   ├── handlers/         # Telegram command/callback handlers (thin layer)
│   ├── services/         # Business logic (validation, calculations)
│   ├── repositories/     # Data access layer (database queries)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic models for validation
│   └── utils/            # Helper functions (formatters, validators)
├── migrations/           # Alembic database migrations
├── config/               # Configuration (settings.py with Pydantic)
└── main.py               # Application entry point

tests/
├── unit/                 # Unit tests (70% of test suite)
├── integration/          # Integration tests (20% of test suite)
└── e2e/                  # End-to-end tests (10% of test suite)
```

### Error Handling

- Use specific exception types (ValueError, KeyError, UnauthorizedError)
- Log errors with context (user_id, transaction_id, correlation_id)
- Return user-friendly error messages (Telegram formatting)
- Retry logic for transient errors (database connection, API timeout)
- Graceful degradation (fallback to default behavior)

### Logging

- Use structlog for structured JSON logging
- Include correlation IDs for request tracing
- Log levels: DEBUG (development), INFO (production), WARNING (issues), ERROR (failures)
- Never log sensitive data (amounts, descriptions in production)
- Log performance metrics (query time, handler execution time)

**Example**:

```python
import structlog

logger = structlog.get_logger()

async def record_transaction(...):
    logger.info(
        "Recording transaction",
        user_id=user_id,
        transaction_type=transaction_type,
        category_id=category_id,
        correlation_id=context.user_data.get("correlation_id")
    )
    try:
        result = await repository.create(...)
        logger.info(
            "Transaction recorded successfully",
            transaction_id=result.transaction_id,
            correlation_id=context.user_data.get("correlation_id")
        )
        return result
    except Exception as e:
        logger.exception(
            "Failed to record transaction",
            error=str(e),
            correlation_id=context.user_data.get("correlation_id")
        )
        raise
```

### Configuration Management

- Use Pydantic Settings for environment variable parsing
- .env file for local development (never commit)
- Environment-specific configs (development, staging, production)
- Type validation for all config values

**Example** (config/settings.py):

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    telegram_bot_token: str
    telegram_admin_id: int

    # Database
    database_url: str
    database_pool_size: int = 10

    # Scheduler
    daily_summary_time: str = "00:00"  # WITA timezone

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

## Project-Specific Guidance

### Financial Transaction Handling

- Use `Decimal` type for all monetary values (never float)
- Validate amounts are positive for income/expenses
- Store amounts in smallest unit (Rupiah, no decimal places)
- Timezone-aware timestamps (WITA = UTC+8)
- Transaction atomicity (database transactions for multi-step operations)

### WITA Timezone Handling

- Use pytz for timezone conversion
- Store all timestamps in UTC in database
- Convert to WITA for display and daily summary generation
- Handle timezone-aware datetime objects

**Example**:

```python
import pytz
from datetime import datetime

WITA = pytz.timezone("Asia/Makassar")  # UTC+8, no DST

def now_wita() -> datetime:
    """Get current time in WITA timezone."""
    return datetime.now(WITA)

def to_wita(dt: datetime) -> datetime:
    """Convert UTC datetime to WITA."""
    return dt.astimezone(WITA)
```

### Daily Summary Generation

- Scheduled at 00:00 WITA (APScheduler with CronTrigger)
- Aggregate transactions from previous day (WITA date)
- Store category breakdown as JSONB
- Send formatted summary to all active users
- Performance goal: <60s for 500 transactions

### Data Retention

- 3-year retention policy for transactions
- Archive old data to separate table (transactions_archive)
- Monthly cleanup job (last day of month)
- Soft delete for user-initiated deletions (status='deleted')

## Architecture Guidelines

### Layered Architecture

```
Telegram Bot (Presentation Layer)
    ↓
Handlers (Thin controller layer - parse input, format output)
    ↓
Services (Business logic - validation, calculations, workflows)
    ↓
Repositories (Data access - database queries, no business logic)
    ↓
Models (Domain entities - SQLAlchemy ORM models)
    ↓
PostgreSQL Database
```

### Dependency Flow

- Handlers depend on Services
- Services depend on Repositories
- Repositories depend on Models
- No circular dependencies
- Inject dependencies via constructor (dependency injection)

### Boundaries

- No database queries in handlers (use services)
- No business logic in repositories (pure data access)
- No Telegram API calls in services (return data, handlers send messages)
- No direct model access from handlers (use services)

## Important Reminders

1. **Always use exact technology versions** documented in this file
2. **Never introduce newer language features** not available in Python 3.11
3. **Prioritize consistency** with existing codebase over external best practices
4. **Follow the layered architecture** strictly (handlers → services → repositories → models)
5. **Test coverage requirements**: ≥80% overall, 100% for financial calculations
6. **Performance goals**: <2s transaction confirmation, <5s daily summary, <60s report delivery
7. **Security first**: OWASP Top 10 compliance, input validation, SQL injection prevention
8. **Financial data handling**: Use Decimal, validate amounts, timezone awareness (WITA)
9. **Documentation**: Docstrings for all public functions, type hints everywhere
10. **Logging**: Structured JSON logging with correlation IDs, never log sensitive data

## Success Criteria

Code generated by Copilot should:

- ✅ Be compatible with Python 3.11 and all specified library versions
- ✅ Follow the layered architecture (handlers → services → repositories → models)
- ✅ Include proper error handling and logging
- ✅ Have comprehensive docstrings and type hints
- ✅ Be testable with ≥80% coverage (100% for financial logic)
- ✅ Meet performance goals (<2s transactions, <5s summaries)
- ✅ Follow OWASP Top 10 security practices
- ✅ Handle WITA timezone correctly
- ✅ Use Decimal for monetary values
- ✅ Be consistent with existing codebase patterns
