# Feature Specification: Telegram Cash Flow Management Bot

**Feature Branch**: `001-cashflow-bot`  
**Created**: 2025-12-18  
**Status**: Draft  
**Input**: User description: "Telegram bot system for company cash flow management with automated daily reports at 24:00 WITA"

## Clarifications

### Session 2025-12-18

- Q: How should user authentication and whitelist management work for bot access? → A: Semi-automated with admin approval - Users send `/register` command with employee ID/code, administrator approves via bot command, user automatically added to whitelist
- Q: Should income transactions have category classification like expenses? → A: Single category - All income recorded as generic "Income" with no subcategories, rely on description field for differentiation
- Q: How should users input amount and description when using keyboard buttons instead of commands? → A: Sequential prompts - Bot first asks "Enter amount:", waits for numeric input, then asks "Enter description (optional):"
- Q: What events should trigger immediate management notifications beyond the daily report? → A: Critical errors only - Notify management immediately for: report delivery failures after retry exhaustion, authentication failures (3+ attempts), system downtime >5 minutes
- Q: What is the long-term data retention policy beyond the 90-day minimum? → A: One year retention - Keep full transaction detail for 1 year, then archive to compressed storage (read-only access for audits), delete after 3 years

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record Income Transaction (Priority: P1)

Company staff can quickly record cash income throughout the business day using simple bot commands or inline keyboard buttons, with immediate visual confirmation of the recorded transaction.

**Why this priority**: Recording income is the most fundamental business operation. Without income tracking, the entire cash flow system provides no value. This is the minimum viable feature that demonstrates core functionality.

**Independent Test**: Can be fully tested by sending an income transaction command (e.g., "/income 500000 Client payment") and receiving a formatted confirmation message with transaction details. Delivers immediate value by creating a digital record of cash inflows.

**Acceptance Scenarios**:

1. **Given** staff opens Telegram bot, **When** they send `/income 500000 Client payment for Project A`, **Then** bot confirms transaction with formatted message showing amount Rp 500,000, category "Income", description, timestamp, and transaction ID
2. **Given** staff clicks "Record Income" keyboard button, **When** bot prompts "Enter amount:", staff replies "500000", bot prompts "Enter description (optional):", staff replies "Client payment", **Then** bot saves transaction and displays confirmation with all details
3. **Given** staff clicks "Record Income" button and enters amount via sequential prompt, **When** staff skips description prompt by sending empty message or /skip, **Then** bot saves transaction with "No description" default
4. **Given** staff enters income with only amount `/income 750000`, **When** bot processes command, **Then** bot saves with "No description" default
5. **Given** staff enters invalid amount `/income abc`, **When** bot validates input, **Then** bot responds with error message "❌ Invalid amount. Please enter numbers only (e.g., /income 100000 Description)" and provides example

---

### User Story 2 - Record Expense Transaction (Priority: P1)

Company staff can record cash expenses with category selection (operational costs, salaries, supplies, etc.) throughout the day, enabling proper expense categorization for financial analysis.

**Why this priority**: Expense tracking is equally critical as income tracking for cash flow management. Together with US1, this completes the basic transaction recording capability needed for any meaningful financial reporting.

**Independent Test**: Can be fully tested by recording an expense with category selection (e.g., "/expense 250000 Office supplies") and verifying the transaction is saved with correct category classification. Delivers value by tracking cash outflows with categorization.

**Acceptance Scenarios**:

1. **Given** staff wants to record expense, **When** they send `/expense 250000 Office supplies purchase`, **Then** bot presents inline keyboard with expense categories (Operational, Salaries, Supplies, Marketing, Other)
2. **Given** expense categories displayed, **When** staff selects "Supplies" category, **Then** bot confirms transaction with formatted message showing amount Rp 250,000, category "Supplies", description, and transaction ID
3. **Given** staff clicks "💸 Record Expense" keyboard button, **When** bot prompts "Enter amount:", staff replies "250000", bot prompts "Enter description (optional):", staff replies "Office supplies", bot shows category keyboard, staff selects "Supplies", **Then** bot saves and confirms transaction
4. **Given** staff uses quick category command `/expense_supplies 150000 Paper and ink`, **When** bot processes command, **Then** bot saves expense directly to Supplies category without additional prompts
5. **Given** staff enters expense without description `/expense 50000`, **When** category selection completes, **Then** bot saves transaction with "Uncategorized expense" default description

---

### User Story 3 - View Daily Summary On-Demand (Priority: P2)

Staff and management can request current day's cash flow summary at any time to check financial status before the automated evening report.

**Why this priority**: Real-time visibility into daily cash position helps management make informed decisions during business hours. This is secondary to recording capabilities but critical for operational awareness.

**Independent Test**: Can be fully tested by sending `/summary` command at any time during the day and receiving formatted report showing total income, total expenses, net cash flow, and transaction count. Delivers value by providing instant financial snapshot.

**Acceptance Scenarios**:

1. **Given** transactions recorded during the day, **When** user sends `/summary` command, **Then** bot displays formatted daily summary with total income, total expenses, net cash flow (positive/negative indicator), and transaction breakdown by category
2. **Given** no transactions recorded yet, **When** user requests `/summary`, **Then** bot displays "📊 Daily Summary - No transactions recorded today" with zero balances
3. **Given** user requests summary via "📊 Daily Summary" keyboard button, **When** bot processes request, **Then** bot shows identical formatted summary as command-based request
4. **Given** multiple expense categories used, **When** summary generated, **Then** bot groups expenses by category with subtotals and grand total

---

### User Story 4 - Automated Daily Report Delivery (Priority: P2)

Management receives comprehensive daily financial report automatically at 24:00 WITA (midnight Central Indonesia Time) summarizing the day's complete cash flow activity without manual intervention.

**Why this priority**: Automated reporting eliminates manual effort and ensures consistent daily financial oversight. While important for management, the system provides value even without automation if reports can be requested manually (US3).

**Independent Test**: Can be fully tested by configuring scheduled task to trigger at 24:00 WITA, verifying report generation includes all day's transactions, and confirming delivery to designated management chat/group. Delivers value by providing end-of-day financial closure automatically.

**Acceptance Scenarios**:

1. **Given** scheduled task triggers at 24:00 WITA, **When** bot generates daily report, **Then** bot sends comprehensive formatted report to management group with date header, total income, total expenses, net cash flow, category breakdowns, and transaction count
2. **Given** no transactions occurred during the day, **When** midnight report triggers, **Then** bot sends report indicating "No transactions recorded" with zero balances
3. **Given** report generation completes, **When** new day starts (00:01 WITA), **Then** bot resets daily counters and begins tracking new day's transactions
4. **Given** report delivery fails (network issue), **When** bot detects failure, **Then** bot retries delivery every 5 minutes for up to 30 minutes and logs error if all retries fail

---

### User Story 5 - Interactive Inline Keyboard Navigation (Priority: P3)

Users interact with bot through dynamic inline keyboard menus that adapt based on context, reducing need to memorize commands and improving mobile user experience.

**Why this priority**: Enhanced UX improves adoption and efficiency but bot remains functional with command-line interface. This is a polish feature that makes the bot more professional and user-friendly.

**Independent Test**: Can be fully tested by sending `/start` command and navigating through all menu options using only keyboard buttons without typing any commands. Delivers value by improving accessibility and reducing user training requirements.

**Acceptance Scenarios**:

1. **Given** user sends `/start` command, **When** bot displays main menu, **Then** inline keyboard shows buttons: "💰 Record Income", "💸 Record Expense", "📊 Daily Summary", "📋 Transaction History", "⚙️ Settings"
2. **Given** user selects "💸 Record Expense", **When** keyboard updates, **Then** bot shows category selection buttons: "🏢 Operational", "👔 Salaries", "📦 Supplies", "📢 Marketing", "➕ Other", "◀️ Back"
3. **Given** user navigates through menus, **When** user clicks "◀️ Back" button, **Then** bot returns to previous menu level
4. **Given** user completes transaction entry, **When** confirmation displayed, **Then** keyboard automatically returns to main menu with all primary options

---

### User Story 6 - Transaction History and Search (Priority: P3)

Users can view past transactions with filtering options (date range, category, type) to review historical cash flow data and verify previous entries.

**Why this priority**: Historical data access is valuable for auditing and verification but not essential for core cash flow recording. Users can operate effectively with only current-day visibility (US3).

**Independent Test**: Can be fully tested by requesting `/history` command and receiving paginated list of recent transactions with filtering buttons for date and category. Delivers value by enabling data verification and historical analysis.

**Acceptance Scenarios**:

1. **Given** user sends `/history` command, **When** bot retrieves data, **Then** bot displays last 10 transactions with pagination buttons "◀️ Previous" and "Next ▶️"
2. **Given** history displayed, **When** user applies "Today" filter button, **Then** bot shows only current day's transactions
3. **Given** user applies category filter "Supplies", **When** filter activates, **Then** bot displays only transactions in Supplies category across all dates
4. **Given** user requests specific date via `/history 2025-12-15`, **When** bot processes request, **Then** bot displays all transactions from December 15, 2025

---

### Edge Cases

- **What happens when user records transaction exactly at 23:59:59 WITA?** System must include transaction in current day's report generated at 24:00, not next day. Transaction timestamp determines inclusion in daily summary.

- **How does system handle duplicate transaction entries?** System warns user if identical transaction (same amount, description, category) recorded within 60 seconds, asking "Confirm duplicate transaction?" with Yes/No buttons to prevent accidental double-entry.

- **What if automated report fails to send due to network outage?** System implements retry mechanism (5-minute intervals, max 30 minutes) and logs failure. Manual `/report yesterday` command allows recovery of missed reports.

- **How are transactions handled during timezone transitions or DST changes?** System operates exclusively in WITA (UTC+8) with no DST adjustments. All timestamps stored in UTC with WITA display conversion.

- **What happens if user enters extremely large transaction amount (e.g., 999,999,999,999)?** System validates maximum amount of Rp 10,000,000,000 (10 billion) and rejects larger entries with message "Amount exceeds maximum limit. Please verify and re-enter."

- **How does bot handle concurrent transaction entries from multiple users?** System processes each transaction independently with atomic database operations. Each entry receives unique transaction ID and timestamp to prevent conflicts.

- **What if user tries to edit or delete transaction after recording?** Transaction modification not supported in MVP to maintain audit trail integrity. Users can add correcting entry with note referencing original transaction ID.

- **How are permissions managed if multiple staff have bot access?** All authenticated users have equal access to record transactions and view summaries. Role-based permissions (staff vs. management) deferred to future version unless required for security.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept income transaction entries via command format `/income [amount] [description]` with amount as required numeric parameter and description as optional text parameter

- **FR-002**: System MUST accept expense transaction entries via command format `/expense [amount] [description]` and present category selection via inline keyboard with minimum categories: Operational, Salaries, Supplies, Marketing, Other

- **FR-003**: System MUST validate transaction amount input as numeric values only, rejecting non-numeric input with clear error message and usage example

- **FR-004**: System MUST generate unique transaction ID for each recorded entry using timestamp-based sequential format (e.g., TX20251218001)

- **FR-005**: System MUST store transaction data persistently with fields: transaction_id, type (income/expense), amount, category, description, timestamp (UTC), user_id, and status

- **FR-006**: System MUST display transaction confirmation messages in formatted layout with emoji indicators (💰 for income, 💸 for expense), bold headers, and monospace numbers for amounts

- **FR-007**: System MUST calculate daily summary showing total income, total expenses, net cash flow (income - expenses), and transaction count with category breakdowns

- **FR-008**: System MUST provide `/summary` command to generate on-demand daily summary report for current business day (WITA timezone)

- **FR-009**: System MUST execute automated daily report generation at exactly 24:00 WITA (16:00 UTC) using scheduled task mechanism

- **FR-010**: System MUST deliver automated daily report to designated management chat or group with comprehensive formatting including date header, financial totals, and category analysis

- **FR-011**: System MUST implement inline keyboard navigation with main menu, category selection menus, and contextual back buttons

- **FR-012**: System MUST handle keyboard button callbacks with appropriate state management to support multi-step transaction entry flows

- **FR-013**: System MUST provide `/start` command that displays welcome message and main menu keyboard with primary bot functions

- **FR-014**: System MUST provide `/help` command that displays command reference with syntax examples and feature descriptions

- **FR-015**: System MUST implement transaction history retrieval via `/history` command with pagination (10 transactions per page)

- **FR-016**: System MUST support date filtering for history queries via `/history [YYYY-MM-DD]` format

- **FR-017**: System MUST format all currency amounts using Indonesian Rupiah convention with "Rp" prefix and thousand separators (e.g., Rp 1,500,000)

- **FR-018**: System MUST implement retry mechanism for failed report delivery with 5-minute intervals for maximum 30 minutes

- **FR-019**: System MUST reset daily transaction counters at 00:01 WITA each day to begin new business day tracking

- **FR-020**: System MUST authenticate users via Telegram user ID to restrict access to authorized company staff only

- **FR-021**: System MUST log all transaction activities including user ID, timestamp, action type, and success/failure status for audit purposes

- **FR-022**: System MUST validate maximum transaction amount of Rp 10,000,000,000 and reject entries exceeding this limit

- **FR-023**: System MUST detect potential duplicate transactions (identical amount, description, category within 60 seconds) and prompt user for confirmation

- **FR-024**: System MUST support manual report generation for previous dates via `/report [YYYY-MM-DD]` command for recovery of missed automated reports

- **FR-025**: System MUST display user-friendly error messages for all validation failures with actionable guidance and command examples

- **FR-026**: System MUST provide `/register` command allowing new users to request access by submitting employee ID or registration code for administrator approval

- **FR-027**: System MUST provide administrator command `/approve [user_id]` to whitelist approved users, automatically enabling their access to bot functions

- **FR-028**: System MUST categorize all income transactions under single "Income" category, using description field for income source differentiation

- **FR-029**: System MUST implement sequential prompt flow for keyboard-based transaction entry: first prompt "Enter amount:", validate numeric input, then prompt "Enter description (optional):" with skip capability

- **FR-030**: System MUST send immediate notifications to management for critical errors: report delivery failures after full retry cycle, 3+ authentication failures from same user within 1 hour, system downtime exceeding 5 minutes

- **FR-031**: System MUST retain full transaction detail for 1 year, archive to compressed read-only storage after 1 year, and permanently delete archived data after 3 years total retention

### Key Entities

- **Transaction**: Core financial record containing unique identifier, transaction type (income/expense), monetary amount in Rupiah, category classification, descriptive text, timestamp in UTC with WITA display, recording user identifier, and transaction status

- **User**: Company staff member authorized to use bot, identified by Telegram user ID, with associated metadata including display name, authorization status (pending/approved/rejected), role designation (staff/management/admin), employee ID, and registration timestamp

- **Daily Summary**: Calculated aggregate report containing summary date, total income amount, total expense amount, net cash flow (calculated), transaction count, and category-wise breakdowns

- **Category**: Expense classification type with identifier, display name, emoji icon, and sort order for consistent presentation

- **Report**: Formatted financial document containing report date, generation timestamp, delivery status, recipient list, and associated daily summary data

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Staff can record single transaction (income or expense) in under 30 seconds from opening Telegram to receiving confirmation message

- **SC-002**: System processes transaction entries and generates confirmation within 2 seconds under normal load conditions (up to 50 concurrent users)

- **SC-003**: Daily reports generate and deliver to management within 60 seconds of 24:00 WITA trigger time with 99% success rate

- **SC-004**: Users successfully complete transaction recording on first attempt without errors in 90% of cases (measured by ratio of successful transactions to total attempts)

- **SC-005**: Management receives accurate daily reports with zero calculation errors (total income + total expenses = correct net cash flow) in 100% of generated reports

- **SC-006**: System handles minimum 200 transactions per day across multiple users without performance degradation

- **SC-007**: Bot maintains 99.5% uptime during business hours (08:00-22:00 WITA) measured monthly

- **SC-008**: Error messages provide sufficient clarity that 80% of users can self-correct input errors without external help (measured by successful retry after error)

- **SC-009**: Transaction data persists reliably with zero data loss (all recorded transactions retrievable in history for minimum 90 days)

- **SC-010**: Inline keyboard navigation reduces command memorization requirements such that new users can record first transaction within 2 minutes of `/start` command without training

## Assumptions *(if applicable)*

- Company staff have existing Telegram accounts and basic familiarity with Telegram messaging
- Management has designated Telegram group or chat for receiving automated daily reports
- Internet connectivity available throughout business day for real-time transaction recording
- Server hosting bot has reliable time synchronization for accurate WITA scheduling
- Company requires financial data retention for 1 year active access, with 3-year total retention for compliance
- Company has designated administrator(s) responsible for approving user registration requests
- Income source differentiation via description field is sufficient (no subcategories needed for MVP)
- Transaction recording volume will not exceed 500 transactions per day (average company size)
- All company staff requiring access can be identified and whitelisted via Telegram user ID
- Company primarily operates in Indonesian Rupiah currency (multi-currency not required)
- Management prefers comprehensive daily reports over weekly or monthly summaries
- Mobile device usage expected (bot UI optimized for smartphone screens)

## Non-Functional Requirements *(if applicable)*

### Performance

- Transaction confirmation response time: <2 seconds (95th percentile)
- Daily summary generation time: <5 seconds for up to 500 transactions
- History query response time: <3 seconds for paginated results (active data only, archived data may take up to 10 seconds)
- Report generation and delivery: <60 seconds from trigger

### Scalability

- Support minimum 20 concurrent authorized users
- Handle up to 500 transactions per business day
- Maintain performance with 1 year of active historical data (approximately 180,000 transactions)
- Archived data (1-3 years old) accessible with degraded performance for audit purposes

### Reliability

- System uptime: 99.5% during business hours (08:00-22:00 WITA)
- Data persistence: Zero transaction data loss
- Report delivery success rate: 99% (with retry mechanism)

### Usability

- Command syntax simplicity: Maximum 3 parameters per command
- Mobile-optimized message formatting: Max 300 characters per message block
- Emoji usage: Consistent icons for transaction types and menu options
- Response clarity: All error messages include corrective action guidance

### Observability

- Critical error notifications: Immediate alerts to management for report delivery failures, repeated authentication failures (3+ attempts/hour), system downtime >5 minutes
- Notification delivery: Telegram messages to management group with severity level, timestamp, error details, and recommended actions

### Security

- User authentication: Semi-automated whitelist with admin approval via `/register` and `/approve` commands
- Data access: Authorized users can view only company-wide data (no personal restrictions in MVP)
- Audit logging: All transactions logged with user ID, timestamp, action type, and registration events
- Data encryption: Telegram's default end-to-end encryption for message delivery

### Maintainability

- Configuration externalization: Report schedule, management chat ID, user whitelist stored in configuration file
- Logging: Structured logs with severity levels (INFO, WARNING, ERROR) for troubleshooting
- Error handling: Graceful degradation with user-friendly messages for all failure scenarios

## Out of Scope *(clarifies boundaries)*

The following features are explicitly excluded from this specification and may be considered for future iterations:

- **Multi-currency support**: Only Indonesian Rupiah (IDR) supported
- **Transaction editing/deletion**: Immutable transactions maintain audit trail integrity
- **Advanced reporting**: Charts, graphs, trend analysis, forecasting deferred
- **Budget tracking**: Budget limits and variance analysis not included
- **Approval workflows**: All transactions recorded immediately without approval steps
- **Multi-company support**: Single company deployment only
- **Mobile app**: Telegram bot interface only (no native mobile application)
- **Export functionality**: Excel/PDF report export not included in MVP
- **Receipt attachment**: Photo/document attachment for transaction receipts deferred
- **Recurring transactions**: Automated recurring expense entries not supported
- **Bank integration**: No automatic bank account synchronization
- **Tax calculations**: Tax computation and reporting not included
- **Role-based access control**: All authenticated users have equal permissions in MVP
- **Custom categories**: Fixed category list (user-defined categories not supported)
- **Multi-language support**: Indonesian/English interface only

## Technical Considerations *(guidance for implementation)*

### Time Zone Handling

System must operate in WITA (Waktu Indonesia Tengah / Central Indonesia Time = UTC+8) with no daylight saving time adjustments. All internal timestamps stored in UTC for consistency with WITA conversion for display and scheduling.

### Scheduling Mechanism

Daily report generation at 24:00 WITA requires robust scheduling solution (cron job, system scheduler, or framework-based task scheduler) with failure recovery and logging capabilities.

### Message Formatting

Telegram supports limited formatting options:
- **Bold**: `*text*` or `**text**`
- *Italic*: `_text_` or `__text__`
- `Monospace`: `` `text` `` or ``` ```text``` ```
- Combinations: `***bold italic***`

Custom fonts beyond these options not supported. Compact layouts achieved through strategic emoji placement and formatting combinations.

### Inline Keyboard Design

Keyboards are context-sensitive and stateful:
- Main menu persistent across sessions
- Category selection triggered by expense entry
- Navigation breadcrumb via back buttons
- Callback data payloads identify button actions

### Data Validation Strategy

Multi-layer validation:
1. Input format validation (numeric amount, date format)
2. Business rule validation (amount limits, duplicate detection)
3. User-friendly error messages with examples
4. Silent handling of edge cases where appropriate

### Duplicate Detection Logic

Duplicate defined as:
- Identical amount (exact match)
- Identical description (case-insensitive)
- Same category
- Within 60-second time window
- Same user ID

### Scalability Considerations

While MVP targets small company usage (20 users, 500 daily transactions), architecture should support:
- Database indexing on frequently queried fields (date, user_id, category)
- Pagination for history queries to limit memory usage
- Asynchronous report generation to prevent blocking

### Error Recovery

Critical failure scenarios:
- Network interruption during transaction save: Implement transaction rollback/retry
- Report delivery failure: Retry mechanism with exponential backoff
- Database unavailability: Queue transactions in memory with persistent fallback
- Bot API rate limiting: Implement request throttling and retry queue
