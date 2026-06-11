import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
BOT_USERNAME = os.getenv("BOT_USERNAME", "justgift_bot")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-frontend.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "justgift_internal_secret")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

WELCOME_TEXT = """
🎁 *Добро пожаловать в Justgift!*

Открывай кейсы, выигрывай звёзды, испытывай удачу!

✨ Бронзовые, серебряные и золотые кейсы
🎰 Каждый день — бесплатный кейс
💫 Пополнение и вывод звёзд прямо здесь

Нажми кнопку ниже, чтобы начать 👇
"""

def main_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🎁 Открыть Justgift",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = message.text or ""
    args = text.split(" ", 1)[1] if " " in text else ""
    
    # Handle deposit deep-link: /start pay_{tx_id}_{amount}
    if args.startswith("pay_"):
        parts = args.split("_")
        if len(parts) == 3:
            tx_id = parts[1]
            amount = int(parts[2])
            await handle_deposit_request(message, tx_id, amount)
            return
    
    # Handle withdraw deep-link: /start withdraw_{tx_id}_{amount}
    if args.startswith("withdraw_"):
        parts = args.split("_")
        if len(parts) == 3:
            tx_id = parts[1]
            amount = int(parts[2])
            await handle_withdraw_request(message, tx_id, amount)
            return
    
    await message.answer(
        WELCOME_TEXT,
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

async def handle_deposit_request(message: Message, tx_id: str, amount: int):
    """Send Stars invoice for deposit"""
    tg_id = message.from_user.id
    
    await bot.send_invoice(
        chat_id=tg_id,
        title=f"Пополнение баланса — {amount} ⭐",
        description=f"Зачислится {amount} звёзд на ваш баланс в Justgift",
        payload=f"deposit_{tx_id}_{tg_id}_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount} звёзд", amount=amount)],
    )

async def handle_withdraw_request(message: Message, tx_id: str, amount: int):
    """Confirm withdrawal and send Stars check"""
    tg_id = message.from_user.id
    
    await message.answer(
        f"💫 *Запрос на вывод {amount} ⭐ принят*\n\n"
        f"Мы обработаем его в течение 24 часов.\n"
        f"Звёзды будут отправлены на ваш аккаунт.",
        parse_mode="Markdown"
    )

@dp.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery):
    await query.answer(ok=True)

@dp.message(F.successful_payment)
async def payment_received(message: Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    
    if parts[0] == "deposit" and len(parts) == 4:
        tx_id = parts[1]
        tg_id = int(parts[2])
        amount = int(parts[3])
        
        # Confirm in backend
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/api/deposit/confirm",
                json={
                    "secret": INTERNAL_SECRET,
                    "tx_id": int(tx_id),
                    "tg_id": tg_id,
                    "amount": amount
                }
            )
        
        await message.answer(
            f"✅ *Баланс пополнен!*\n\n"
            f"На ваш счёт зачислено *{amount} ⭐*\n\n"
            f"Возвращайтесь в игру 🎁",
            parse_mode="Markdown",
            reply_markup=main_keyboard()
        )

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in [8526401545]:
        return
    
    await message.answer(
        "👑 *Панель администратора*\n\n"
        "Используй команды:\n"
        "`/give [user_id] [amount]` — выдать звёзды\n"
        "`/users` — список пользователей",
        parse_mode="Markdown"
    )

@dp.message(Command("give"))
async def cmd_give(message: Message):
    if message.from_user.id not in [8526401545]:
        return
    
    parts = message.text.split()
    if len(parts) != 3:
        await message.answer("Использование: /give [user_id] [amount]")
        return
    
    target_id = int(parts[1])
    amount = int(parts[2])
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/admin/give-stars",
            json={"tg_id": target_id, "amount": amount},
            headers={"x-init-data": f"dev:{message.from_user.id}"}
        )
    
    if resp.status_code == 200:
        await message.answer(f"✅ Выдано {amount} ⭐ пользователю {target_id}")
        try:
            await bot.send_message(target_id, f"🎁 Администратор выдал вам {amount} ⭐ в Justgift!", 
                                   reply_markup=main_keyboard())
        except Exception:
            pass
    else:
        await message.answer(f"❌ Ошибка: {resp.text}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
