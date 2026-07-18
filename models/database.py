"""Database models for StakeWave"""
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    language = Column(String(5), default="en")
    balance = Column(Float, default=0.0)
    total_earned = Column(Float, default=0.0)
    total_staked = Column(Float, default=0.0)
    referral_code = Column(String(20), unique=True)
    referred_by = Column(Integer, nullable=True)
    referral_count = Column(Integer, default=0)
    referral_earnings = Column(Float, default=0.0)
    is_premium = Column(Boolean, default=False)
    daily_streak = Column(Integer, default=0)
    last_daily_claim = Column(DateTime, nullable=True)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    stakes = relationship("Stake", back_populates="user")
    predictions = relationship("PredictionEntry", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")


class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50))
    image_url = Column(String(500))
    option_a = Column(String(100), nullable=False)
    option_b = Column(String(100), nullable=False)
    total_pool_a = Column(Float, default=0.0)
    total_pool_b = Column(Float, default=0.0)
    correct_option = Column(String(1), nullable=True)
    status = Column(String(20), default="active")
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    min_bet = Column(Float, default=0.10)
    max_bet = Column(Float, default=100.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    entries = relationship("PredictionEntry", back_populates="prediction")


class PredictionEntry(Base):
    __tablename__ = "prediction_entries"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=False)
    option = Column(String(1), nullable=False)
    amount = Column(Float, nullable=False)
    potential_payout = Column(Float, default=0.0)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="predictions")
    prediction = relationship("Prediction", back_populates="entries")


class Stake(Base):
    __tablename__ = "stakes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)
    apy_percent = Column(Float, default=15.0)
    earned_so_far = Column(Float, default=0.0)
    status = Column(String(20), default="active")
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    last_yield_calc = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="stakes")


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    type = Column(String(30), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(200))
    status = Column(String(20), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="transactions")


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    task_type = Column(String(30))
    reward = Column(Float, nullable=False)
    url = Column(String(500))
    image_url = Column(String(500))
    is_active = Column(Boolean, default=True)
    daily_limit = Column(Integer, default=100)
    completed_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserTask(Base):
    __tablename__ = "user_tasks"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.telegram_id"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    status = Column(String(20), default="pending")
    completed_at = Column(DateTime, nullable=True)


class SpinReward(Base):
    __tablename__ = "spin_rewards"
    id = Column(Integer, primary_key=True)
    label = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    probability = Column(Float, nullable=False)
    color = Column(String(20), default="#4CAF50")
    is_active = Column(Boolean, default=True)
