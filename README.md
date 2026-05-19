# Forex Signal Bot (FastAPI + Telegram)

Production-ready AI-powered forex signal bot scaffold.

Features
- Live market scanner (TwelveData + Finnhub)
- Strategy engine (RSI, EMA20, EMA50, MACD)
- Telegram signal delivery
- FastAPI dashboard + health endpoints
- Docker + Railway deployment
- Logging and error handling

See `./.env.example` for environment variables.

Quick start (local)
1. Copy `.env.example` to `.env` and fill credentials.
2. Create virtualenv and install:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Run locally:
```bash
uvicorn app.main:app --reload
```

Railway deployment
1. Push to GitHub and connect the repo on Railway.
2. Set environment variables in Railway (do NOT commit secrets).
3. Railway will start the `web` service using `Procfile`.

GitHub auto deploy
1. Create GitHub secrets: `RAILWAY_API_KEY`, `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `TWELVEDATA_API_KEY`, `FINNHUB_API_KEY`.
2. The GitHub Actions workflow at `.github/workflows/deploy.yml` will run on pushes to `main`.
3. If Railway is connected to the repo, deployments will trigger automatically from `main`.
