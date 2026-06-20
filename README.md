# 🤖 AI Trading Bot

Automated trading system powered by **Twelvedata** (market data), **Alpaca** (broker), and **DeepSeek AI** (intelligence). Comes with a beautiful dark-theme Next.js dashboard.

## 🚀 Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/mahfudzidris/trading-bot
cd trading-bot

# 2. Configure (start with mock mode — no real money!)
cp .env.example .env
# Edit .env if needed (MOCK_MODE=true by default)

# 3. Run everything
docker compose up -d
```

Then open:
- 📊 **Dashboard:** http://localhost:3000
- 🔧 **API:** http://localhost:8000/docs

---

## 📈 System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ TwelveData  │────▶│  AI Trading  │────▶│   Alpaca    │
│ (Live Data) │     │    Bot       │     │  (Broker)   │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │   SQLite DB  │
                    │  (Trades)    │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Dashboard   │
                    │  (Next.js)   │
                    └──────────────┘
```

## 🧠 How It Works (Mock Mode)

In `MOCK_MODE=true` (default), the system generates realistic mock data:

- **Geometric Brownian motion** for price simulation
- **RSI, SMA, EMA** calculations from mock OHLCV data
- **AI decisions** based on technical indicators (rule-based mock)
- **30 days of historical trades** pre-seeded for the dashboard

No API keys needed — everything runs offline.

---

## 🔑 Live Mode Setup

When ready for real trading:

| # | Step | Details |
|:-:|:-----|:--------|
| 1 | **Twelvedata** | Sign up at [twelvedata.com](https://twelvedata.com) → get API key |
| 2 | **Alpaca** | Sign up at [alpaca.markets](https://alpaca.markets) → get API keys (use paper trading first!) |
| 3 | **DeepSeek** | Sign up at [platform.deepseek.com](https://platform.deepseek.com) → get API key |
| 4 | **Update .env** | Set `MOCK_MODE=false` and fill in all API keys |

```bash
# .env
MOCK_MODE=false
TWELVEDATA_API_KEY=your_key_here
ALPACA_API_KEY=your_key_here
DEEPSEEK_API_KEY=your_key_here
```

---

## 🎯 API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/account` | Account summary |
| `GET` | `/api/positions` | Current positions |
| `GET` | `/api/trades` | Trade history |
| `GET` | `/api/trades/today` | Today's trades |
| `GET` | `/api/daily-reports` | Daily PnL reports |
| `GET` | `/api/analyze/{symbol}` | AI analysis for a symbol |
| `POST` | `/api/run-analysis` | Run daily analysis + trades |
| `GET` | `/api/performance` | Performance summary |

Full API docs at http://localhost:8000/docs (Swagger UI)

---

## 📊 Dashboard Pages

| Page | Route | Features |
|:-----|:------|:---------|
| **Dashboard** | `/` | Summary cards, PnL chart, recent trades |
| **Trades** | `/trades` | Full trade history with filters |
| **Analysis** | `/analysis` | AI recommendations per symbol |
| **Settings** | `/settings` | API config, mock mode toggle |

---

## 💻 Manual Run (without Docker)

### Backend

```bash
cd trading-bot
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
cd backend && uvicorn main:app --reload --port 8000
```

### Dashboard

```bash
cd trading-bot/dashboard
npm install
npm run dev
```

---

## 🛡️ Safety First

| Safety Feature | Description |
|:---------------|:------------|
| 🧪 **Mock mode** | Test everything without real money |
| 📋 **Paper trading** | Alpaca paper account by default |
| 📉 **Stop loss** | Auto-calculated per trade (default 2%) |
| 🧾 **Full audit trail** | Every trade logged with AI reasoning |
| 📊 **Performance tracking** | Win rate, PnL, drawdown monitoring |

---

## 📁 Project Structure

```
trading-bot/
├── backend/
│   ├── main.py                 # FastAPI server + endpoints
│   ├── config.py               # Environment configuration
│   ├── data/
│   │   └── twelvedata_client.py
│   ├── ai/
│   │   └── deepseek_analyzer.py
│   ├── broker/
│   │   └── alpaca_client.py
│   ├── strategy/
│   │   └── engine.py
│   ├── db/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── crud.py             # CRUD operations
│   └── scheduler/
│       └── daily_run.py
├── dashboard/
│   └── src/
│       ├── app/                # Next.js pages
│       ├── components/         # Reusable components
│       ├── lib/                # API client
│       └── types/              # TypeScript types
├── docker-compose.yml
└── .env.example
```

---

## 🔗 Links

- [Twelvedata API Docs](https://twelvedata.com/docs)
- [Alpaca API Docs](https://docs.alpaca.markets)
- [DeepSeek Platform](https://platform.deepseek.com)
- [Next.js](https://nextjs.org)
