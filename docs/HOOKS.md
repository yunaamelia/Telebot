# Git Hooks & Quality Assurance

Comprehensive pre-commit hooks dan quality checks untuk Telegram Cash Flow Bot.

## 🎯 Overview

Project ini menggunakan multiple hooks untuk memastikan kualitas kode:

- **Pre-commit**: Formatting, linting, security checks
- **Pre-push**: Testing, coverage verification
- **Commit-msg**: Conventional commits validation
- **Pre-build**: Docker build validation
- **Pre-flight**: Deployment readiness checks

## 📦 Installation

### 1. Install Dependencies

```bash
# Install pre-commit
pip install pre-commit

# Install development dependencies
pip install -r requirements-dev.txt
```

### 2. Install Pre-commit Hooks

```bash
# Install all hooks (pre-commit, pre-push, commit-msg)
pre-commit install --install-hooks

# Install specific hook type
pre-commit install --hook-type pre-commit
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg
```

### 3. Optional: Install Custom Hooks

```bash
# Post-merge hook
ln -sf ../../scripts/post-merge.sh .git/hooks/post-merge
```

## 🔍 Hook Types

### Pre-commit (Fast Checks)

Runs on every `git commit`:

- ✅ File formatting (trailing whitespace, EOF, line endings)
- ✅ Syntax validation (Python, YAML, JSON, TOML)
- ✅ Import sorting (reorder-python-imports)
- ✅ Code formatting (Black)
- ✅ Linting (Flake8 with plugins)
- ✅ Security scanning (Bandit, detect-secrets)
- ✅ Documentation (pydocstyle)
- ✅ No debug statements (pdb, breakpoint)
- ✅ Migration naming validation

### Pre-push (Comprehensive Checks)

Runs on `git push` - lebih lambat tapi thorough:

- 🧪 Full test suite execution
- 📊 Code coverage (minimum 80%)
- 🔍 Type checking (mypy)
- 🛡️ Security vulnerability scan

### Commit-msg

Validates commit messages follow Conventional Commits:

```bash
# Valid commit messages:
feat(auth): add user registration flow
fix(api): correct timezone handling
docs(readme): update installation instructions
test(models): add User model tests

# Invalid (will be rejected):
# "fixed bug"
# "WIP"
# "some changes"
```

### Pre-build

Run before Docker build:

```bash
./scripts/pre-build.sh
```

Checks:

- Required files present
- No secrets in code
- Dependencies valid
- Linting passes

### Pre-flight

Run before deployment:

```bash
./scripts/preflight.sh
```

Comprehensive checks:

- Environment configuration
- Dependencies compatibility
- Code quality standards
- Database migrations
- Test suite
- Security vulnerabilities
- Docker build success

## 🚀 Usage

### Run All Hooks Manually

```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
pre-commit run flake8 --all-files
pre-commit run pytest-coverage
```

### Skip Hooks (Emergency Only)

```bash
# Skip all hooks (NOT RECOMMENDED)
git commit --no-verify -m "emergency fix"

# Skip specific check with SKIP environment variable
SKIP=flake8,mypy git commit -m "fix: urgent bug fix"
```

### Update Hooks

```bash
# Update to latest versions
pre-commit autoupdate

# Manually update specific hook
# Edit .pre-commit-config.yaml and change 'rev' field
```

## 📋 Configuration Files

| File | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | Main hook configuration |
| `.bandit.yml` | Security linting rules |
| `.yamllint.yml` | YAML formatting rules |
| `.markdownlint.json` | Markdown formatting rules |
| `.secrets.baseline` | Known secrets to ignore |
| `.flake8` | Python linting configuration |
| `pyproject.toml` | Black, pytest, coverage config |

## 🛠️ Custom Hooks

### check-env-example

Validates `.env.example` contains all required settings from `settings.py`.

```bash
python scripts/check_env_example.py
```

### check-todos

Ensures all TODO/FIXME comments have ticket references.

```python
# ✅ Good
# TODO(#123): Implement caching layer
# FIXME[T-456]: Handle edge case for negative amounts

# ❌ Bad
# TODO: fix this later
# FIXME: broken
```

### validate-models

Validates SQLAlchemy models can be imported without errors.

```bash
python -c "from src.bot.models import User, Category, Transaction, DailySummary"
```

## 🔧 Troubleshooting

### Hook Installation Failed

```bash
# Re-install hooks
pre-commit uninstall
pre-commit install --install-hooks

# Check installation
pre-commit --version
```

### Hook Execution is Slow

```bash
# Skip slow hooks during development
export SKIP=mypy,pytest-coverage
git commit -m "fix: quick fix"

# Reset
unset SKIP
```

### Pre-commit Not Found

```bash
# Install in virtual environment
source venv/bin/activate
pip install pre-commit

# Or install globally
pip install --user pre-commit
```

### Formatting Conflicts

If Black and Flake8 disagree:

```bash
# Black takes precedence - format first
black src/
# Then check
flake8 src/
```

### Secret Detection False Positives

Add to `.secrets.baseline`:

```bash
# Scan and update baseline
detect-secrets scan --baseline .secrets.baseline
```

## 📊 Coverage Requirements

- Overall coverage: ≥ 80%
- Financial logic (transaction calculations): 100%
- Core business logic: ≥ 90%
- Utilities and helpers: ≥ 85%

## 🔒 Security Scanning

### Bandit (Static Analysis)

```bash
# Run manually
bandit -r src/ -c .bandit.yml
```

### detect-secrets

```bash
# Scan for new secrets
detect-secrets scan

# Create baseline
detect-secrets scan --baseline .secrets.baseline
```

### Safety (Dependency Vulnerabilities)

```bash
# Check for known vulnerabilities
safety check --json
```

## 🎓 Best Practices

1. **Commit Often**: Small, focused commits are easier to review
2. **Write Tests First**: TDD approach ensures better coverage
3. **Follow Conventions**: Use Conventional Commits format
4. **Review Hook Output**: Don't skip checks without understanding why
5. **Keep Hooks Fast**: Slow checks move to pre-push
6. **Update Regularly**: Run `pre-commit autoupdate` monthly

## 📚 Resources

- [Pre-commit Documentation](https://pre-commit.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Flake8 Rules](https://flake8.pycqa.org/en/latest/user/error-codes.html)
- [Bandit Security Checks](https://bandit.readthedocs.io/)

## 🆘 Getting Help

If hooks are blocking your work:

1. Read the error message carefully
2. Try running the failing check manually
3. Check if it's a false positive (document in config)
4. Ask team for help before using `--no-verify`

**Remember**: Hooks exist to catch bugs early. Bypassing them regularly indicates a process problem, not a hook problem.
