"""Prediction market routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.db import get_db
from utils.auth import verify_token
from models.database import User, Prediction, PredictionEntry, Transaction
from datetime import datetime, timedelta
import random

router = APIRouter(prefix="/api/predictions", tags=["predictions"])


@router.get("/active")
async def get_active_predictions(db: AsyncSession = Depends(get_db)):
    """Get all active predictions"""
    result = await db.execute(
        select(Prediction).where(Prediction.status == "active").order_by(Prediction.created_at.desc())
    )
    predictions = result.scalars().all()
    return [{
        "id": p.id, "title": p.title, "description": p.description,
        "category": p.category, "image_url": p.image_url,
        "option_a": p.option_a, "option_b": p.option_b,
        "total_pool_a": round(p.total_pool_a, 2),
        "total_pool_b": round(p.total_pool_b, 2),
        "total_pool": round(p.total_pool_a + p.total_pool_b, 2),
        "end_time": p.end_time.isoformat(),
        "min_bet": p.min_bet, "max_bet": p.max_bet,
        "status": p.status
    } for p in predictions]


@router.post("/bet")
async def place_bet(data: dict, token: str, db: AsyncSession = Depends(get_db)):
    """Place a prediction bet"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    prediction_id = data.get("prediction_id")
    option = data.get("option")  # "A" or "B"
    amount = data.get("amount", 0)

    if option not in ("A", "B") or amount <= 0:
        raise HTTPException(400, "Invalid option or amount")

    result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = result.scalar_one_or_none()
    if not user or user.balance < amount:
        raise HTTPException(400, "Insufficient balance")

    pred_result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
    prediction = pred_result.scalar_one_or_none()
    if not prediction or prediction.status != "active":
        raise HTTPException(400, "Prediction not available")

    if amount < prediction.min_bet or amount > prediction.max_bet:
        raise HTTPException(400, f"Bet must be between ${prediction.min_bet} and ${prediction.max_bet}")

    # Calculate potential payout
    total_pool = prediction.total_pool_a + prediction.total_pool_b + amount
    if option == "A":
        prediction.total_pool_a += amount
        opposite_pool = prediction.total_pool_b
    else:
        prediction.total_pool_b += amount
        opposite_pool = prediction.total_pool_a

    platform_fee = amount * 0.03
    net_amount = amount - platform_fee
    potential_payout = net_amount + (net_amount * (opposite_pool / (total_pool - amount + 0.01)))

    user.balance -= amount
    entry = PredictionEntry(
        user_id=user.telegram_id, prediction_id=prediction_id,
        option=option, amount=amount, potential_payout=round(potential_payout, 4)
    )
    tx = Transaction(
        user_id=user.telegram_id, type="predict", amount=-amount,
        description=f"Bet ${amount} on {option}: {prediction.title}"
    )
    db.add(entry)
    db.add(tx)
    await db.commit()

    return {
        "entry_id": entry.id, "option": option, "amount": amount,
        "potential_payout": round(potential_payout, 4),
        "new_balance": round(user.balance, 4)
    }


@router.get("/my-bets")
async def get_my_bets(token: str, db: AsyncSession = Depends(get_db)):
    """Get user's prediction entries"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(
        select(PredictionEntry, Prediction)
        .join(Prediction, PredictionEntry.prediction_id == Prediction.id)
        .where(PredictionEntry.user_id == payload["telegram_id"])
        .order_by(PredictionEntry.created_at.desc())
    )
    rows = result.all()
    return [{
        "entry_id": e.id, "prediction_title": p.title,
        "option": e.option, "amount": e.amount,
        "potential_payout": e.potential_payout, "status": e.status,
        "prediction_status": p.status,
        "created_at": e.created_at.isoformat()
    } for e, p in rows]


@router.get("/leaderboard")
async def get_leaderboard(db: AsyncSession = Depends(get_db)):
    """Get top earners leaderboard"""
    result = await db.execute(
        select(User).order_by(User.total_earned.desc()).limit(50)
    )
    users = result.scalars().all()
    return [{
        "rank": i + 1,
        "username": u.username or u.first_name or "Anonymous",
        "total_earned": round(u.total_earned, 2),
        "level": u.level,
        "referral_count": u.referral_count
    } for i, u in enumerate(users)]
