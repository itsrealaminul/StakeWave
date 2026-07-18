"""Staking routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.db import get_db
from utils.auth import verify_token
from models.database import User, Stake, Transaction
from datetime import datetime
import os

router = APIRouter(prefix="/api/staking", tags=["staking"])

APY = float(os.getenv("STAKING_APY", "15"))


@router.post("/stake")
async def create_stake(data: dict, token: str, db: AsyncSession = Depends(get_db)):
    """Stake points to earn yield"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    amount = data.get("amount", 0)
    if amount <= 0:
        raise HTTPException(400, "Invalid amount")

    result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = result.scalar_one_or_none()
    if not user or user.balance < amount:
        raise HTTPException(400, "Insufficient balance")

    user.balance -= amount
    user.total_staked += amount

    stake = Stake(user_id=user.telegram_id, amount=amount, apy_percent=APY)
    tx = Transaction(user_id=user.telegram_id, type="stake", amount=-amount,
                     description=f"Staked ${amount} at {APY}% APY")
    db.add(stake)
    db.add(tx)
    await db.commit()

    return {"stake_id": stake.id, "amount": amount, "apy": APY, "balance": user.balance}


@router.post("/unstake")
async def unstake(data: dict, token: str, db: AsyncSession = Depends(get_db)):
    """Unstake and collect earnings"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    stake_id = data.get("stake_id")
    result = await db.execute(select(Stake).where(Stake.id == stake_id, Stake.user_id == payload["telegram_id"]))
    stake = result.scalar_one_or_none()
    if not stake or stake.status != "active":
        raise HTTPException(404, "Stake not found")

    # Calculate final yield
    days = (datetime.utcnow() - stake.start_date).total_seconds() / 86400
    yield_amount = stake.amount * (stake.apy_percent / 100) * (days / 365)
    total_return = stake.amount + yield_amount

    user_result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = user_result.scalar_one_or_none()
    user.balance += total_return
    user.total_earned += yield_amount
    user.total_staked -= stake.amount

    stake.status = "withdrawn"
    stake.earned_so_far = yield_amount
    stake.end_date = datetime.utcnow()

    tx = Transaction(user_id=user.telegram_id, type="unstake", amount=total_return,
                     description=f"Unstaked ${stake.amount} + ${round(yield_amount, 4)} yield")
    db.add(tx)
    await db.commit()

    return {"stake_id": stake.id, "principal": stake.amount, "yield": round(yield_amount, 4),
            "total_return": round(total_return, 4), "balance": round(user.balance, 4)}


@router.get("/my-stakes")
async def get_my_stakes(token: str, db: AsyncSession = Depends(get_db)):
    """Get user's active stakes"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    result = await db.execute(
        select(Stake).where(Stake.user_id == payload["telegram_id"]).order_by(Stake.start_date.desc())
    )
    stakes = result.scalars().all()
    now = datetime.utcnow()
    return [{
        "id": s.id, "amount": s.amount, "apy": s.apy_percent,
        "earned_so_far": round(s.earned_so_far + s.amount * (s.apy_percent / 100) * ((now - s.start_date).total_seconds() / 86400 / 365), 4),
        "status": s.status, "start_date": s.start_date.isoformat()
    } for s in stakes]
