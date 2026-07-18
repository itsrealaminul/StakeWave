"""StakeWave - Main FastAPI Application"""
import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """App startup/shutdown"""
    from utils.db import init_db
    await init_db()
    await seed_data()
    print("✅ Database initialized")
    yield


app = FastAPI(title="StakeWave API", version="1.0.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routes
from routes.user import router as user_router
from routes.predictions import router as predictions_router
from routes.staking import router as staking_router
from routes.tasks import router as tasks_router

app.include_router(user_router)
app.include_router(predictions_router)
app.include_router(staking_router)
app.include_router(tasks_router)


@app.get("/")
async def root():
    return {"name": "StakeWave API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Handle Telegram webhook updates"""
    from bot import bot, dp
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/set-webhook")
async def set_webhook_endpoint():
    """Set bot webhook"""
    from bot import bot
    webhook_url = os.getenv("WEBHOOK_URL", "")
    if webhook_url:
        await bot.set_webhook(f"{webhook_url}/webhook")
        return {"status": "webhook set", "url": f"{webhook_url}/webhook"}
    return {"status": "no WEBHOOK_URL configured"}


async def seed_data():
    """Seed initial data"""
    from utils.db import async_session
    from models.database import Prediction, Task, SpinReward
    from sqlalchemy import select
    from datetime import datetime, timedelta

    async with async_session() as db:
        # Check if already seeded
        result = await db.execute(select(Prediction).limit(1))
        if result.scalar_one_or_none():
            return

        # Seed predictions
        predictions = [
            Prediction(
                title="Will Bitcoin hit $100K by end of 2026?",
                description="Predict whether Bitcoin will reach $100,000 before December 31, 2026",
                category="crypto", option_a="Yes 🚀", option_b="No 📉",
                end_time=datetime.utcnow() + timedelta(days=90)
            ),
            Prediction(
                title="Ethereum price above $5K by Q4 2026?",
                description="Will ETH break the $5,000 barrier?",
                category="crypto", option_a="Yes 🚀", option_b="No 📉",
                end_time=datetime.utcnow() + timedelta(days=60)
            ),
            Prediction(
                title="Will Apple release AR glasses in 2026?",
                description="Predict Apple's AR product launch",
                category="tech", option_a="Yes 👓", option_b="No ❌",
                end_time=datetime.utcnow() + timedelta(days=120)
            ),
            Prediction(
                title="Next US Fed rate decision?",
                description="Will the Fed cut rates in the next meeting?",
                category="finance", option_a="Rate Cut 📉", option_b="Hold/Same 📊",
                end_time=datetime.utcnow() + timedelta(days=30)
            ),
            Prediction(
                title="Tesla stock above $300 by EOY?",
                description="Will TSLA reach $300 by end of year?",
                category="stocks", option_a="Yes 🚗", option_b="No 📉",
                end_time=datetime.utcnow() + timedelta(days=150)
            ),
            Prediction(
                title="Will Dogecoin hit $1?",
                description="The eternal question — will DOGE reach $1?",
                category="crypto", option_a="Yes 🐕", option_b="No 😢",
                end_time=datetime.utcnow() + timedelta(days=180)
            ),
        ]
        for p in predictions:
            db.add(p)

        # Seed tasks
        tasks = [
            Task(title="Follow us on Twitter", description="Follow @StakeWave on X", task_type="social", reward=0.10, url="https://x.com/stakewave"),
            Task(title="Join Telegram Channel", description="Join our official channel", task_type="subscribe", reward=0.05, url="https://t.me/stakewave"),
            Task(title="Watch Ad (30s)", description="Watch a short video ad", task_type="ad", reward=0.03),
            Task(title="Visit Partner Website", description="Visit our partner site for 30 seconds", task_type="visit", reward=0.08),
            Task(title="Complete Survey", description="Fill out a quick survey", task_type="survey", reward=0.25),
            Task(title="Share on Social Media", description="Share StakeWave on your social media", task_type="social", reward=0.15),
            Task(title="Daily Check-in", description="Open the app daily", task_type="daily", reward=0.02),
            Task(title="Try Crypto App", description="Download and try a partner crypto app", task_type="app_install", reward=0.50),
        ]
        for t in tasks:
            db.add(t)

        # Seed spin rewards
        spin_rewards = [
            SpinReward(label="$0.01", amount=0.01, probability=0.30, color="#4CAF50"),
            SpinReward(label="$0.02", amount=0.02, probability=0.25, color="#2196F3"),
            SpinReward(label="$0.05", amount=0.05, probability=0.20, color="#FF9800"),
            SpinReward(label="$0.10", amount=0.10, probability=0.12, color="#9C27B0"),
            SpinReward(label="$0.25", amount=0.25, probability=0.08, color="#F44336"),
            SpinReward(label="$0.50", amount=0.50, probability=0.03, color="#E91E63"),
            SpinReward(label="$1.00", amount=1.00, probability=0.015, color="#FFD700"),
            SpinReward(label="JACKPOT $5", amount=5.00, probability=0.005, color="#FF0000"),
        ]
        for s in spin_rewards:
            db.add(s)

        await db.commit()
        print("✅ Seed data loaded")


# Run bot in background
async def run_bot():
    from bot import start_bot
    await start_bot()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
