"""User & Auth API routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.db import get_db
from utils.auth import create_token, verify_token, generate_referral_code
from models.database import User, Transaction
from datetime import datetime
import hashlib

router = APIRouter(prefix="/api/user", tags=["user"])


@router.post("/auth")
async def auth_user(data: dict, db: AsyncSession = Depends(get_db)):
    """Authenticate or register user via Telegram WebApp initData"""
    telegram_id = data.get("telegram_id")
    username = data.get("username", "")
    first_name = data.get("first_name", "User")
    referral_code = data.get("referral_code")

    if not telegram_id:
        raise HTTPException(400, "telegram_id required")

    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=generate_referral_code(telegram_id),
            referred_by=None
        )

        # Handle referral
        if referral_code:
            ref_result = await db.execute(select(User).where(User.referral_code == referral_code))
            referrer = ref_result.scalar_one_or_none()
            if referrer and referrer.telegram_id != telegram_id:
                user.referred_by = referrer.telegram_id
                referrer.referral_count += 1

        db.add(user)
        await db.commit()
        await db.refresh(user)

    user.last_active = datetime.utcnow()
    await db.commit()

    token = create_token(user.telegram_id, user.username)
    return {
        "token": token,
        "user": {
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "balance": user.balance,
            "total_earned": user.total_earned,
            "referral_code": user.referral_code,
            "referral_count": user.referral_count,
            "referral_earnings": user.referral_earnings,
            "is_premium": user.is_premium,
            "daily_streak": user.daily_streak,
            "level": user.level,
            "xp": user.xp
        }
    }


@router.get("/profile")
async def get_profile(token: str, db: AsyncSession = Depends(get_db)):
    """Get user profile"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "balance": round(user.balance, 4),
        "total_earned": round(user.total_earned, 4),
        "total_staked": round(user.total_staked, 4),
        "referral_code": user.referral_code,
        "referral_count": user.referral_count,
        "referral_earnings": round(user.referral_earnings, 4),
        "is_premium": user.is_premium,
        "daily_streak": user.daily_streak,
        "level": user.level,
        "xp": user.xp,
        "created_at": user.created_at.isoformat()
    }


@router.post("/daily-claim")
async def claim_daily(token: str, db: AsyncSession = Depends(get_db)):
    """Claim daily reward"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    now = datetime.utcnow()
    if user.last_daily_claim and (now - user.last_daily_claim).total_seconds() < 86400:
        raise HTTPException(400, "Already claimed today")

    # Streak bonus
    if user.last_daily_claim and (now - user.last_daily_claim).total_seconds() < 172800:
        user.daily_streak += 1
    else:
        user.daily_streak = 1

    # Reward based on streak
    base_reward = 0.05
    streak_bonus = min(user.daily_streak * 0.01, 0.20)
    total_reward = base_reward + streak_bonus

    user.balance += total_reward
    user.total_earned += total_reward
    user.last_daily_claim = now
    user.xp += 10

    tx = Transaction(user_id=user.telegram_id, type="bonus", amount=total_reward,
                     description=f"Daily reward (streak: {user.daily_streak})")
    db.add(tx)
    await db.commit()

    return {"reward": total_reward, "streak": user.daily_streak, "balance": user.balance}


@router.post("/spin")
async def spin_wheel(token: str, db: AsyncSession = Depends(get_db)):
    """Spin the wheel for rewards"""
    import random
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "User not found")

    # Spin rewards
    rewards = [
        {"label": "$0.01", "amount": 0.01, "weight": 30},
        {"label": "$0.02", "amount": 0.02, "weight": 25},
        {"label": "$0.05", "amount": 0.05, "weight": 20},
        {"label": "$0.10", "amount": 0.10, "weight": 12},
        {"label": "$0.25", "amount": 0.25, "weight": 8},
        {"label": "$0.50", "amount": 0.50, "weight": 3},
        {"label": "$1.00", "amount": 1.00, "weight": 1.5},
        {"label": "JACKPOT $5.00", "amount": 5.00, "weight": 0.5},
    ]

    weights = [r["weight"] for r in rewards]
    chosen = random.choices(rewards, weights=weights, k=1)[0]

    user.balance += chosen["amount"]
    user.total_earned += chosen["amount"]
    user.xp += 5

    tx = Transaction(user_id=user.telegram_id, type="bonus", amount=chosen["amount"],
                     description=f"Spin reward: {chosen['label']}")
    db.add(tx)
    await db.commit()

    return {"reward": chosen["amount"], "label": chosen["label"], "balance": user.balance}
