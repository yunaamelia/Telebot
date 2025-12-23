# Implementation Plan: Telegram Cash Flow Management Bot

**Branch**: `001-cashflow-bot` | **Date**: 2025-12-18 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-cashflow-bot/spec.md`

## Summary

Build a Telegram bot for company cash flow management enabling real-time transaction recording (income/expenses) with automated daily financial reports delivered at 24:00 WITA. System uses Python 3.11+ with python-telegram-bot framework, PostgreSQL for data persistence, and APScheduler for report automation. Architecture supports 20+ concurrent users, handles 500+ daily transactions, and maintains 1-year active data with 3-year archival compliance.

## Technical Context

**Language/Version**: Python 3.11 (async/await support, improved performance, security patches)  
**Primary Dependencies**: python-telegram-bot 20.x (native async), SQLAlchemy 2.x (ORM), APScheduler 3.x (WITA scheduling), pytz (timezone handling)  
**Storage**: PostgreSQL 15+ (ACID compliance, JSON support, complex queries, proven reliability for financial data)  
**Testing**: pytest 7.x (unit), pytest-asyncio (async tests), pytest-cov (coverage ≥80%), Testcontainers (integration with real PostgreSQL)  
**Target Platform**: Linux server (Ubuntu 22.04 LTS recommended, systemd service management)  
**Project Type**: Single project (backend service with CLI administration interface)  
**Performance Goals**: <2s transaction confirmation (p95), <5s daily summary generation (500 tx), <60s report delivery from 24:00 WITA trigger  
**Constraints**: <200ms p95 API response, Telegram Bot API rate limits (30 msg/sec), WITA (UTC+8) timezone accuracy, zero data loss requirement  
**Scale/Scope**: 20 concurrent users, 500 transactions/day, 1-year active data (~180k transactions), 3-year total retention, 99.5% uptime during business hours

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Code Quality & SOLID Architecture ✅

- **PASS**: Architecture separates concerns: handlers (presentation), services (business logic), repositories (data access), models (domain)
- **PASS**: Complexity managed via small, focused modules: transaction_service.py, report_generator.py, keyboard_builder.py
- **ENFORCEMENT**: Pylint + flake8 in CI, complexity limit ≤15, function length ≤50 LOC

### Principle II: Test-First Development ✅  

- **PASS**: TDD workflow: Phase 0 includes test infrastructure setup before Phase 1 implementation
- **PASS**: Testing pyramid: Unit tests (transaction validation, amount parsing), Integration tests (DB operations, Telegram API), E2E tests (full user workflows)
- **TARGET**: ≥80% coverage requirement, 100% for financial calculations

### Principle III: User Experience Consistency & Accessibility ✅

- **PASS**: Sequential prompt flow provides clear guidance (amount → description)
- **PASS**: Consistent emoji usage (💰 income, 💸 expense, 📊 summary) across all messages
- **PASS**: Error messages include examples and corrective guidance per FR-025
- **NOTE**: Telegram platform inherently mobile-optimized; keyboard navigation reduces accessibility barriers

### Principle IV: Performance Requirements & SLOs ✅

- **PASS**: <2s response time target aligns with constitution <200ms p95 API requirement
- **PASS**: 99.5% uptime target matches constitution SLO during business hours
- **PASS**: Error budget approach: 0.1% allows for risky deployments while maintaining reliability
- **MONITORING**: DataDog/Prometheus for continuous performance tracking

### Principle V: Observability & Debuggability ✅

- **PASS**: Structured logging (JSON format) with correlation IDs for request tracing
- **PASS**: Critical error notifications to management (report failures, auth failures 3+, downtime >5min)
- **PASS**: Audit trail: All transactions logged with user_id, timestamp, action type per FR-021
- **INSTRUMENTATION**: Metrics for transaction rates, error rates, response times

**GATE RESULT**: ✅ **PASSED** - All 5 constitution principles satisfied. Proceed to Phase 0 research.

## Project Structure

### Documentation (this feature)

```text
specs/001-cashflow-bot/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output - Technology decisions, best practices
├── data-model.md        # Phase 1 output - Database schema, entity relationships
├── quickstart.md        # Phase 1 output - Development setup, test scenarios
├── contracts/           # Phase 1 output - Bot command contracts, message schemas
│   ├── commands.yaml    # All bot commands with parameters
│   └── messages.yaml    # Message templates and formats
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
cashflow-bot/
├── src/
│   ├── bot/
│   │   ├── __init__.py
│   │   ├── handlers/          # Command and callback handlers
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py # /income, /expense handlers
│   │   │   ├── summary.py     # /summary handler
│   │   │   ├── history.py     # /history handler
│   │   │   ├── auth.py        # /register, /approve handlers
│   │   │   └── keyboard.py    # Inline keyboard callbacks
│   │   ├── services/          # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── transaction_service.py
│   │   │   ├── report_service.py
│   │   │   ├── auth_service.py
│   │   │   └── notification_service.py
│   │   ├── models/            # Domain models
│   │   │   ├── __init__.py
│   │   │   ├── transaction.py
│   │   │   ├── user.py
│   │   │   ├── category.py
│   │   │   └── report.py
│   │   ├── repositories/      # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── transaction_repository.py
│   │   │   ├── user_repository.py
│   │   │   └── category_repository.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── formatters.py  # Currency, date formatting
│   │   │   ├── validators.py  # Input validation
│   │   │   └── timezone.py    # WITA timezone handling
│   │   └── keyboards/         # Inline keyboard builders
│   │       ├── __init__.py
│   │       ├── main_menu.py
│   │       └── categories.py
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── daily_report.py    # APScheduler job for 24:00 WITA
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py      # DB connection pool
│   │   ├── migrations/        # Alembic migrations
│   │   └── session.py         # Session management
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py        # Pydantic settings
│   │   └── logging.py         # Logging configuration
│   └── main.py                # Application entry point
├── tests/
│   ├── unit/
│   │   ├── services/
│   │   ├── utils/
│   │   └── models/
│   ├── integration/
│   │   ├── test_database.py
│   │   ├── test_telegram_api.py
│   │   └── test_scheduler.py
│   └── e2e/
│       └── test_user_workflows.py
├── migrations/                # Alembic migrations directory
├── .env.example              # Environment variables template
├── .gitignore
├── requirements.txt          # Production dependencies
├── requirements-dev.txt      # Development dependencies
├── pytest.ini                # Pytest configuration
├── .pylintrc                 # Pylint rules
├── alembic.ini              # Database migration config
├── docker-compose.yml       # Local development stack
├── Dockerfile               # Production container image
└── README.md                # Setup and deployment guide
```

**Structure Decision**: Single project structure selected because all components run as unified service. No frontend/backend separation needed since Telegram provides UI. CLI administration tools integrated into main service via separate command handlers.

## Architecture

### System Architecture Overview

The Cash Flow Bot follows a **layered architecture** pattern with clear separation of concerns, enabling maintainability, testability, and scalability. The system is designed as a **single monolithic service** that handles all bot operations, scheduled tasks, and database interactions.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Telegram Bot API                             │
│                   (api.telegram.org - External)                      │
└──────────────────────────────┬──────────────────────────────────────┘
                                │ HTTPS / Webhook or Long Polling
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    python-telegram-bot Library                       │
│              (Update Dispatcher, Handler Manager)                    │
└──────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                          BOT APPLICATION                             │
│                        (src/main.py - Entry)                         │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    HANDLERS LAYER                             │  │
│  │          (Presentation - User Interaction)                    │  │
│  │                                                               │  │
│  │  • transaction.py    (/income, /expense commands)           │  │
│  │  • summary.py        (/summary command)                      │  │
│  │  • history.py        (/history command)                      │  │
│  │  • auth.py           (/register, /approve commands)          │  │
│  │  • keyboard.py       (Callback query handlers)               │  │
│  │  • main_menu.py      (/start, /help commands)                │  │
│  │  • error.py          (Global error handler)                  │  │
│  │                                                               │  │
│  │  Responsibilities:                                           │  │
│  │  - Parse user commands and messages                          │  │
│  │  - Validate input format                                     │  │
│  │  - Call service layer for business logic                     │  │
│  │  - Format responses for Telegram                             │  │
│  │  - Handle conversation states                                │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    SERVICES LAYER                             │  │
│  │            (Business Logic - Core Operations)                 │  │
│  │                                                               │  │
│  │  • transaction_service.py  (Transaction CRUD, validation)    │  │
│  │  • report_service.py       (Summary generation, analytics)   │  │
│  │  • auth_service.py         (User registration, approval)     │  │
│  │  • notification_service.py (Alert sending, reports)          │  │
│  │                                                               │  │
│  │  Responsibilities:                                           │  │
│  │  - Business rules enforcement                                │  │
│  │  - Amount validation (<10B, positive)                        │  │
│  │  - Duplicate detection                                       │  │
│  │  - Financial calculations                                    │  │
│  │  - Timezone conversions (UTC ↔ WITA)                        │  │
│  │  - Authorization checks                                      │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                 REPOSITORIES LAYER                            │  │
│  │             (Data Access - Database Operations)               │  │
│  │                                                               │  │
│  │  • transaction_repository.py  (Transaction CRUD)             │  │
│  │  • user_repository.py         (User CRUD)                    │  │
│  │  • category_repository.py     (Category queries, caching)    │  │
│  │                                                               │  │
│  │  Responsibilities:                                           │  │
│  │  - SQL query construction                                    │  │
│  │  - Database session management                               │  │
│  │  - Transaction scope handling                                │  │
│  │  - Error handling for DB operations                          │  │
│  │  - No business logic (pure data access)                      │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                      │
│                               ▼                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     MODELS LAYER                              │  │
│  │              (Domain Entities - SQLAlchemy ORM)               │  │
│  │                                                               │  │
│  │  • transaction.py  (Transaction model with constraints)      │  │
│  │  • user.py         (User model with status enum)             │  │
│  │  • category.py     (Category model with type check)          │  │
│  │  • report.py       (DailySummary model with JSONB)           │  │
│  │                                                               │  │
│  │  Responsibilities:                                           │  │
│  │  - Database table mapping                                    │  │
│  │  - Column definitions and constraints                        │  │
│  │  - Relationships (foreign keys)                              │  │
│  │  - Data validation at model level                            │  │
│  └───────────────────────────┬──────────────────────────────────┘  │
│                               │                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                     UTILITIES                                 │  │
│  │                                                               │  │
│  │  • formatters.py   (Currency, ID generation)                 │  │
│  │  • validators.py   (Input validation)                        │  │
│  │  • timezone.py     (WITA conversions)                        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   SCHEDULER (APScheduler)                     │  │
│  │                                                               │  │
│  │  • daily_report.py  (24:00 WITA cron job)                    │  │
│  │                                                               │  │
│  │  Responsibilities:                                           │  │
│  │  - Schedule report generation at 24:00 WITA                  │  │
│  │  - Invoke report_service for summary                         │  │
│  │  - Handle timezone-aware job execution                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   CONFIG & LOGGING                            │  │
│  │                                                               │  │
│  │  • settings.py  (Pydantic environment config)                │  │
│  │  • logging.py   (Structured JSON logging)                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
└──────────────────────────────┬──────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  DATABASE CONNECTION POOL                            │
│                   (SQLAlchemy AsyncEngine)                           │
└──────────────────────────────┬──────────────────────────────────────┘
                                │ asyncpg (PostgreSQL driver)
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                             │
│                          (Version 15+)                               │
│                                                                       │
│  Tables:                                                             │
│  • users                (User accounts, status, employee_id)        │
│  • categories           (Transaction categories with type)           │
│  • transactions         (Financial transactions with audit)          │
│  • daily_summaries      (Aggregated daily reports, JSONB)           │
│                                                                       │
│  Indexes:                                                            │
│  • transactions(user_id, timestamp)  - User history queries         │
│  • transactions(timestamp)           - Date range filtering          │
│  • transactions(category_id)         - Category analytics            │
│  • daily_summaries(summary_date)     - Report retrieval              │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow Diagrams

#### 1. Record Income Transaction Flow

```
┌──────────────┐
│     User     │
└──────┬───────┘
       │ /income 500000 Client payment
       ▼
┌──────────────────────────────────────┐
│    transaction.py (Handler)          │
│  • Parse command arguments           │
│  • Extract amount, description       │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  transaction_service.py (Service)    │
│  • Validate amount (>0, <10B)        │
│  • Check for duplicates              │
│  • Get user from session             │
│  • Generate transaction ID           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ transaction_repository.py (Repo)     │
│  • Create Transaction object         │
│  • Save to database                  │
│  • Return saved transaction          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│      PostgreSQL Database              │
│  • INSERT INTO transactions          │
│  • Return transaction_id             │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  transaction_service.py (Service)    │
│  • Format confirmation message       │
│  • Return to handler                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│    transaction.py (Handler)          │
│  • Send Telegram message             │
│  • Log transaction recorded          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│     User     │ ✅ Income Recorded Successfully
└──────────────┘
```

#### 2. Daily Report Generation Flow (Scheduled)

```
┌──────────────────────────────────────┐
│   APScheduler (CronTrigger)          │
│   Fires at 24:00 WITA daily          │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  daily_report.py (Scheduler Job)     │
│  • Get yesterday's date (WITA)       │
│  • Invoke report service             │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  report_service.py (Service)         │
│  • Query transactions for date       │
│  • Calculate totals by type          │
│  • Calculate category breakdown      │
│  • Generate percentage distribution  │
│  • Compare with previous day         │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ transaction_repository.py (Repo)     │
│  • SELECT * FROM transactions        │
│    WHERE DATE = yesterday            │
│  • GROUP BY category, type           │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│      PostgreSQL Database              │
│  • Execute aggregation query         │
│  • Return summary data               │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  report_service.py (Service)         │
│  • Create DailySummary object        │
│  • Save to daily_summaries table     │
│  • Format report message             │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ notification_service.py (Service)    │
│  • Send to MANAGEMENT_CHAT_ID        │
│  • Handle errors (retry, alert)      │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│       Telegram Bot API                │
│  POST /sendMessage                   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│  Management  │ 📊 Daily Financial Report
│     Chat     │
└──────────────┘
```

#### 3. User Registration Approval Flow

```
┌──────────────┐
│  New User    │
└──────┬───────┘
       │ /register EMP12345
       ▼
┌──────────────────────────────────────┐
│      auth.py (Handler)                │
│  • Check user not already registered │
│  • Validate employee_id format       │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   auth_service.py (Service)           │
│  • Create User with status=pending   │
│  • Generate notification for admin   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  user_repository.py (Repo)            │
│  • INSERT INTO users                 │
│  • Return user object                │
└──────┬───────────────────────────────┘
       │
       ├─────────────────────────────────┐
       │                                  │
       ▼                                  ▼
┌─────────────────┐          ┌──────────────────────┐
│   New User      │          │  notification_service │
│ (Confirmation)  │          │  • Send to admin      │
└─────────────────┘          └──────┬───────────────┘
                                     │
                                     ▼
                            ┌──────────────────┐
                            │  Admin Chat      │
                            │ 🔔 New Request   │
                            │ [Approve][Reject]│
                            └──────┬───────────┘
                                   │ Admin clicks [Approve]
                                   ▼
                            ┌──────────────────────┐
                            │ auth.py (Handler)    │
                            │ /approve <user_id>   │
                            └──────┬───────────────┘
                                   │
                                   ▼
                            ┌──────────────────────┐
                            │ auth_service.py      │
                            │ • Update status      │
                            │   to 'active'        │
                            └──────┬───────────────┘
                                   │
                                   ▼
                            ┌──────────────────────┐
                            │ user_repository.py   │
                            │ • UPDATE users       │
                            │   SET status=active  │
                            └──────┬───────────────┘
                                   │
                                   ▼
                            ┌──────────────────────┐
                            │  New User            │
                            │ 🎉 Approved!         │
                            │ (Can now use bot)    │
                            └──────────────────────┘
```

### Component Interaction Matrix

| Component | Depends On | Used By | Responsibility |
|-----------|------------|---------|----------------|
| **Handlers** | Services, Utils | Telegram Bot API | User interaction, input parsing, response formatting |
| **Services** | Repositories, Utils, Models | Handlers, Scheduler | Business logic, validation, calculations |
| **Repositories** | Models, Database | Services | Data access, query execution |
| **Models** | SQLAlchemy | Repositories | ORM mapping, constraints |
| **Scheduler** | Services | None (triggered by time) | Scheduled task execution |
| **Utils** | None | Handlers, Services | Helper functions, formatting |
| **Database** | None | Repositories | Data persistence |

### Technology Stack Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                           │
│                                                                   │
│  python-telegram-bot 20.7  →  Async/await handlers              │
│  Telegram Bot API          →  Message/keyboard formatting       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│                                                                   │
│  Python 3.11               →  Async/await, type hints            │
│  Pydantic Settings 2.5     →  Environment configuration          │
│  structlog 23.2            →  Structured JSON logging            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                         │
│                                                                   │
│  Custom Services           →  Transaction validation, reports    │
│  pytz 2023.3               →  WITA timezone handling             │
│  APScheduler 3.10.4        →  Daily report scheduling            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                            │
│                                                                   │
│  SQLAlchemy 2.0.25         →  Async ORM, session management      │
│  asyncpg                   →  PostgreSQL async driver            │
│  Alembic 1.12              →  Database migrations                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     PERSISTENCE LAYER                            │
│                                                                   │
│  PostgreSQL 15+            →  ACID transactions, JSONB support   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                         │
│                                                                   │
│  Docker 24+                →  Container runtime                  │
│  docker-compose            →  Multi-container orchestration      │
│  systemd                   →  Production service management      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      PRODUCTION SERVER                           │
│                     (Ubuntu 22.04 LTS)                           │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Docker Environment                          │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │       cashflow-bot Container                       │ │   │
│  │  │                                                     │ │   │
│  │  │  • Python 3.11 application                         │ │   │
│  │  │  • Bot handlers, services, scheduler              │ │   │
│  │  │  • Logs to stdout (JSON)                          │ │   │
│  │  │  • Health check: /healthz endpoint                │ │   │
│  │  │                                                     │ │   │
│  │  │  Environment Variables:                            │ │   │
│  │  │  - TELEGRAM_BOT_TOKEN                             │ │   │
│  │  │  - DATABASE_URL                                    │ │   │
│  │  │  - MANAGEMENT_CHAT_ID                             │ │   │
│  │  │  - TIMEZONE=Asia/Makassar                         │ │   │
│  │  │                                                     │ │   │
│  │  └────────────────┬───────────────────────────────────┘ │   │
│  │                   │                                      │   │
│  │                   │ PostgreSQL connection                │   │
│  │                   ▼                                      │   │
│  │  ┌────────────────────────────────────────────────────┐ │   │
│  │  │       postgres Container                           │ │   │
│  │  │                                                     │ │   │
│  │  │  • PostgreSQL 15                                   │ │   │
│  │  │  • Persistent volume: /var/lib/postgresql/data    │ │   │
│  │  │  • Network: internal                               │ │   │
│  │  │  • Port: 5432 (not exposed externally)            │ │   │
│  │  │                                                     │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              systemd Service Manager                     │   │
│  │                                                           │   │
│  │  • cashflow-bot.service                                  │   │
│  │  • Auto-restart on failure                               │   │
│  │  • Logs to journald                                      │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Backup System                               │   │
│  │                                                           │   │
│  │  • Daily cron job (02:00 AM)                            │   │
│  │  • pg_dump to /backups/                                 │   │
│  │  • 7-day retention                                       │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────┬───────────────────────────────────────┘
                            │
                            │ HTTPS (443)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Telegram Servers                            │
│                   (api.telegram.org)                             │
│                                                                   │
│  • Webhook endpoint (optional)                                   │
│  • Long polling (default)                                        │
│  • Rate limiting: 30 msg/sec                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                             │
│                                                                   │
│  Layer 1: Authentication & Authorization                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Whitelist-based user access                             │ │
│  │  • Employee ID validation                                  │ │
│  │  • Admin approval workflow                                 │ │
│  │  • Session management per Telegram chat                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Layer 2: Input Validation                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Amount validation (>0, <10B)                            │ │
│  │  • SQL injection prevention (parameterized queries)        │ │
│  │  • Command injection prevention                            │ │
│  │  • Type checking with Pydantic models                      │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Layer 3: Data Protection                                        │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • Environment variable for secrets                        │ │
│  │  • No hardcoded credentials                                │ │
│  │  • Encrypted database connections (SSL)                    │ │
│  │  • Sensitive data not logged                               │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Layer 4: Network Security                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • HTTPS only for Telegram API                             │ │
│  │  • PostgreSQL not exposed externally                       │ │
│  │  • Docker network isolation                                │ │
│  │  • Firewall rules (UFW/iptables)                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Layer 5: Audit & Monitoring                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • All transactions logged with user_id                    │ │
│  │  • Structured logging with correlation IDs                 │ │
│  │  • Critical error alerts to management                     │ │
│  │  • Metrics collection for anomaly detection                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Concurrency Model

```
┌─────────────────────────────────────────────────────────────────┐
│                 ASYNC/AWAIT CONCURRENCY                          │
│                                                                   │
│  Main Event Loop (asyncio)                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐ │ │
│  │  │  User 1       │  │  User 2       │  │  User N       │ │ │
│  │  │  Request      │  │  Request      │  │  Request      │ │ │
│  │  └───────┬───────┘  └───────┬───────┘  └───────┬───────┘ │ │
│  │          │                   │                   │          │ │
│  │          ▼                   ▼                   ▼          │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │         Handler Coroutines (Async)                  │  │ │
│  │  │  • Non-blocking I/O                                 │  │ │
│  │  │  • await database queries                           │  │ │
│  │  │  • await Telegram API calls                         │  │ │
│  │  └─────────────────┬───────────────────────────────────┘  │ │
│  │                    │                                       │ │
│  │                    ▼                                       │ │
│  │  ┌─────────────────────────────────────────────────────┐  │ │
│  │  │       Database Connection Pool                      │  │ │
│  │  │  • Max connections: 10                              │  │ │
│  │  │  • Async connections (asyncpg)                      │  │ │
│  │  └─────────────────────────────────────────────────────┘  │ │
│  │                                                             │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  APScheduler Background Thread                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  • AsyncIOScheduler                                        │ │
│  │  • CronTrigger for 24:00 WITA                             │ │
│  │  • Job runs in event loop                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Performance Characteristics:
• ~20 concurrent users supported
• Non-blocking database operations
• Efficient memory usage (single event loop)
• No thread contention (single-threaded async)
```

### Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     ERROR HANDLING LAYERS                        │
│                                                                   │
│  User Error (Validation Failure)                                 │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Handler catches ValueError                                 │ │
│  │  → Format user-friendly message                            │ │
│  │  → Include example usage                                    │ │
│  │  → Send to user via Telegram                               │ │
│  │  → Log at WARNING level                                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Business Logic Error (Duplicate, Unauthorized)                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Service raises custom exception                            │ │
│  │  → Handler catches specific exception                       │ │
│  │  → Return actionable message to user                        │ │
│  │  → Log at INFO level (expected behavior)                    │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  System Error (Database, Network)                                │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Service/Repository raises exception                        │ │
│  │  → Global error handler catches                             │ │
│  │  → Log at ERROR level with context                          │ │
│  │  → Send generic error to user                               │ │
│  │  → Retry logic for transient errors                         │ │
│  │  → Alert management if critical                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Critical Error (Service Down, Database Unavailable)             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Multiple retries failed                                    │ │
│  │  → Log at CRITICAL level                                    │ │
│  │  → Send alert to MANAGEMENT_CHAT_ID                        │ │
│  │  → Update service health status                             │ │
│  │  → Trigger restart if applicable                            │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Decisions Records (ADRs)

**ADR-001: Layered Architecture Pattern**

- **Decision**: Use layered architecture with handlers → services → repositories → models
- **Rationale**: Clear separation of concerns, testability, maintainability per Constitution Principle I
- **Alternatives Considered**: Hexagonal architecture (too complex for single service), flat structure (poor maintainability)

**ADR-002: Single Monolithic Service**

- **Decision**: Deploy as single service, not microservices
- **Rationale**: Simple deployment, no network overhead, 20 concurrent users doesn't justify microservices complexity
- **Alternatives Considered**: Microservices (overkill), serverless (cold starts problematic for Telegram bot)

**ADR-003: PostgreSQL over SQLite**

- **Decision**: Use PostgreSQL for persistence
- **Rationale**: ACID compliance, concurrent writes, JSONB support, production-ready for financial data
- **Alternatives Considered**: SQLite (no concurrent writes), MongoDB (schema flexibility not needed)

**ADR-004: Async/Await Concurrency**

- **Decision**: Use Python asyncio for concurrency
- **Rationale**: python-telegram-bot 20.x native async, non-blocking I/O, efficient for I/O-bound workload
- **Alternatives Considered**: Threading (GIL contention), multiprocessing (overkill)

**ADR-005: APScheduler for Cron Jobs**

- **Decision**: Use APScheduler for 24:00 WITA report generation
- **Rationale**: Simple, timezone-aware, runs in same process, no external dependencies
- **Alternatives Considered**: Celery (too heavy), system cron (timezone handling complex)

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | All constitution principles satisfied without violations |

## Phases

### Phase 0: Research & Technology Validation

**Duration**: 2-3 days  
**Objective**: Validate technology choices, resolve NEEDS CLARIFICATION items, document best practices

**Research Topics**:

1. Python telegram bot framework comparison (python-telegram-bot vs. aiogram vs. Telebot)
2. PostgreSQL vs. SQLite for financial transaction storage
3. APScheduler vs. Celery for WITA timezone scheduling
4. Telegram API formatting limitations and Fira Code font integration approaches
5. Testing strategies for async Telegram bots
6. Docker deployment best practices for Python services

**Output**: research.md with technology decisions and rationales

**Success Criteria**: Zero NEEDS CLARIFICATION markers in Technical Context, all technology choices justified with benchmarks or industry references

---

### Phase 1: Core Design & Contracts

**Duration**: 3-4 days  
**Objective**: Define data model, API contracts, and developer quickstart guide

**Deliverables**:

1. **data-model.md**: Database schema with all entities (Transaction, User, Category, Report, DailySummary)
2. **contracts/commands.yaml**: All bot commands with parameters, validation rules, response formats
3. **contracts/messages.yaml**: Message templates for confirmations, errors, summaries, reports
4. **quickstart.md**: Development environment setup, test data scenarios, example workflows

**Key Activities**:

- Design PostgreSQL schema with proper indexes (date, user_id, category)
- Define all 15+ bot commands (/income, /expense, /summary, /history, /register, /approve, /start, /help, etc.)
- Create message template system with emoji standards and formatting
- Document test scenarios for each user story

**Success Criteria**: Database schema supports all functional requirements, command contracts cover all user stories, quickstart enables new developer onboarding in <2 hours

---

### Phase 2: Project Setup & Infrastructure

**Duration**: 2 days  
**Objective**: Initialize project structure, configure tooling, set up CI/CD foundations

**Tasks**:

- Initialize Python 3.11 project with virtual environment
- Configure pytest, pytest-asyncio, pytest-cov
- Set up Pylint, flake8, black (code formatting)
- Configure Alembic for database migrations
- Create docker-compose.yml for local PostgreSQL
- Set up GitHub Actions for CI (lint, test, coverage)
- Create .env.example with all configuration variables
- Initialize logging with structlog (JSON format)

**Deliverables**: Working CI pipeline, local development environment, initial migration files

---

### Phase 3: Database Layer & Models

**Duration**: 3-4 days  
**Objective**: Implement data models, repositories, and database operations

**Tasks** (TDD approach - tests first):

1. Define SQLAlchemy models: Transaction, User, Category, Report, DailySummary
2. Write unit tests for model validation (amount >0, category constraints)
3. Implement transaction repository with CRUD operations
4. Implement user repository with registration workflow
5. Create category seeding (Operational, Salaries, Supplies, Marketing, Other)
6. Write integration tests using Testcontainers (real PostgreSQL)
7. Implement connection pooling and session management
8. Create database indexes for performance (date, user_id, category)

**Deliverables**: Complete data access layer with ≥80% test coverage, working migrations, seeded categories

---

### Phase 4: Core Services & Business Logic

**Duration**: 5-6 days  
**Objective**: Implement transaction recording, validation, and calculation services

**Tasks** (TDD - write tests before implementation):

1. TransactionService: record_income(), record_expense(), validate_amount()
2. Write tests for amount parsing (handle "500000", "500,000", "500.000")
3. Implement duplicate detection logic (60-second window, same amount/description/category)
4. AuthService: register_user(), approve_user(), check_authorization()
5. Write tests for user authorization flows
6. ReportService: generate_daily_summary(), calculate_net_cash_flow()
7. Write tests for financial calculations (ensure accuracy, handle edge cases)
8. Implement category grouping and subtotal calculations
9. NotificationService: send_critical_alert() for management notifications

**Deliverables**: Business logic layer with 100% test coverage for financial calculations, validated amount parsing, working auth workflow

---

### Phase 5: Telegram Bot Handlers

**Duration**: 6-7 days  
**Objective**: Implement all bot commands, conversation flows, and inline keyboards

**Tasks** (TDD where possible, E2E tests for full flows):

1. Implement /start handler with main menu keyboard
2. Implement /income handler (command parsing, sequential prompts)
3. Write E2E test for income recording workflow
4. Implement /expense handler with category selection keyboard
5. Write E2E test for expense recording with categories
6. Implement keyboard callback handlers (category selection, navigation)
7. Implement /summary handler with formatted output
8. Implement /history handler with pagination
9. Implement /register and /approve handlers for user management
10. Implement /help handler with command reference
11. Create keyboard builders (main menu, categories, pagination)
12. Implement error handling with user-friendly messages
13. Add input validation with examples (per FR-025)

**Deliverables**: All bot commands working, inline keyboards functional, conversation state management, ≥80% handler coverage

---

### Phase 6: Formatting & UI Polish

**Duration**: 3-4 days  
**Objective**: Implement message formatting with emoji, currency formatting, Telegram HTML mode

**Tasks**:

1. Create formatters.py: format_currency() with Rp and thousand separators
2. Implement transaction confirmation message templates (emoji, bold, monospace)
3. Create summary report formatter with category grouping
4. Implement daily report formatter for 24:00 WITA delivery
5. Add timestamp formatting for WITA timezone display
6. Implement HTML parse mode for rich formatting
7. **Fira Code integration**: Research Telegram limitations, implement fallback strategy
   - Document that Telegram doesn't support custom fonts directly
   - Use monospace markdown for numeric amounts (mimics Fira Code)
   - Consider future web dashboard for full Fira Code support
8. Test formatting across Android, iOS, Desktop clients

**Deliverables**: Professional message formatting, currency display with Rp formatting, consistent emoji usage, documented Fira Code limitations

**Note on Fira Code**: Telegram Bot API doesn't support custom fonts. Monospace formatting (`text`) is available via HTML or MarkdownV2. For true Fira Code rendering, would require:

- Option A: Generate images with Pillow library rendering text in Fira Code (high latency, not mobile-friendly)
- Option B: Web dashboard using Telegram Web App with Fira Code CSS (@font-face with woff2)
- Option C: Accept Telegram's default monospace font (Courier/Menlo) and document limitation

**Recommendation**: Use Option C for MVP (default monospace), plan Option B (Web App) for future iteration

---

### Phase 7: Scheduling & Automation

**Duration**: 3 days  
**Objective**: Implement daily report generation at 24:00 WITA with retry logic

**Tasks**:

1. Configure APScheduler with WITA timezone (UTC+8)
2. Implement daily_report_job() that triggers at 24:00 WITA
3. Write tests for report generation (mock current time)
4. Implement retry logic (5-minute intervals, max 30 minutes per FR-018)
5. Add transaction counter reset at 00:01 WITA (FR-019)
6. Implement manual report generation via /report [YYYY-MM-DD]
7. Add critical error notification on report delivery failure (FR-030)
8. Test timezone edge cases (23:59:59 transactions included in current day)

**Deliverables**: Working automated reports at 24:00 WITA, retry mechanism, counter reset, manual report recovery

---

### Phase 8: Testing & Quality Assurance

**Duration**: 4-5 days  
**Objective**: Achieve ≥80% coverage, validate all requirements, performance testing

**Tasks**:

1. Write missing unit tests to reach 80% coverage
2. Ensure 100% coverage for financial calculation functions
3. Write integration tests for all database operations
4. Create E2E tests for all 6 user stories from spec
5. Performance testing: 500 transactions/day load simulation
6. Concurrent user testing: 20 simultaneous users
7. Test duplicate detection logic (60-second window)
8. Test WITA timezone accuracy across DST boundaries (WITA has no DST)
9. Security testing: SQL injection, input validation, rate limiting
10. Test data retention policy (archive simulation)

**Deliverables**: Test suite with ≥80% coverage, performance benchmarks meeting SLOs, all user stories validated

---

### Phase 9: Deployment & DevOps

**Duration**: 3 days  
**Objective**: Production deployment, monitoring setup, backup configuration

**Tasks**:

1. Create production Dockerfile (multi-stage build)
2. Set up PostgreSQL production instance with backups
3. Configure systemd service for bot auto-restart
4. Set up log aggregation (ELK stack or CloudWatch)
5. Configure monitoring (Prometheus + Grafana or DataDog)
6. Implement health check endpoint
7. Create database backup script (daily automated backups)
8. Document deployment procedure in README
9. Set up environment-specific configs (dev/staging/prod)
10. Create runbook for common operations (add user, view logs, rollback)

**Deliverables**: Production deployment, monitoring dashboards, automated backups, operational runbook

---

### Phase 10: Documentation & Handoff

**Duration**: 2 days  
**Objective**: Complete user documentation, admin guide, architecture docs

**Tasks**:

1. Write user guide: How to use bot commands
2. Write admin guide: User approval, manual reports, troubleshooting
3. Document architecture decisions (ADRs)
4. Create API reference for all bot commands
5. Document database schema with ER diagram
6. Write contribution guide for future developers
7. Create changelog and versioning strategy
8. Document known limitations (Fira Code, Telegram rate limits)

**Deliverables**: Complete documentation set, user and admin guides, architecture documentation

## Timeline Summary

**Total Duration**: 38-47 days (7-9 weeks)

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 0: Research | 2-3 days | None |
| Phase 1: Design | 3-4 days | Phase 0 |
| Phase 2: Setup | 2 days | Phase 1 |
| Phase 3: Database | 3-4 days | Phase 2 |
| Phase 4: Services | 5-6 days | Phase 3 |
| Phase 5: Bot Handlers | 6-7 days | Phase 4 |
| Phase 6: Formatting | 3-4 days | Phase 5 |
| Phase 7: Scheduling | 3 days | Phase 6 |
| Phase 8: Testing | 4-5 days | Phase 7 |
| Phase 9: Deployment | 3 days | Phase 8 |
| Phase 10: Documentation | 2 days | Phase 9 |

**Critical Path**: Phases 0 → 1 → 2 → 3 → 4 → 5 → 7 → 8 → 9 (core functionality)  
**Parallel Opportunities**: Phase 6 (Formatting) can partially overlap with Phase 5, Phase 10 (Docs) can partially overlap with Phase 9

## Risks & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Telegram API rate limits (30 msg/sec) | Medium | High | Implement message queue, batch notifications, add exponential backoff |
| Timezone calculation errors | Low | Critical | Use pytz library, extensive testing, UTC storage with WITA display only |
| PostgreSQL performance degradation | Low | Medium | Proper indexing, query optimization, connection pooling, archive old data |
| Concurrent transaction conflicts | Medium | High | Use database transactions (ACID), implement optimistic locking |
| Data loss during crashes | Low | Critical | Database transactions, automated backups, WAL archiving |
| User input parsing errors | High | Low | Comprehensive validation, clear error messages, fuzzy amount parsing |
| WITA scheduling drift | Low | Medium | NTP time sync on server, monitor scheduler accuracy, alert on drift |
| Test coverage gaps | Medium | Medium | Mandatory 80% coverage gate in CI, focus on financial logic 100% |

## Next Steps

1. **IMMEDIATE**: Run `/speckit.plan` Phase 0 to generate research.md
2. **Phase 0 Output**: Technology validation, best practices documentation
3. **Phase 1 Output**: Generate data-model.md, contracts/, quickstart.md
4. **Phase 1 Final**: Run update-agent-context.sh to propagate technology choices
5. **Phase 2**: Use `/speckit.tasks` to generate detailed task breakdown with dependencies
6. **Phase 3+**: Execute implementation phases following TDD workflow per Constitution Principle II
