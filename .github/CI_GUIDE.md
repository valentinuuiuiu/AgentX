# 🏔️ Rehoboam CI/CD Guide — 2026

## GitHub Actions Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to main, PR, manual | Unit + integration tests |
| `hermes-signals.yml` | Every 15 min, manual | Generate + post trading signals |
| `jules-vps-maintenance.yml` | Every 6 hours, manual | VPS health, git sync, backups |
| `telegram-send.yml` | Manual only | Send custom Telegram messages |
| `main.yml` | Push to main | Build + deploy |
| `remix-docker.yml` | Push to main | Build Remix MCP Docker image |
| `codeql-analysis.yml` | Weekly | Security analysis |
| `auto-merge-dependabot.yml` | PR | Auto-merge Dependabot PRs |

## Required GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

| Secret | Description | Where to get it |
|--------|-------------|-----------------|
| `TELEGRAM_BOT_TOKEN` | Bot token for signal posting | @BotFather on Telegram |
| `TELEGRAM_CHAT_ID` | Chat ID for signal posting | @userinfobot on Telegram |
| `ALCHEMY_API_KEY` | Ethereum RPC access | alchemy.com |
| `ETHERSCAN_API_KEY` | Contract verification | etherscan.io |
| `BINANCE_API_KEY` | Optional, for higher rate limits | binance.com |
| `VPS_PASSWORD` | SSH password for VPS | Your VPS root password |

## How to Set Up Telegram Bot

1. Message @BotFather → `/newbot` → name it `RehoboamSignalsBot`
2. Copy the token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)
3. Add to GitHub Secrets as `TELEGRAM_BOT_TOKEN`
4. Message @userinfobot → copy your numeric Chat ID
5. Add to GitHub Secrets as `TELEGRAM_CHAT_ID`

## How to Trigger Workflows

### Manual trigger (any workflow):
```bash
gh workflow run hermes-signals.yml
gh workflow run jules-vps-maintenance.yml
gh workflow run telegram-send.yml -f target_chat_id="-100123456789" -f message="Test"
```

### Check workflow status:
```bash
gh run list --workflow=hermes-signals.yml
gh run watch <run-id>
```

## Test Commands (Local)

```bash
# Fast unit tests only
python -m pytest tests/ -m "not integration and not heavy" -q

# Integration tests (needs API keys)
python -m pytest tests/ -m integration -q

# Signal tests
python -m pytest tests/ -m signal -q

# JS tests
npx jest --passWithNoTests
```

## Cron Schedule Reference

| Workflow | Cron | Frequency |
|----------|------|-----------|
| Hermes Signals | `*/15 * * * *` | Every 15 minutes |
| Jules VPS | `0 */6 * * *` | Every 6 hours |
| CodeQL | Weekly (default) | Sundays |

## Troubleshooting

**"Workflow not running"** → Check Actions tab → enable workflows if disabled
**"Secret not found"** → Secrets are case-sensitive, check spelling
**"API rate limit"** → Add BINANCE_API_KEY for higher limits
**"VPS connection refused"** → Check UFW: `ufw status verbose`

## 2026 Updates

- Python 3.12 (was 3.11)
- Node 20 (was 18)
- actions/setup-python@v5 (was v4)
- python-telegram-bot 22.7 (was 20.3)
- pytest.ini with 20+ markers for fine-grained test control
- Timeout on tests to prevent CI hangs
- Artifact upload for signal data debugging