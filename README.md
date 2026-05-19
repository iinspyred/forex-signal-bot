# AI Forex Signal Bot

Production-ready FastAPI forex signal bot for Railway. It fetches live market data, scans forex candles, generates BUY/SELL alerts, stores emitted signals, exposes health/dashboard endpoints, and responds to Telegram commands.

## Features

- Async FastAPI service with one low-resource scanner loop
- TwelveData candle data with Finnhub fallback quote snapshots
- RSI, EMA20/EMA50, MACD, trend, volatility, and volume filters
- Duplicate signal prevention and confidence scoring
- Telegram alerts, startup notice, hourly heartbeat, and `/start`, `/help`, `/status`
- Rotating application, error, and trade logs
- SQLite signal persistence
- Railway, Docker, Procfile, and GitHub auto-deploy ready
- TradingView webhook placeholder at `POST /webhook/tradingview`

## Environment

Create a local `.env` from `.env.example` and set real values:

```bash
TWELVEDATA_API_KEY=your_twelvedata_api_key
FINNHUB_API_KEY=your_finnhub_api_key
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
SCAN_INTERVAL_SECONDS=60
SIGNAL_COOLDOWN_MINUTES=30
HEARTBEAT_INTERVAL_SECONDS=3600
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./signals.db
```

Do not commit `.env`. Rotate any token that has been shared publicly.

## Local Development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open:

- `GET http://localhost:8000/`
- `GET http://localhost:8000/health`
- `GET http://localhost:8000/signals`
- `GET http://localhost:8000/stats`

## Telegram Setup

1. Create a bot with BotFather and copy the token.
2. Send a message to the bot from your Telegram account or group.
3. Set `TELEGRAM_CHAT_ID` to the target chat id.
4. Start the app. The bot uses polling and responds to `/start`, `/help`, and `/status`.

## Railway Deployment

1. Push this repository to GitHub.
2. In Railway, create a new project from the GitHub repository.
3. Add the environment variables from `.env.example`.
4. Deploy. Railway uses the `Dockerfile` and runs:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## GitHub Auto Deploy

Railway automatically redeploys when the connected GitHub branch changes. Keep secrets in Railway variables only, not in GitHub.

## Docker

```bash
docker build -t forex-signal-bot .
docker run --env-file .env -p 8000:8000 forex-signal-bot
```

## Troubleshooting

- No Telegram messages: check `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, and whether the bot can message the chat.
- No signals: strict filters may produce no alerts during quiet markets; check `/health` and `logs/app.log`.
- API errors: confirm provider keys, rate limits, and pair support.
- Railway starts then exits: verify all required environment variables and inspect deployment logs.

## Disclaimer

This project generates forex signals for research and alerting. It does not execute trades and is not financial advice.
