"""Tasks & Offers routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from utils.db import get_db
from utils.auth import verify_token
from models.database import User, Task, UserTask, Transaction
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/available")
async def get_available_tasks(token: str, db: AsyncSession = Depends(get_db)):
    """Get available tasks for user"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    # Get tasks not completed by user
    completed = await db.execute(
        select(UserTask.task_id).where(UserTask.user_id == payload["telegram_id"])
    )
    completed_ids = [r[0] for r in completed.all()]

    result = await db.execute(
        select(Task).where(Task.is_active == True, ~Task.id.in_(completed_ids) if completed_ids else True)
        .order_by(Task.reward.desc())
    )
    tasks = result.scalars().all()

    return [{
        "id": t.id, "title": t.title, "description": t.description,
        "task_type": t.task_type, "reward": t.reward,
        "url": t.url, "image_url": t.image_url
    } for t in tasks]


@router.post("/complete")
async def complete_task(data: dict, token: str, db: AsyncSession = Depends(get_db)):
    """Mark task as completed and claim reward"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    task_id = data.get("task_id")
    result = await db.execute(select(Task).where(Task.id == task_id, Task.is_active == True))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")

    # Check if already completed
    existing = await db.execute(
        select(UserTask).where(UserTask.user_id == payload["telegram_id"], UserTask.task_id == task_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Task already completed")

    # Check daily limit
    if task.completed_count >= task.daily_limit:
        raise HTTPException(400, "Task limit reached")

    user_result = await db.execute(select(User).where(User.telegram_id == payload["telegram_id"]))
    user = user_result.scalar_one_or_none()

    # Reward user
    user.balance += task.reward
    user.total_earned += task.reward
    user.xp += 20

    # Referral commission
    if user.referred_by:
        ref_result = await db.execute(select(User).where(User.telegram_id == user.referred_by))
        referrer = ref_result.scalar_one_or_none()
        if referrer:
            commission = task.reward * 0.12
            referrer.balance += commission
            referrer.referral_earnings += commission
            referrer.total_earned += commission
            ref_tx = Transaction(user_id=referrer.telegram_id, type="referral", amount=commission,
                                 description=f"Referral commission from {user.username}")
            db.add(ref_tx)

    user_task = UserTask(user_id=user.telegram_id, task_id=task_id,
                         status="completed", completed_at=datetime.utcnow())
    task.completed_count += 1
    tx = Transaction(user_id=user.telegram_id, type="earn", amount=task.reward,
                     description=f"Task completed: {task.title}")
    db.add(user_task)
    db.add(tx)
    await db.commit()

    return {"reward": task.reward, "balance": round(user.balance, 4), "xp": user.xp}
