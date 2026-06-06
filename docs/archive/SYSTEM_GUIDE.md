# 🏔️ REHOBOAM — COMPLETE SYSTEM GUIDE

## What's Running Right Now

| Service | Status | PID | Purpose |
|---------|--------|-----|---------|
| Signal Bot | 🟢 RUNNING | 930283 | Posts signals every 5 min |
| Interactive Bot | 🟢 RUNNING | 930285 | Talks to customers |
| Cron Job | 🟢 ACTIVE | — | Runs every 5 min |
| Landing Page | 🟢 SERVING | — | http://localhost:8080 |
| Health Monitor | 🟢 ACTIVE | — | Checks every minute |

## Quick Commands

```bash
# Start everything
./start_all.sh

# Check status
python3 status_dashboard.py

# Start trial for user
python3 customer_acquisition.py --start-trial @username

# Check customer stats
python3 customer_acquisition.py --stats

# View logs
tail -f signal_data/hermes_bot.log
tail -f signal_data/hermes_interactive_bot.log
tail -f signal_data/health.log
```

## Customer Flow

1. **Discovery** → User sees post on Telegram/Twitter/Reddit
2. **DM Bot** → User messages @web4_bot_nobot
3. **Onboarding** → Bot sends /start with welcome + trial offer
4. **Trial** → User gets 7 days FREE PRO
5. **Signals** → Real signals every 5 minutes
6. **Referral** → User shares code, gets +7 days per conversion
7. **Conversion** → User pays $49/month (PRO) or $149/month (VIP)

## File Structure

```
clean_rehoboam_project/
├── hermes_signal_bot.py          # Posts signals to Telegram
├── hermes_interactive_bot.py     # Talks to customers
├── real_convergence_engine.py    # Multi-source signal engine
├── customer_acquisition.py       # Customer tracking & outreach
├── status_dashboard.py           # System status
├── health_check.py               # Auto-restart dead services
├── landing_page.html             # Pricing page
├── start_all.sh                  # Start everything
├── marketing_content/             # SEO content
│   ├── blog_*.md
│   ├── twitter_thread.txt
│   ├── reddit_post.txt
│   └── outreach_messages.json
└── signal_data/
    ├── customers.db              # Customer database
    ├── signals.db                # Signal performance
    ├── hermes_bot.log
    ├── hermes_interactive_bot.log
    └── health.log
```

## Database Schema

### customers.db
- telegram_id, username, status, tier, trial_start, trial_end
- referral_code, referred_by, referral_count
- first_contact, last_contact, messages_count

### signals.db
- pair, action, tier, strength, entry_price
- stop_loss, take_profit_1, take_profit_2
- risk_reward, convergence_score, status, pnl_pct

## Monetization

| Tier | Price | Features |
|------|-------|----------|
| FREE | $0 | 1 signal/day, delayed |
| PRO | $49/mo | Unlimited, real-time, 3-source |
| VIP | $149/mo | Everything + whale tracking |

**Revenue Streams:**
1. Subscriptions ($49-149/mo)
2. Affiliate commissions (Binance/Bybit/OKX)
3. Bot setup service ($200 one-time)
4. Referral rewards (+7 days free)

## Support

- **Bot:** @web4_bot_nobot
- **Admin:** Check .env ADMIN_CHAT_ID
- **Wallet:** 0xa4660Bf26BF89fe073d42E7A4945a3Df6Bd3c407

## Health Monitoring

Cron jobs:
- Every minute: Health check + auto-restart
- Every 5 minutes: Signal generation + posting
- Every 30 minutes: Lead search

## Never Forget

The SQLite database remembers:
- Every customer interaction
- Every signal generated
- Every trial started
- Every referral made
- Every message sent

**Even if the server crashes, the data survives.**
