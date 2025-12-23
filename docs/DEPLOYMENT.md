# Cash Flow Bot - Deployment Runbook

**Version**: 1.0  
**Last Updated**: 2025-12-23  
**Maintainer**: DevOps Team

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Deployment Steps](#deployment-steps)
4. [Post-Deployment Verification](#post-deployment-verification)
5. [Rollback Procedures](#rollback-procedures)
6. [Monitoring & Alerts](#monitoring--alerts)
7. [Troubleshooting](#troubleshooting)
8. [Maintenance Tasks](#maintenance-tasks)

---

## Prerequisites

### System Requirements

- **OS**: Ubuntu 22.04 LTS or newer
- **CPU**: 2 cores minimum (4 cores recommended)
- **RAM**: 2GB minimum (4GB recommended)
- **Disk**: 20GB minimum (50GB recommended for logs and backups)
- **Network**: Stable internet connection with outbound HTTPS access

### Software Dependencies

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# Install PostgreSQL 15
sudo apt install -y postgresql-15 postgresql-contrib-15

# Install system utilities
sudo apt install -y git curl wget systemd supervisor
```

### Telegram Bot Setup

1. Create bot via @BotFather on Telegram
2. Note down the bot token: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`
3. Get management chat ID using @userinfobot or `/start` command
4. Verify bot can send messages to management chat

### Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE cashflow_db;
CREATE USER cashflow_user WITH ENCRYPTED PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE cashflow_db TO cashflow_user;
ALTER DATABASE cashflow_db OWNER TO cashflow_user;

# Exit psql
\q
```

---

## Pre-Deployment Checklist

### Security

- [ ] Strong passwords generated for database user
- [ ] Telegram bot token obtained and secured
- [ ] Management chat ID verified
- [ ] Firewall rules configured (block PostgreSQL port 5432 from external access)
- [ ] SSH access secured with key-based authentication
- [ ] System packages updated to latest versions

### Infrastructure

- [ ] PostgreSQL service running and accessible
- [ ] Backup storage configured with sufficient space
- [ ] Log rotation configured
- [ ] Monitoring tools installed (optional: Prometheus, Grafana)
- [ ] Alert channels configured (Telegram management chat)

### Code & Configuration

- [ ] Latest code pulled from repository
- [ ] Dependencies installed via requirements.txt
- [ ] `.env` file created from `.env.production.example`
- [ ] All environment variables configured
- [ ] Database migrations tested
- [ ] Unit tests passing (≥80% coverage)
- [ ] Integration tests passing

---

## Deployment Steps

### Step 1: Prepare Deployment User

```bash
# Create dedicated user for the bot
sudo useradd -m -s /bin/bash cashflow
sudo usermod -aG sudo cashflow  # Optional: if user needs sudo access

# Create application directory
sudo mkdir -p /opt/cashflow-bot
sudo chown cashflow:cashflow /opt/cashflow-bot
```

### Step 2: Clone Repository

```bash
# Switch to cashflow user
sudo su - cashflow

# Clone repository
cd /opt/cashflow-bot
git clone https://github.com/your-org/cashflow-bot.git .

# Checkout production branch/tag
git checkout tags/v1.0.0  # Or: git checkout production
```

### Step 3: Setup Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Optional: for testing
```

### Step 4: Configure Environment Variables

```bash
# Copy environment template
cp deployment/.env.production.example .env

# Edit .env file with actual values
nano .env

# Required variables:
# - TELEGRAM_BOT_TOKEN
# - MANAGEMENT_CHAT_ID
# - DATABASE_URL
# - TIMEZONE=Asia/Makassar
# - LOG_LEVEL=INFO

# Secure .env file permissions
chmod 600 .env
```

### Step 5: Initialize Database

```bash
# Run migrations
alembic upgrade head

# Verify tables created
psql postgresql://cashflow_user:password@localhost:5432/cashflow_db -c "\dt"

# Verify seed data (categories)
psql postgresql://cashflow_user:password@localhost:5432/cashflow_db -c "SELECT * FROM categories;"
```

### Step 6: Run Tests

```bash
# Run unit tests
pytest tests/unit/ -v --tb=short

# Run integration tests
pytest tests/integration/ -v --tb=short

# Check coverage
pytest --cov=src --cov-report=term-missing --cov-report=html

# Verify coverage ≥80%
coverage report
```

### Step 7: Install Systemd Service

```bash
# Copy service file
sudo cp deployment/cashflow-bot.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable cashflow-bot.service
```

### Step 8: Start Application

```bash
# Start the service
sudo systemctl start cashflow-bot.service

# Check status
sudo systemctl status cashflow-bot.service

# View logs
sudo journalctl -u cashflow-bot.service -f
```

### Step 9: Setup Database Backup Cron

```bash
# Make backup script executable
chmod +x scripts/backup-db.sh

# Add to crontab (daily at 2:00 AM)
crontab -e

# Add this line:
0 2 * * * /opt/cashflow-bot/scripts/backup-db.sh >> /opt/cashflow-bot/logs/backup.log 2>&1
```

---

## Post-Deployment Verification

### Functional Testing

1. **Bot Availability**

   ```bash
   # Check if bot responds
   # Send /start command via Telegram
   # Expected: Welcome message with main menu
   ```

2. **Record Income Transaction**

   ```bash
   # Command: /income 500000 Test income
   # Expected: Confirmation message with transaction ID
   ```

3. **Record Expense Transaction**

   ```bash
   # Command: /expense 250000 Test expense
   # Expected: Category keyboard appears, confirmation after selection
   ```

4. **Daily Summary**

   ```bash
   # Command: /summary
   # Expected: Formatted summary with totals and category breakdown
   ```

5. **Transaction History**

   ```bash
   # Command: /history
   # Expected: List of recent transactions with pagination
   ```

### Database Verification

```bash
# Check database connection
psql $DATABASE_URL -c "SELECT COUNT(*) FROM users;"

# Verify transactions recorded
psql $DATABASE_URL -c "SELECT * FROM transactions ORDER BY created_at DESC LIMIT 5;"

# Check categories seeded
psql $DATABASE_URL -c "SELECT * FROM categories;"
```

### Log Verification

```bash
# Check application logs
tail -f /opt/cashflow-bot/logs/cashflow-bot.log

# Check for errors
grep -i "error" /opt/cashflow-bot/logs/cashflow-bot.log

# Check systemd logs
journalctl -u cashflow-bot.service --since "1 hour ago"
```

### Performance Metrics

```bash
# Check service resource usage
systemctl status cashflow-bot.service

# Monitor CPU and memory
top -p $(pgrep -f "python.*main.py")

# Check database connections
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='cashflow_db';"
```

### Scheduled Tasks

```bash
# Verify scheduler is running
grep -i "scheduler" /opt/cashflow-bot/logs/cashflow-bot.log

# Check daily report schedule (should run at 00:00 WITA)
# Wait until 00:00 WITA and verify report delivery to management chat

# Verify backup cron job
crontab -l | grep backup-db.sh
```

---

## Rollback Procedures

### Quick Rollback (Service Level)

```bash
# Stop current service
sudo systemctl stop cashflow-bot.service

# Switch to previous version
cd /opt/cashflow-bot
git checkout tags/v0.9.0  # Previous stable version

# Restart service
sudo systemctl start cashflow-bot.service

# Verify rollback
sudo systemctl status cashflow-bot.service
```

### Database Rollback

```bash
# Identify target migration version
alembic history

# Rollback to specific version
alembic downgrade <revision_id>

# Or rollback one version
alembic downgrade -1

# Verify database state
psql $DATABASE_URL -c "\dt"
```

### Full System Rollback

```bash
# 1. Stop service
sudo systemctl stop cashflow-bot.service

# 2. Restore database from backup
psql $DATABASE_URL < /opt/cashflow-bot/backups/cashflow_backup_YYYYMMDD_HHMMSS.sql

# 3. Checkout previous code version
cd /opt/cashflow-bot
git checkout tags/v0.9.0

# 4. Reinstall dependencies if needed
source venv/bin/activate
pip install -r requirements.txt

# 5. Restart service
sudo systemctl start cashflow-bot.service

# 6. Notify management
# Send manual notification via Telegram about rollback
```

---

## Monitoring & Alerts

### Health Checks

```bash
# Check service health
curl -f http://localhost:8000/health || echo "Service unhealthy"

# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;" || echo "Database unreachable"

# Check bot API connectivity
curl -s https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe
```

### Log Monitoring

```bash
# Real-time error monitoring
tail -f /opt/cashflow-bot/logs/cashflow-bot.log | grep -i "error\|critical"

# Check for specific errors
grep -i "database" /opt/cashflow-bot/logs/cashflow-bot.log | grep -i "error"

# Count errors in last hour
journalctl -u cashflow-bot.service --since "1 hour ago" | grep -c "ERROR"
```

### Alerting Configuration

Critical alerts are automatically sent to management chat:

- Report delivery failures
- Database connection errors
- Bot downtime >5 minutes
- Authentication failures (≥3 attempts)
- Backup failures

### Manual Alert Testing

```bash
# Test notification to management chat
curl -X POST "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" \
  -d "chat_id=$MANAGEMENT_CHAT_ID" \
  -d "text=🔔 Test Alert: Deployment completed successfully" \
  -d "parse_mode=HTML"
```

---

## Troubleshooting

### Bot Not Responding

**Symptoms**: Bot doesn't reply to commands

**Diagnosis**:

```bash
# Check if service is running
sudo systemctl status cashflow-bot.service

# Check logs for errors
sudo journalctl -u cashflow-bot.service -n 50

# Test bot token validity
curl https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe
```

**Solutions**:

1. Restart service: `sudo systemctl restart cashflow-bot.service`
2. Verify bot token in `.env`
3. Check internet connectivity
4. Verify Telegram API is accessible

### Database Connection Errors

**Symptoms**: "Could not connect to database" errors

**Diagnosis**:

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection manually
psql $DATABASE_URL -c "SELECT 1;"

# Check connection pool
psql $DATABASE_URL -c "SELECT * FROM pg_stat_activity WHERE datname='cashflow_db';"
```

**Solutions**:

1. Restart PostgreSQL: `sudo systemctl restart postgresql`
2. Verify DATABASE_URL in `.env`
3. Check firewall rules
4. Verify database user permissions

### Scheduler Not Running

**Symptoms**: Daily reports not sent at 24:00 WITA

**Diagnosis**:

```bash
# Check scheduler logs
grep -i "scheduler\|apscheduler" /opt/cashflow-bot/logs/cashflow-bot.log

# Verify timezone configuration
cat .env | grep TIMEZONE
```

**Solutions**:

1. Verify TIMEZONE=Asia/Makassar in `.env`
2. Check system timezone: `timedatectl`
3. Restart service to reload scheduler
4. Manually trigger report: `/report`

### High Memory Usage

**Symptoms**: Service consuming excessive memory

**Diagnosis**:

```bash
# Check memory usage
ps aux | grep "python.*main.py"

# Check database connection leaks
psql $DATABASE_URL -c "SELECT count(*) FROM pg_stat_activity WHERE datname='cashflow_db';"
```

**Solutions**:

1. Restart service: `sudo systemctl restart cashflow-bot.service`
2. Check for memory leaks in logs
3. Reduce DATABASE_POOL_SIZE in `.env`
4. Investigate transaction history queries

---

## Maintenance Tasks

### Daily

- [ ] Monitor service status: `systemctl status cashflow-bot.service`
- [ ] Check error logs: `grep -i error /opt/cashflow-bot/logs/cashflow-bot.log`
- [ ] Verify daily report delivered to management chat

### Weekly

- [ ] Review backup status: `ls -lh /opt/cashflow-bot/backups/`
- [ ] Check disk space: `df -h`
- [ ] Review transaction volume and performance metrics
- [ ] Update system packages: `sudo apt update && sudo apt upgrade`

### Monthly

- [ ] Test database restore from backup
- [ ] Review and rotate logs
- [ ] Audit user access and permissions
- [ ] Update dependencies: `pip list --outdated`
- [ ] Security scan: Run `bandit -r src/`

### Quarterly

- [ ] Full disaster recovery drill
- [ ] Performance benchmarking and optimization
- [ ] Security audit and penetration testing
- [ ] Review and update documentation

---

## Emergency Contacts

- **DevOps Team**: [email/phone]
- **Database Admin**: [email/phone]
- **Management**: [Telegram chat ID in .env]
- **Support Escalation**: [escalation procedure]

---

## Version History

| Version | Date       | Changes                           | Author      |
|---------|------------|-----------------------------------|-------------|
| 1.0     | 2025-12-23 | Initial deployment runbook        | DevOps Team |

---

## Appendix

### Useful Commands

```bash
# Service management
sudo systemctl start cashflow-bot.service
sudo systemctl stop cashflow-bot.service
sudo systemctl restart cashflow-bot.service
sudo systemctl status cashflow-bot.service

# View logs
sudo journalctl -u cashflow-bot.service -f
tail -f /opt/cashflow-bot/logs/cashflow-bot.log

# Database operations
psql $DATABASE_URL
alembic upgrade head
alembic downgrade -1
alembic history

# Backup & Restore
./scripts/backup-db.sh
psql $DATABASE_URL < backup_file.sql

# Health checks
curl http://localhost:8000/health
psql $DATABASE_URL -c "SELECT 1;"
```

### Configuration Files

- Service: `/etc/systemd/system/cashflow-bot.service`
- Environment: `/opt/cashflow-bot/.env`
- Database: `/etc/postgresql/15/main/postgresql.conf`
- Logs: `/opt/cashflow-bot/logs/`
- Backups: `/opt/cashflow-bot/backups/`

---

**Document Status**: ✅ Ready for Production Use  
**Review Date**: 2026-01-23 (Review quarterly)
