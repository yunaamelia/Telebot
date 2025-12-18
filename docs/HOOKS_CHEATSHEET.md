# Git Hooks - Quick Reference Card

## 🚀 Installation (Run Once)

```bash
make install-hooks
```

## 💻 Daily Usage

| Action | Command | When |
|--------|---------|------|
| Commit code | `git commit -m "feat: description"` | Auto-runs pre-commit |
| Push code | `git push` | Auto-runs pre-push + tests |
| Format code | `make format` | Before commit |
| Run all checks | `pre-commit run --all-files` | Manual check |
| Deploy | `./scripts/preflight.sh` | Before deployment |

## 📝 Commit Message Format

```
<type>(<scope>): <subject>

feat(auth): add user login
fix(api): correct timezone bug
docs(hooks): update guide
test(models): add User tests
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 🔧 Common Commands

```bash
# Development
make test              # Run tests
make coverage          # Coverage report
make lint              # Run linters
make format            # Auto-format

# Hooks
make install-hooks     # Install hooks
pre-commit run --all-files  # Run all checks
SKIP=mypy git commit   # Skip specific check

# Deployment
./scripts/preflight.sh # Pre-deployment check
make build             # Build Docker image
```

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| Hook too slow | `SKIP=mypy,pytest git commit` |
| Hook false positive | Update baseline: `detect-secrets scan --baseline .secrets.baseline` |
| Format conflict | Run: `make format` then `make lint` |
| Hook not running | `pre-commit install --install-hooks` |

## 📚 Documentation

- **Quick Start**: `docs/HOOKS_QUICKSTART.md`
- **Full Reference**: `docs/HOOKS.md`
- **All Docs**: `docs/README.md`

## 🆘 Emergency Bypass (Use Sparingly!)

```bash
# Skip ALL hooks (emergency only!)
git commit --no-verify -m "emergency: critical fix"
```

## ✅ Quality Checklist

Before pushing:

- [ ] Code formatted (`make format`)
- [ ] Tests pass (`make test`)
- [ ] Coverage ≥80% (`make coverage`)
- [ ] No linting errors (`make lint`)
- [ ] Commit message follows format

Before deploying:

- [ ] Pre-flight passed (`./scripts/preflight.sh`)
- [ ] All tests green
- [ ] .env configured
- [ ] Migrations applied

---
**Quick Help**: Run `make help` for all commands
