# Quick Setup Guide - Git Hooks & Quality Checks

## 🚀 Quick Start (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements-dev.txt

# 2. Install all hooks
make install-hooks
# or manually:
pre-commit install --install-hooks

# 3. Verify installation
pre-commit run --all-files
```

## 📋 Complete Hook List

| Hook Type | When | What | Speed |
|-----------|------|------|-------|
| **pre-commit** | Before commit | Format, lint, security | ⚡ Fast |
| **pre-push** | Before push | Tests, coverage, type-check | 🐌 Slow |
| **commit-msg** | On commit message | Validate format | ⚡ Instant |
| **pre-merge-commit** | Before merge | Same as pre-commit | ⚡ Fast |
| **post-merge** | After merge/pull | Update deps, notify | ⚡ Fast |

## 🔨 Pre-commit Hooks (Runs on Every Commit)

### File Checks

- ✅ Remove trailing whitespace
- ✅ Add EOF newline
- ✅ Fix line endings (LF)
- ✅ Check file size (<500KB)
- ✅ Detect merge conflicts

### Python Quality

- ✅ Syntax validation (check-ast)
- ✅ Import sorting (reorder-python-imports)
- ✅ Code formatting (Black)
- ✅ Linting (Flake8 + plugins)
- ✅ No debug statements
- ✅ Docstring validation

### Security

- ✅ Detect private keys
- ✅ Scan for secrets (detect-secrets)
- ✅ Security linting (Bandit)

### Config Files

- ✅ YAML syntax
- ✅ JSON syntax
- ✅ TOML syntax
- ✅ Markdown linting

## 🧪 Pre-push Hooks (Runs on Push)

- 🧪 Full test suite
- 📊 Coverage check (≥80%)
- 🔍 Type checking (mypy)

## 📝 Commit Message Format

Uses [Conventional Commits](https://www.conventionalcommits.org/):

```bash
<type>(<scope>): <subject>

# Types:
feat     # New feature
fix      # Bug fix
docs     # Documentation
style    # Formatting
refactor # Code restructuring
test     # Adding tests
chore    # Maintenance

# Examples:
feat(auth): add user registration
fix(api): correct timezone handling
docs(hooks): update setup guide
test(models): add User model tests
```

## 🛠️ Custom Scripts

| Script | Purpose | When to Run |
|--------|---------|-------------|
| `preflight.sh` | Complete deployment check | Before deploy |
| `pre-build.sh` | Docker build validation | Before `docker build` |
| `pre-push.sh` | Test & coverage | Automatic on push |
| `post-merge.sh` | Update after merge | Automatic after merge |
| `check_env_example.py` | Validate .env.example | On commit |
| `check_todos.py` | TODOs have tickets | On commit |

## 💡 Common Commands

```bash
# Run all checks manually
pre-commit run --all-files

# Run specific check
pre-commit run black --all-files
pre-commit run flake8 --all-files

# Update hooks to latest versions
pre-commit autoupdate

# Skip hooks (emergency only!)
git commit --no-verify

# Skip specific hooks
SKIP=mypy,pytest-coverage git commit -m "fix: urgent"
```

## 🔧 Using Make Commands

```bash
make help              # Show all available commands
make install-hooks     # Install all git hooks
make test              # Run tests
make coverage          # Run with coverage report
make lint              # Run all linters
make format            # Format code
make security          # Security checks
make preflight         # Pre-deployment checks
make setup             # Complete project setup
```

## 🐛 Troubleshooting

### Hook fails to run

```bash
# Re-install hooks
pre-commit uninstall
pre-commit install --install-hooks
```

### Slow hook execution

```bash
# Skip slow checks during development
export SKIP=mypy,pytest-coverage
git commit -m "fix: quick iteration"
```

### False positive in secret detection

```bash
# Update baseline
detect-secrets scan --baseline .secrets.baseline
git add .secrets.baseline
```

### Import/formatting conflicts

```bash
# Run formatters in order:
isort src/              # 1. Sort imports
black src/              # 2. Format code
flake8 src/             # 3. Check linting
```

## 📚 Full Documentation

See [docs/HOOKS.md](../docs/HOOKS.md) for complete documentation.

## ✅ Verification

After setup, verify everything works:

```bash
# 1. Check hooks are installed
ls -la .git/hooks/

# 2. Run all checks
pre-commit run --all-files

# 3. Test commit (will be rejected if invalid)
git commit --allow-empty -m "test commit"

# 4. Run preflight check
./scripts/preflight.sh
```

Expected output: ✅ All checks pass

## 🎯 Best Practices

1. **Commit often** - Small commits are easier to review
2. **Read errors** - Don't bypass without understanding
3. **Format first** - Run `make format` before committing
4. **Test locally** - Don't rely on CI to catch issues
5. **Update regularly** - Run `pre-commit autoupdate` monthly

## 🆘 Need Help?

- Read error messages carefully
- Check [docs/HOOKS.md](../docs/HOOKS.md)
- Run failing check manually for details
- Ask team before using `--no-verify`

---

**Remember**: Hooks catch bugs early. Bypassing them creates technical debt!
