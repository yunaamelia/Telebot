# Tasks: Telegram Cash Flow Management Bot

**Feature**: 001-cashflow-bot  
**Input**: Design documents from `/specs/001-cashflow-bot/`  
**Prerequisites**: ✅ plan.md, ✅ spec.md, ✅ research.md, ✅ data-model.md, ✅ contracts/  
**Generated**: 2025-12-18

**Tests**: Per Constitution Principle II (Test-First Development), tests are MANDATORY for all business logic. Tests must be written BEFORE implementation (TDD workflow: Red → Green → Refactor).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- **File paths**: All paths are absolute from repository root

**Path Conventions** (Single project per plan.md):

- Source code: `src/bot/`, `src/database/`, `src/scheduler/`, `src/config/`
- Tests: `tests/unit/`, `tests/integration/`, `tests/e2e/`
- Migrations: `migrations/`
- Config: `.env.example`, `requirements.txt`, `docker-compose.yml`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure - REQUIRED before any development

- [X] T001 Create project directory structure per plan.md §Project Structure in cashflow-bot/
- [X] T002 Initialize Python 3.11 virtual environment with venv in cashflow-bot/
- [X] T003 [P] Create requirements.txt with python-telegram-bot==20.7, SQLAlchemy==2.0.25, APScheduler==3.10.4, pytz==2023.3
- [X] T004 [P] Create requirements-dev.txt with pytest==7.4.3, pytest-asyncio==0.21.1, pytest-cov==4.1.0, pylint==3.0.3, flake8==6.1.0
- [X] T005 [P] Configure .gitignore for Python (venv/, **pycache**/, .env, *.pyc)
- [X] T006 [P] Create .env.example with TELEGRAM_BOT_TOKEN, DATABASE_URL, MANAGEMENT_CHAT_ID, TIMEZONE=Asia/Makassar
- [X] T007 [P] Configure .pylintrc with complexity limit ≤15, function length ≤50 LOC per constitution
- [X] T008 [P] Configure pytest.ini with asyncio_mode=auto, testpaths=tests, coverage ≥80%
- [X] T009 Create docker-compose.yml with PostgreSQL 15.5 service and bot service definitions
- [X] T010 Create Dockerfile with multi-stage build (builder + runtime) per plan.md §Phase 9
- [X] T011 [P] Initialize Alembic with alembic init migrations/ for database migrations
- [X] T012 [P] Create README.md with project overview, quick start, development setup
- [X] T013 [P] Setup GitHub Actions workflow in .github/workflows/ci.yml for lint, test, coverage gates

**Checkpoint**: ✅ Project structure ready - can now setup foundational infrastructure

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database Foundation

- [X] T014 Create base database connection in src/database/connection.py with PostgreSQL connection pooling
- [X] T015 Create session management in src/database/session.py with SQLAlchemy async session factory
- [X] T016 [P] Create users table migration in migrations/versions/001_create_users.py per data-model.md
- [X] T017 [P] Create categories table migration in migrations/versions/002_create_categories.py with seed data
- [X] T018 Create transactions table migration in migrations/versions/003_create_transactions.py with all indexes
- [X] T019 Create daily_summaries table migration in migrations/versions/004_create_daily_summaries.py with JSONB support
- [X] T020 Seed categories with INSERT statements in migration: Income, Operational, Salaries, Supplies, Marketing, Other

### Model Layer (Domain Objects)

- [X] T021 [P] Create User model in src/bot/models/user.py with SQLAlchemy ORM per data-model.md §User Model
- [X] T022 [P] Create Category model in src/bot/models/category.py with CHECK constraints
- [X] T023 [P] Create Transaction model in src/bot/models/transaction.py with all validation constraints
- [X] T024 [P] Create DailySummary model in src/bot/models/report.py with computed net_cash_flow column
- [X] T025 Create **init**.py in src/bot/models/ to export all models

### Repository Layer (Data Access)

- [X] T026 [P] Create UserRepository in src/bot/repositories/user_repository.py with CRUD operations
- [X] T027 [P] Create CategoryRepository in src/bot/repositories/category_repository.py with caching
- [X] T028 Create TransactionRepository in src/bot/repositories/transaction_repository.py with duplicate detection query
- [X] T029 Create **init**.py in src/bot/repositories/ to export all repositories

### Core Utilities

- [X] T030 [P] Create currency formatter in src/bot/utils/formatters.py with Rp prefix and thousand separators per FR-017
- [X] T031 [P] Create WITA timezone handler in src/bot/utils/timezone.py with UTC↔WITA conversion
- [X] T032 [P] Create amount validator in src/bot/utils/validators.py with numeric parsing, max 10B validation per FR-022
- [X] T033 Create transaction ID generator in src/bot/utils/formatters.py with TX20251218001 format per FR-004
- [X] T034 Create **init**.py in src/bot/utils/ to export all utilities

### Configuration & Logging

- [X] T035 Create Pydantic settings in src/config/settings.py with environment variable loading
- [X] T036 [P] Configure structured logging in src/config/logging.py with JSON format, correlation IDs per constitution
- [X] T037 Create **init**.py in src/config/ to export settings and logging

**Checkpoint**: ✅ Foundation complete - User story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Record Income Transaction (Priority: P1) 🎯 MVP

**Goal**: Company staff can quickly record cash income with immediate confirmation

**Independent Test**: Send `/income 500000 Client payment` → Receive formatted confirmation with transaction ID, amount Rp 500,000, timestamp

**Why P1**: Most fundamental business operation - without income tracking, no value delivered

### Tests for User Story 1 (TDD: Write FIRST, ensure they FAIL)

- [X] T038 [P] [US1] Unit test for amount parsing in tests/unit/utils/test_validators.py (test cases: "500000", "500,000", "500.000", "abc")
- [X] T039 [P] [US1] Unit test for transaction ID generation in tests/unit/utils/test_formatters.py (verify TX20251218001 format)
- [X] T040 [P] [US1] Unit test for income service in tests/unit/services/test_transaction_service.py (test record_income with valid/invalid amounts)
- [X] T041 [US1] Integration test for income recording in tests/integration/test_income_transaction.py with Testcontainers PostgreSQL
- [X] T042 [US1] E2E test for /income command in tests/e2e/test_income_flow.py with mock Telegram Update

### Implementation for User Story 1

- [X] T043 [P] [US1] Implement TransactionService.record_income() in src/bot/services/transaction_service.py with amount validation
- [X] T044 [P] [US1] Implement NotificationService.send_confirmation() in src/bot/services/notification_service.py with HTML formatting
- [X] T045 [US1] Create income command handler in src/bot/handlers/transaction.py for /income [amount] [description]
- [X] T046 [US1] Create income confirmation message template in contracts/messages.yaml integration (already exists, verify usage)
- [X] T047 [US1] Implement sequential prompt flow for keyboard-based income entry per FR-029 using ConversationHandler
- [X] T048 [US1] Add duplicate detection check in TransactionService with 60-second window query per edge cases
- [X] T049 [US1] Create duplicate confirmation keyboard in src/bot/keyboards/main_menu.py with Yes/No buttons
- [X] T050 [US1] Add error handling for invalid amount with usage example per FR-003 in transaction.py
- [X] T051 [US1] Add logging for income transactions with user_id, timestamp, amount per FR-021

**Checkpoint**: ✅ User Story 1 complete - Can record income transactions independently

---

## Phase 4: User Story 2 - Record Expense Transaction (Priority: P1) 🎯 MVP

**Goal**: Company staff can record cash expenses with category selection

**Independent Test**: Send `/expense 250000 Office supplies` → Category keyboard appears → Select "Supplies" → Receive confirmation

**Why P1**: Equally critical as income - completes basic transaction recording capability

### Tests for User Story 2 (TDD: Write FIRST, ensure they FAIL)

- [X] T052 [P] [US2] Unit test for expense service in tests/unit/services/test_transaction_service.py (test record_expense with categories)
- [X] T053 [P] [US2] Unit test for category keyboard builder in tests/unit/keyboards/test_categories.py
- [X] T054 [US2] Integration test for expense recording in tests/integration/test_expense_transaction.py with category selection
- [X] T055 [US2] E2E test for /expense command in tests/e2e/test_expense_flow.py with category callback

### Implementation for User Story 2

- [ ] T056 [P] [US2] Implement TransactionService.record_expense() in src/bot/services/transaction_service.py
- [ ] T057 [P] [US2] Create category selection keyboard in src/bot/keyboards/categories.py with emoji per data-model.md §categories seed
- [ ] T058 [US2] Create expense command handler in src/bot/handlers/transaction.py for /expense [amount] [description]
- [ ] T059 [US2] Implement category callback handler in src/bot/handlers/keyboard.py for category selection
- [ ] T060 [US2] Create expense confirmation message template usage (verify contracts/messages.yaml)
- [ ] T061 [US2] Implement sequential prompt flow for keyboard-based expense entry with category step
- [ ] T062 [P] [US2] Implement quick category shortcuts in src/bot/handlers/transaction.py (/expense_supplies, /expense_operational, etc.)
- [ ] T063 [US2] Add default description "Uncategorized expense" when skipped per US2 AS5
- [ ] T064 [US2] Add duplicate detection for expense transactions (reuse from US1)
- [ ] T065 [US2] Add error handling with category selection guidance

**Checkpoint**: ✅ User Stories 1 AND 2 complete - Can record both income and expense transactions


---


## Phase 5: User Story 3 - View Daily Summary On-Demand (Priority: P2)

**Goal**: Staff and management can request current day's financial snapshot anytime

**Independent Test**: Send `/summary` → Receive formatted report with total income, expenses, net cash flow, transaction count

**Why P2**: Real-time visibility valuable but secondary to recording capabilities

### Tests for User Story 3 (TDD: Write FIRST, ensure they FAIL)

- [ ] T066 [P] [US3] Unit test for daily summary calculation in tests/unit/services/test_report_service.py
- [ ] T067 [P] [US3] Unit test for net cash flow calculation in tests/unit/services/test_report_service.py (income - expenses)
- [ ] T068 [US3] Integration test for summary generation in tests/integration/test_summary.py with sample transactions
- [ ] T069 [US3] E2E test for /summary command in tests/e2e/test_summary_flow.py

### Implementation for User Story 3

- [ ] T070 [P] [US3] Implement ReportService.generate_daily_summary() in src/bot/services/report_service.py per FR-007
- [ ] T071 [P] [US3] Implement category breakdown aggregation in ReportService with SQL GROUP BY
- [ ] T072 [US3] Create summary command handler in src/bot/handlers/summary.py for /summary
- [ ] T073 [US3] Create summary message formatter in src/bot/utils/formatters.py with emoji, headers, totals
- [ ] T074 [US3] Implement zero-transaction day handling per US3 AS2 with "No transactions recorded" message
- [ ] T075 [US3] Add summary keyboard button in main menu linking to summary handler
- [ ] T076 [US3] Add net cash flow positive/negative indicator (+ green, - red with emoji)
- [ ] T077 [US3] Add transaction count and category subtotals per US3 AS1

**Checkpoint**: ✅ User Stories 1, 2, AND 3 complete - Can record and view daily financial status

---

## Phase 6: User Story 4 - Automated Daily Report Delivery (Priority: P2)

**Goal**: Management receives comprehensive daily report at 24:00 WITA automatically

**Independent Test**: Configure scheduler to trigger at 24:00 WITA → Verify report generated → Confirm delivery to management chat

**Why P2**: Automation valuable but system provides value even with manual reports (US3)

### Tests for User Story 4 (TDD: Write FIRST, ensure they FAIL)

- [ ] T078 [P] [US4] Unit test for scheduler configuration in tests/unit/scheduler/test_daily_report.py with timezone validation
- [ ] T079 [P] [US4] Unit test for report delivery with retry logic in tests/unit/services/test_notification_service.py
- [ ] T080 [US4] Integration test for 24:00 WITA trigger in tests/integration/test_scheduler.py with time mocking
- [ ] T081 [US4] E2E test for full report workflow in tests/e2e/test_daily_report.py

### Implementation for User Story 4

- [ ] T082 [P] [US4] Configure APScheduler in src/scheduler/daily_report.py with WITA timezone per FR-009
- [ ] T083 [P] [US4] Implement daily report job in src/scheduler/daily_report.py calling ReportService
- [ ] T084 [US4] Implement report delivery to management chat in src/bot/services/notification_service.py per FR-010
- [ ] T085 [US4] Create comprehensive report message template with date header, financial totals
- [ ] T086 [US4] Implement retry mechanism in NotificationService with 5-minute intervals, 30-minute max per FR-018
- [ ] T087 [US4] Implement daily counter reset at 00:01 WITA per FR-019 in scheduler
- [ ] T088 [US4] Add critical error notification for report delivery failures per FR-030
- [ ] T089 [US4] Handle zero-transaction days in daily report per US4 AS2
- [ ] T090 [US4] Add timezone edge case handling for 23:59:59 WITA transactions per edge cases
- [ ] T091 [US4] Implement manual report recovery with /report [YYYY-MM-DD] command per FR-024

**Checkpoint**: ✅ User Stories 1-4 complete - Core financial recording and reporting functional with automation

---

## Phase 7: User Story 5 - Interactive Inline Keyboard Navigation (Priority: P3)

**Goal**: Users interact through dynamic keyboard menus reducing command memorization

**Independent Test**: Send `/start` → Navigate all menu options using only keyboard buttons without typing commands

**Why P3**: UX enhancement but bot remains functional with CLI - polish feature

### Tests for User Story 5 (TDD: Write FIRST, ensure they FAIL)

- [ ] T092 [P] [US5] Unit test for main menu keyboard builder in tests/unit/keyboards/test_main_menu.py
- [ ] T093 [P] [US5] Unit test for keyboard navigation state management in tests/unit/handlers/test_keyboard.py
- [ ] T094 [US5] Integration test for keyboard navigation flow in tests/integration/test_keyboard_navigation.py
- [ ] T095 [US5] E2E test for complete /start workflow in tests/e2e/test_start_flow.py

### Implementation for User Story 5

- [ ] T096 [P] [US5] Create main menu keyboard in src/bot/keyboards/main_menu.py with buttons per US5 AS1
- [ ] T097 [P] [US5] Implement /start command handler in src/bot/handlers/auth.py with welcome message per FR-013
- [ ] T098 [US5] Create keyboard callback routing in src/bot/handlers/keyboard.py for all menu actions
- [ ] T099 [US5] Implement "Record Income" button callback linking to income conversation flow
- [ ] T100 [US5] Implement "Record Expense" button callback linking to expense conversation flow
- [ ] T101 [US5] Implement "Daily Summary" button callback linking to summary handler
- [ ] T102 [US5] Implement "Transaction History" button callback linking to history handler (placeholder for US6)
- [ ] T103 [US5] Implement "Settings" button callback with "Coming soon" message per US5 AS4
- [ ] T104 [US5] Add Back button functionality returning to previous menu level per US5 AS3
- [ ] T105 [US5] Ensure keyboard auto-returns to main menu after transaction confirmation per US5 AS4

**Checkpoint**: ✅ User Stories 1-5 complete - Full keyboard navigation enhancing UX

---

## Phase 8: User Story 6 - Transaction History and Search (Priority: P3)

**Goal**: Users can view past transactions with filtering options

**Independent Test**: Send `/history` → Receive last 10 transactions with pagination → Apply filters → Navigate pages

**Why P3**: Historical access valuable for auditing but not essential for core flow recording

### Tests for User Story 6 (TDD: Write FIRST, ensure they FAIL)

- [ ] T106 [P] [US6] Unit test for pagination logic in tests/unit/repositories/test_transaction_repository.py
- [ ] T107 [P] [US6] Unit test for date filtering in tests/unit/repositories/test_transaction_repository.py
- [ ] T108 [US6] Integration test for history retrieval in tests/integration/test_history.py
- [ ] T109 [US6] E2E test for /history command in tests/e2e/test_history_flow.py with filters

### Implementation for User Story 6

- [ ] T110 [P] [US6] Implement TransactionRepository.get_history() with pagination in src/bot/repositories/transaction_repository.py per FR-015
- [ ] T111 [P] [US6] Implement date filtering in TransactionRepository with YYYY-MM-DD parsing per FR-016
- [ ] T112 [P] [US6] Implement category filtering in TransactionRepository
- [ ] T113 [US6] Create history command handler in src/bot/handlers/history.py for /history [date]
- [ ] T114 [US6] Create pagination keyboard in src/bot/keyboards/main_menu.py with Previous/Next buttons per US6 AS1
- [ ] T115 [US6] Create filter keyboard with Today/Week/Month/All buttons per US6 AS2, AS3
- [ ] T116 [US6] Implement pagination callbacks for page navigation
- [ ] T117 [US6] Implement filter callbacks for date and category filtering
- [ ] T118 [US6] Add history message formatter with transaction list display
- [ ] T119 [US6] Handle empty history with "No transactions found" message
- [ ] T120 [US6] Implement sort order (timestamp DESC - most recent first) per data-model.md

**Checkpoint**: ✅ All 6 User Stories complete - Full feature set delivered

---

## Phase 9: Authentication & User Management (Cross-Cutting)

**Purpose**: User registration and admin approval workflow per FR-026, FR-027

### Tests (TDD: Write FIRST, ensure they FAIL)

- [ ] T121 [P] Unit test for registration workflow in tests/unit/services/test_auth_service.py
- [ ] T122 [P] Unit test for admin approval in tests/unit/services/test_auth_service.py
- [ ] T123 Integration test for /register command in tests/integration/test_registration.py
- [ ] T124 E2E test for complete registration workflow in tests/e2e/test_auth_flow.py

### Implementation

- [ ] T125 [P] Implement AuthService.register_user() in src/bot/services/auth_service.py
- [ ] T126 [P] Implement AuthService.approve_user() in src/bot/services/auth_service.py
- [ ] T127 [P] Implement AuthService.check_authorization() decorator for command handlers
- [ ] T128 Create /register command handler in src/bot/handlers/auth.py
- [ ] T129 Create /approve command handler in src/bot/handlers/auth.py (admin only)
- [ ] T130 Add registration notification to admins with approve button
- [ ] T131 Add authorization check to all transaction/summary/history handlers
- [ ] T132 Add unauthorized access error message per contracts/commands.yaml
- [ ] T133 Add authentication failure notification (3+ attempts) per FR-030

**Checkpoint**: ✅ User management complete - Controlled access to bot functions

---

## Phase 10: Help & Documentation (Cross-Cutting)

**Purpose**: User guidance and command reference per FR-014

### Tests (Optional - documentation focused)

- [ ] T134 [P] Verify /help command displays all commands in tests/e2e/test_help.py

### Implementation

- [ ] T135 [P] Create /help command handler in src/bot/handlers/auth.py
- [ ] T136 Create help message template with command reference and examples per contracts/messages.yaml
- [ ] T137 Add section grouping: Recording, Reports, User Management, General per contracts/commands.yaml

**Checkpoint**: ✅ Help system complete - Users can self-serve command information

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Improvements affecting multiple user stories

### Error Handling & Validation

- [ ] T138 [P] Add global error handler in src/bot/handlers/error.py for uncaught exceptions
- [ ] T139 [P] Implement user-friendly error messages for all validation failures per FR-025
- [ ] T140 Add command usage examples in error messages per FR-025
- [ ] T141 Add maximum amount validation (10 billion) with error message per FR-022

### Performance & Reliability

- [ ] T142 [P] Add database connection pooling configuration in src/database/connection.py
- [ ] T143 [P] Add database indexes verification per data-model.md performance requirements
- [ ] T144 Implement rate limiting handling for Telegram API (30 msg/sec) per plan.md risks
- [ ] T145 Add retry logic for network failures in NotificationService

### Observability

- [ ] T146 [P] Add correlation IDs to all log entries per constitution Principle V
- [ ] T147 [P] Add metrics collection for transaction rates, error rates per plan.md constitution
- [ ] T148 Add critical error alerting to management per FR-030 (report failures, downtime >5min)
- [ ] T149 Add structured audit logging for all transactions per FR-021

### Code Quality

- [ ] T150 [P] Run pylint on all source files and fix issues (complexity ≤15, length ≤50)
- [ ] T151 [P] Run flake8 on all source files and fix formatting
- [ ] T152 Add type hints to all functions per research.md §python-telegram-bot best practices
- [ ] T153 Add docstrings to all public functions with examples

### Testing

- [ ] T154 [P] Verify test coverage ≥80% overall per constitution
- [ ] T155 [P] Verify financial calculations have 100% coverage per constitution
- [ ] T156 Add integration test for WITA timezone edge case (23:59:59) per edge cases
- [ ] T157 Run full E2E test suite and verify all user stories

### Documentation

- [ ] T158 [P] Update README.md with deployment instructions
- [ ] T159 [P] Create CONTRIBUTING.md with development workflow
- [ ] T160 Update quickstart.md with test scenarios validation
- [ ] T161 Add architecture diagram showing all components per plan.md

**Checkpoint**: ✅ Polish complete - Production-ready quality

---

## Phase 12: Deployment Preparation

**Purpose**: Production deployment readiness

- [ ] T162 Create systemd service file in deployment/cashflow-bot.service
- [ ] T163 [P] Configure production environment variables in deployment/.env.production.example
- [ ] T164 [P] Create database backup script in scripts/backup-db.sh
- [ ] T165 Test Docker build and run locally with docker-compose up
- [ ] T166 Create deployment runbook in docs/DEPLOYMENT.md
- [ ] T167 [P] Setup monitoring with health check endpoint (if using web framework)
- [ ] T168 Perform security audit (SQL injection, input validation, rate limiting)
- [ ] T169 Run performance test with 500 transactions/day simulation per plan.md
- [ ] T170 Validate all quickstart.md test scenarios

**Checkpoint**: ✅ Ready for production deployment

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS all user stories
    ↓
    ├── Phase 3 (US1 - Income) ← MVP Start
    ├── Phase 4 (US2 - Expense) ← MVP Critical
    ├── Phase 5 (US3 - Summary) ← Can run parallel
    ├── Phase 6 (US4 - Automated Reports) ← Can run parallel
    ├── Phase 7 (US5 - Keyboards) ← Can run parallel
    └── Phase 8 (US6 - History) ← Can run parallel
    ↓
Phase 9 (Auth) ← Cross-cutting
Phase 10 (Help) ← Cross-cutting
Phase 11 (Polish) ← Depends on all desired user stories
Phase 12 (Deployment) ← Final phase
```

### User Story Dependencies

- **Foundation (Phase 2)**: BLOCKS everything - must complete first
- **US1 (Income P1)**: Can start after Foundation - No dependencies on other stories ✅ MVP
- **US2 (Expense P1)**: Can start after Foundation - Independently testable ✅ MVP
- **US3 (Summary P2)**: Can start after Foundation - Independent (uses TransactionRepository)
- **US4 (Reports P2)**: Can start after Foundation - Independent (reuses US3 summary logic)
- **US5 (Keyboards P3)**: Can start after Foundation - Enhances all stories but independent
- **US6 (History P3)**: Can start after Foundation - Independent

**Recommended MVP**: Phase 1 + Phase 2 + Phase 3 (US1) + Phase 4 (US2) + Phase 9 (Auth) = Basic transaction recording with controlled access

### Within Each User Story

1. **Tests FIRST** (TDD): Write tests, ensure they FAIL
2. **Models**: Create database entities
3. **Services**: Implement business logic
4. **Handlers**: Wire up to Telegram commands/keyboards
5. **Validation**: Add error handling and edge cases
6. **Logging**: Add audit trail
7. **Verify**: Tests now PASS

### Parallel Opportunities

**Setup Phase (All can run in parallel)**:

- T003, T004, T005, T006, T007, T008, T011, T012, T013

**Foundational Phase (Within categories can run in parallel)**:

- Migrations: T016, T017
- Models: T021, T022, T023, T024
- Repositories: T026, T027
- Utilities: T030, T031, T032, T036

**User Stories (Can run in parallel after Foundation)**:

- Different developers can work on US1, US2, US3, US4, US5, US6 simultaneously
- Within each story: All tests marked [P] can run in parallel
- Within each story: All models marked [P] can run in parallel

**Polish Phase (Many can run in parallel)**:

- T138, T139, T142, T143, T146, T147, T150, T151, T154, T155, T158, T159

---

## Parallel Execution Example: User Story 1 (Income Recording)

**Step 1**: Foundation complete ✅

**Step 2**: Parallel test writing (can all start simultaneously):

- Developer A: T038 (amount parsing tests)
- Developer A: T039 (transaction ID tests)
- Developer A: T040 (service tests)
- Developer B: T041 (integration tests)
- Developer B: T042 (E2E tests)

**Step 3**: All tests FAIL ✅ (TDD Red phase)

**Step 4**: Parallel implementation (some can run simultaneously):

- Developer A: T043 (TransactionService)
- Developer A: T044 (NotificationService)
- Developer B: T045 (income handler)
- Developer C: T047 (conversation flow)

**Step 5**: Sequential integration:

- T048 (duplicate detection) - depends on T043
- T049 (duplicate keyboard) - depends on T048
- T050 (error handling) - depends on T045
- T051 (logging) - depends on all above

**Step 6**: All tests PASS ✅ (TDD Green phase)

**Step 7**: Refactor if needed (TDD Refactor phase)

**Total Estimated Time**: 3-4 days with 2-3 developers working in parallel

---

## Implementation Strategy

### MVP-First Approach

**Week 1-2: Foundation**

- Phase 1: Setup (1-2 days)
- Phase 2: Foundational (3-4 days)

**Week 2-3: MVP (P1 Stories)**

- Phase 3: US1 - Income Recording (3-4 days)
- Phase 4: US2 - Expense Recording (3-4 days)
- Phase 9: Authentication (2-3 days)

**Checkpoint**: MVP delivers basic transaction recording with controlled access

**Week 4: P2 Stories**

- Phase 5: US3 - Daily Summary (2-3 days)
- Phase 6: US4 - Automated Reports (3-4 days)

**Checkpoint**: Core financial management complete with automation

**Week 5: P3 Stories (Optional for MVP)**

- Phase 7: US5 - Keyboards (2-3 days)
- Phase 8: US6 - History (2-3 days)

**Week 6-7: Polish & Deployment**

- Phase 10: Help (1 day)
- Phase 11: Polish (3-4 days)
- Phase 12: Deployment (2-3 days)

**Total**: 6-7 weeks end-to-end

### Incremental Delivery

Each user story is independently deployable:

1. Deploy US1 → Staff can record income
2. Deploy US2 → Staff can record income + expenses
3. Deploy US3 → Staff can view daily summary
4. Deploy US4 → Management gets automated reports
5. Deploy US5 → Enhanced UX with keyboards
6. Deploy US6 → Historical data access

### Quality Gates

Before moving to next phase:

- ✅ All tests PASS (TDD Green)
- ✅ Coverage ≥80% (100% for financial logic)
- ✅ Pylint/flake8 clean
- ✅ Independent test criteria met per user story

---

## Summary

**Total Tasks**: 170  
**MVP Tasks**: ~85 (Phase 1-2, 3-4, 9)  
**Test Tasks**: 52 (30% test coverage by task count)  
**Parallelizable Tasks**: 68 (40% can run in parallel)

**User Stories**:

- US1 (Income): 14 tasks (5 tests + 9 implementation)
- US2 (Expense): 14 tasks (4 tests + 10 implementation)
- US3 (Summary): 12 tasks (4 tests + 8 implementation)
- US4 (Reports): 14 tasks (4 tests + 10 implementation)
- US5 (Keyboards): 14 tasks (4 tests + 10 implementation)
- US6 (History): 15 tasks (4 tests + 11 implementation)

**Recommended MVP**: 85 tasks → 6-7 weeks → P1 features + Auth
**Full Feature Set**: 170 tasks → 10-12 weeks → All P1, P2, P3 features

**Success Criteria**: Each user story independently testable and deliverable as incremental value

---

**Generated**: 2025-12-18  
**Ready**: ✅ All tasks structured by user story with clear dependencies  
**Next Step**: Begin Phase 1 - Setup
