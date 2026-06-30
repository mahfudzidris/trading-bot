# Trading Bot Architecture v2.2

## Overview
AI-powered automated trading bot for US equities (SPLG). Runs on FastAPI backend with Next.js dashboard. Executes trades via Alpaca Paper API using ensemble AI analysis.

## System Components

```
┌─────────────────────────────────────────────────────────┐
│                    Trading Bot System                    │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │TwelveData│  │ DeepSeek │  │  Alpaca  │  │ Backend│  │
│  │  Market  │  │    AI    │  │  Broker  │  │   DB   │  │
│  │   Data   │  │ Analysis │  │  (Paper) │  │ SQLite │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬───┘  │
│       │             │             │              │      │
│       └─────────────┴─────────────┴──────────────┘      │
│                          │                               │
│                   ┌──────┴──────┐                        │
│                   │  Strategy   │                        │
│                   │   Engine    │                        │
│                   │ (DCA + TS)  │                        │
│                   └──────┬──────┘                        │
│                          │                               │
│              ┌───────────┴───────────┐                   │
│              │   Market Watcher      │                   │
│              │  (15-min interval)    │                   │
│              └───────────────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## Services

### 1. Market Data — TwelveData
- Real-time quotes & technical indicators
- REST API via `twelvedata_client.py`
- **Status:** ✅ Connected

### 2. AI Analysis — DeepSeek
- Analyzes SPLG price action + technical indicators
- Returns BUY/SELL/HOLD with confidence score (0-100)
- Threshold: ≥80% confidence required for execution
- Model: `deepseek-v4-flash`
- **Status:** ✅ Connected (key renewed)

### 3. Broker — Alpaca Paper
- Executes market orders with bracket TP/SL
- Fractional shares enabled (float qty)
- Paper account: **$500 cash** (USD)
- **Status:** ✅ ACTIVE

### 4. Strategy Engine
- **DCA (Dollar Cost Average):** 3 tranches per position
- **Trailing Stop:** Activates at +1% profit, trails 0.5%
- **Position Size:** 5% max per trade ($25)
- **Stop Loss:** 1% | **Take Profit:** 4%
- **Symbol:** SPLG (~$65-$85/share)
- **Short trades:** Disabled (cash account)

### 5. Market Watcher
- Background asyncio loop
- 15-minute interval during US market hours (9:30 PM - 4:00 AM MYT)
- Checks local time (MYT) for market hours
- Auto-executes trades when AI confidence ≥ 80%
- **Status:** ✅ Running, 0 failed ticks

### 6. Dashboard (Next.js)
- Account Summary card (balance, cash, BP, PnL)
- Trade history table with filters
- Real-time position tracking
- Accessible via Tailscale: `100.108.97.116:3000`

## Data Flow
```
AI Signal (BUY 85%) → Strategy Engine → DCA Check → Alpaca Order → SQLite DB → Dashboard
                                     ↓
                              Trailing Stop Monitor
```

## Cron Jobs
| Job | Schedule (MYT) | Purpose |
|---|---|---|
| Market Open Report | 9:30 PM Mon-Fri | Pre-market health check + status |
| Market Close Report | 4:00 AM Tue-Sat | Daily P&L + trade summary |
| Trade Watchdog | Every 5 min | Alert on new trades |
| Waktu Solat | 5:30 AM, 8:00 PM | Prayer times (Rawang) |

## Configuration
- `MOCK_MODE=false` — Live paper trading
- `ALPACA_PAPER=true` — Paper account
- `AUTO_TRADE=true` — Autonomous execution
- `MARKET_AUTO_RUN=true` — 24/7 watcher
- Capital: **USD $500** (~MYR 2,000)

## Deployment
- **Backend:** FastAPI, port 8000
- **Dashboard:** Next.js 16, port 3000
- **Network:** Tailscale (100.108.97.116)
- **Host:** macOS (local machine)

---

*Last updated: 2026-06-30*
