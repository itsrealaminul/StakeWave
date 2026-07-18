"""Telegram Bot - StakeWave"""
import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL", "https://stakewave.vercel.app")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart)
async def cmd_start(message: types.Message):
    """Handle /start command"""
    # Check for referral code
    args = message.text.split()
    referral_code = args[1] if len(args) > 1 else None

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open StakeWave", web_app=WebAppInfo(url=APP_URL))],
        [InlineKeyboardButton(text="📊 My Profile", callback_data="profile"),
         InlineKeyboardButton(text="💰 How to Earn", callback_data="howto")],
        [InlineKeyboardButton(text="👥 Referral Link", callback_data="referral"),
         InlineKeyboardButton(text="🏆 Leaderboard", callback_data="leaderboard")],
        [InlineKeyboardButton(text="🌐 Visit Website", url=APP_URL)]
    ])

    await message.answer(
        f"🌊 <b>Welcome to StakeWave!</b>\n\n"
        f"🔮 <b>Predict</b> — Predict crypto prices & events\n"
        f"💰 <b>Stake</b> — Earn 15% APY on your points\n"
        f"📋 <b>Earn</b> — Complete tasks & watch ads\n"
        f"👥 <b>Refer</b> — Get 12% commission forever\n\n"
        f"👇 Tap below to start earning!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🌊 <b>StakeWave Commands</b>\n\n"
        "/start — Start the bot\n"
        "/earn — Open Mini App\n"
        "/profile — View your profile\n"
        "/referral — Get referral link\n"
        "/leaderboard — Top earners\n"
        "/help — Show this message\n\n"
        "💡 <b>How to Earn:</b>\n"
        "1. Open Mini App\n"
        "2. Complete tasks & predictions\n"
        "3. Stake points for passive income\n"
        "4. Refer friends for 12% commission",
        parse_mode="HTML"
    )


@dp.message(Command("earn"))
async def cmd_earn(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Open StakeWave", web_app=WebAppInfo(url=APP_URL))]
    ])
    await message.answer("💰 Open the app to start earning!", reply_markup=keyboard)


@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Open Profile", web_app=WebAppInfo(url=APP_URL + "#profile"))]
    ])
    await message.answer("📊 Tap below to view your profile:", reply_markup=keyboard)


@dp.message(Command("referral"))
async def cmd_referral(message: types.Message):
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"
    await message.answer(
        f"👥 <b>Your Referral Link:</b>\n\n"
        f"🔗 {referral_link}\n\n"
        f"💰 <b>Earn 12% commission</b> on every referral's earnings — forever!\n\n"
        f"Share this link with friends to start earning!",
        parse_mode="HTML"
    )


@dp.message(Command("leaderboard"))
async def cmd_leaderboard(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 View Leaderboard", web_app=WebAppInfo(url=APP_URL + "#leaderboard"))]
    ])
    await message.answer("🏆 Tap below to view the leaderboard:", reply_markup=keyboard)


@dp.callback_query(F.data == "profile")
async def callback_profile(callback: types.CallbackQuery):
    await callback.answer("Opening profile...")
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Open Profile", web_app=WebAppInfo(url=APP_URL + "#profile"))]
    ])
    await callback.message.answer("📊 Your profile:", reply_markup=keyboard)


@dp.callback_query(F.data == "howto")
async def callback_howto(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "💰 <b>How to Earn on StakeWave:</b>\n\n"
        "1️⃣ <b>Complete Tasks</b> — Watch ads, visit sites, try apps\n"
        "2️⃣ <b>Make Predictions</b> — Predict crypto prices & events\n"
        "3️⃣ <b>Stake Points</b> — Earn 15% APY passive income\n"
        "4️⃣ <b>Daily Spin</b> — Free spin every day\n"
        "5️⃣ <b>Refer Friends</b> — Get 12% of their earnings forever\n\n"
        "🎰 The more you do, the more you earn!",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "referral")
async def callback_referral(callback: types.CallbackQuery):
    bot_info = await bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"
    await callback.answer()
    await callback.message.answer(
        f"👥 <b>Your Referral Link:</b>\n\n{referral_link}\n\n"
        f"Earn 12% on every referral's earnings — forever!",
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "leaderboard")
async def callback_leaderboard(callback: types.CallbackQuery):
    await callback.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 View Leaderboard", web_app=WebAppInfo(url=APP_URL + "#leaderboard"))]
    ])
    await callback.message.answer("🏆 Top Earners:", reply_markup=keyboard)


async def set_webhook():
    """Set bot webhook"""
    webhook_url = os.getenv("WEBHOOK_URL", "")
    if webhook_url:
        await bot.set_webhook(f"{webhook_url}/webhook")
        print(f"✅ Webhook set to: {webhook_url}/webhook")
    else:
        print("⚠️ No WEBHOOK_URL set, using polling")


async def start_bot():
    """Start bot with polling (for development)"""
    await dp.start_polling(bot)
