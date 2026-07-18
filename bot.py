"""Telegram Bot - StakeWave"""
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
APP_URL = os.getenv("APP_URL", "https://stakewave.vercel.app")

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()


@dp.message(CommandStart)
async def cmd_start(message: types.Message):
    args = message.text.split()
    referral_code = args[1] if len(args) > 1 else None

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open StakeWave", web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton(text="📊 My Profile", callback_data="profile"),
         InlineKeyboardButton(text="💰 How to Earn", callback_data="howto")],
        [InlineKeyboardButton(text="👥 Referral Link", callback_data="referral"),
         InlineKeyboardButton(text="🏆 Leaderboard", callback_data="leaderboard")],
    ])

    await message.answer(
        "🌊 <b>Welcome to StakeWave!</b>\n\n"
        "🔮 <b>Predict</b> — Predict crypto prices & events\n"
        "💰 <b>Stake</b> — Earn 15% APY on your points\n"
        "📋 <b>Earn</b> — Complete tasks & watch ads\n"
        "👥 <b>Refer</b> — Get 12% commission forever\n\n"
        "👇 Tap below to start earning!",
        reply_markup=keyboard, parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🌊 <b>StakeWave Commands</b>\n\n"
        "/start — Start the bot\n"
        "/earn — Open Mini App\n"
        "/profile — View profile\n"
        "/referral — Get referral link\n"
        "/leaderboard — Top earners\n"
        "/help — Show this message",
        parse_mode="HTML"
    )


@dp.message(Command("earn"))
async def cmd_earn(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open StakeWave", web_app=WebAppInfo(url=APP_URL))]
    ])
    await message.answer("💰 Open the app to start earning!", reply_markup=keyboard)


@dp.message(Command("referral"))
async def cmd_referral(message: types.Message):
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.answer(
        f"👥 <b>Your Referral Link:</b>\n\n{referral_link}\n\n"
        f"Earn 12% on every referral's earnings — forever!",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Open Profile", web_app=WebAppInfo(url=APP_URL + "#profile"))]
    ])
    await callback.message.answer("📊 Your profile:", reply_markup=keyboard)
    await callback.answer()


@dp.callback_query(F.data == "howto")
async def callback_howto(callback: types.CallbackQuery):
    await callback.message.answer(
        "💰 <b>How to Earn:</b>\n\n"
        "1️⃣ Complete Tasks — Watch ads, visit sites\n"
        "2️⃣ Make Predictions — Crypto prices & events\n"
        "3️⃣ Stake Points — 15% APY passive income\n"
        "4️⃣ Daily Spin — Free rewards daily\n"
        "5️⃣ Refer Friends — 12% commission forever",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "referral")
async def callback_referral(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.message.answer(
        f"👥 <b>Your Referral Link:</b>\n\n{referral_link}\n\nEarn 12% forever!",
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "leaderboard")
async def callback_leaderboard(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 View Leaderboard", web_app=WebAppInfo(url=APP_URL + "#leaderboard"))]
    ])
    await callback.message.answer("🏆 Top Earners:", reply_markup=keyboard)
    await callback.answer()


async def start_polling():
    if bot:
        await dp.start_polling(bot)
