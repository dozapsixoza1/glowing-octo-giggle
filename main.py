import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, InlineKeyboardMarkup, InlineKeyboardButton,
    WebAppInfo, LabeledPrice, PreCheckoutQuery, CallbackQuery
)
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8667961704:AAGLpbPSMvcqXDD1sgmRTG2_FtwfHxpZJWI")
BOT_USERNAME = os.getenv("BOT_USERNAME", "justgift_bot")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://automatic-funicular-ov9e.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
INTERNAL_SECRET = os.getenv("INTERNAL_SECRET", "justgift_internal_secret")
ADMIN_IDS = [8526401545]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранение состояния рассылки (в памяти — достаточно для одного процесса)
broadcast_pending: dict[int, str] = {}

WELCOME_TEXT = """
🎁 <b>Добро пожаловать в Justgift!</b>

Открывай кейсы, выигрывай звёзды, испытывай удачу!

✨ Бронзовые, серебряные и золотые кейсы
🎰 Каждый день — бесплатный кейс
💫 Пополнение и вывод звёзд прямо здесь

Нажми кнопку ниже, чтобы начать 👇
"""

def main_keyboard(ref_id=None):
    builder = InlineKeyboardBuilder()
    url = WEBAPP_URL
    if ref_id:
        url = f"{WEBAPP_URL}?ref={ref_id}"
    builder.button(text="🎁 Открыть Justgift", web_app=WebAppInfo(url=url))
    return builder.as_markup()

def admin_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Пользователи", callback_data="admin_users")
    builder.button(text="📢 Рассылка", callback_data="admin_broadcast")
    builder.button(text="🎟 Промокоды", callback_data="admin_promos")
    builder.button(text="⭐ Выдать звёзды", callback_data="admin_give")
    builder.adjust(2)
    return builder.as_markup()

# ============================================================
# /start
# ============================================================
@dp.message(CommandStart())
async def cmd_start(message: Message):
    text = message.text or ""
    args = text.split(" ", 1)[1] if " " in text else ""

    if args.startswith("pay_"):
        parts = args.split("_")
        if len(parts) == 3:
            await handle_deposit_request(message, parts[1], int(parts[2]))
            return

    if args.startswith("withdraw_"):
        parts = args.split("_")
        if len(parts) == 3:
            await handle_withdraw_request(message, parts[1], int(parts[2]))
            return

    # Реферальная ссылка: /start ref_<user_id>
    ref_id = None
    if args.startswith("ref_"):
        try:
            ref_id = int(args.split("_")[1])
        except Exception:
            pass

    await message.answer(
        WELCOME_TEXT,
        parse_mode="HTML",
        reply_markup=main_keyboard(ref_id=message.from_user.id)
    )

# ============================================================
# DEPOSIT / WITHDRAW
# ============================================================
async def handle_deposit_request(message: Message, tx_id: str, amount: int):
    await bot.send_invoice(
        chat_id=message.from_user.id,
        title=f"Пополнение баланса — {amount} ⭐",
        description=f"Зачислится {amount} звёзд на ваш баланс в Justgift",
        payload=f"deposit_{tx_id}_{message.from_user.id}_{amount}",
        currency="XTR",
        prices=[LabeledPrice(label=f"{amount} звёзд", amount=amount)],
    )

async def handle_withdraw_request(message: Message, tx_id: str, amount: int):
    await message.answer(
        f"💫 <b>Запрос на вывод {amount} ⭐ принят</b>\n\n"
        f"Мы обработаем его в течение 24 часов.\n"
        f"Звёзды будут отправлены на ваш аккаунт.",
        parse_mode="HTML"
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
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{BACKEND_URL}/api/deposit/confirm",
                json={"secret": INTERNAL_SECRET, "tx_id": int(tx_id), "tg_id": tg_id, "amount": amount}
            )
        await message.answer(
            f"✅ <b>Баланс пополнен!</b>\n\nНа ваш счёт зачислено <b>{amount} ⭐</b>\n\nВозвращайтесь в игру 🎁",
            parse_mode="HTML",
            reply_markup=main_keyboard()
        )

# ============================================================
# /ref — реферальная ссылка
# ============================================================
@dp.message(Command("ref"))
async def cmd_ref(message: Message):
    tg_id = message.from_user.id
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref_{tg_id}"
    webapp_ref = f"{WEBAPP_URL}?ref={tg_id}"
    await message.answer(
        f"🔗 <b>Ваша реферальная ссылка:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"За каждого приглашённого друга вы получаете <b>25 ⭐</b>!\n\n"
        f"📱 Или поделитесь прямой ссылкой на мини-приложение:\n<code>{webapp_ref}</code>",
        parse_mode="HTML"
    )

# ============================================================
# /admin — панель администратора
# ============================================================
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "👑 <b>Панель администратора</b>\n\nВыбери действие:",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )

# --- Callbacks для кнопок админки ---

@dp.callback_query(F.data == "admin_users")
async def cb_admin_users(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}/api/admin/users",
            headers={"x-init-data": f"dev:{call.from_user.id}"}
        )
    if resp.status_code != 200:
        await call.answer("Ошибка", show_alert=True)
        return
    users = resp.json()[:15]
    text = "👥 <b>Топ пользователей:</b>\n\n"
    for u in users:
        name = u.get("first_name") or "—"
        un = f"@{u['username']}" if u.get("username") else f"ID:{u['tg_id']}"
        text += f"• {name} {un} — <b>{u['balance']} ⭐</b>\n"
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_keyboard())
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    broadcast_pending[call.from_user.id] = "waiting"
    await call.message.edit_text(
        "📢 <b>Рассылка</b>\n\nНапишите текст сообщения (поддерживается HTML).\n"
        "Для отмены введи /admin",
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data == "admin_promos")
async def cb_admin_promos(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BACKEND_URL}/api/admin/promos",
            headers={"x-init-data": f"dev:{call.from_user.id}"}
        )
    promos = resp.json() if resp.status_code == 200 else []
    text = "🎟 <b>Промокоды:</b>\n\n"
    if not promos:
        text += "Нет активных промокодов\n"
    for p in promos[:10]:
        text += f"• <code>{p['code']}</code> — {p['stars']} ⭐, использован {p['used_count']}/{p['max_uses']}\n"
    text += "\n<b>Создать промокод:</b>\n/promo &lt;код&gt; &lt;звёзд&gt; &lt;макс_использований&gt;\n"
    text += "Пример: <code>/promo SUMMER50 50 100</code>"
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=admin_keyboard())
    await call.answer()

@dp.callback_query(F.data == "admin_give")
async def cb_admin_give(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        return
    await call.message.edit_text(
        "⭐ <b>Выдать звёзды</b>\n\nИспользуй команду:\n"
        "<code>/give [user_id] [количество]</code>\n\n"
        "Пример: <code>/give 123456789 500</code>",
        parse_mode="HTML",
        reply_markup=admin_keyboard()
    )
    await call.answer()

# --- Перехват текста для рассылки ---
@dp.message(F.text & ~F.text.startswith("/"))
async def handle_text(message: Message):
    if message.from_user.id in ADMIN_IDS and broadcast_pending.get(message.from_user.id) == "waiting":
        broadcast_pending.pop(message.from_user.id)
        text_to_send = message.text
        # Выполняем рассылку
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/admin/broadcast",
                json={"text": text_to_send},
                headers={"x-init-data": f"dev:{message.from_user.id}"}
            )
        if resp.status_code == 200:
            r = resp.json()
            await message.answer(
                f"✅ <b>Рассылка завершена!</b>\n\nОтправлено: {r['sent']}\nНе доставлено: {r['failed']}\nВсего: {r['total']}",
                parse_mode="HTML",
                reply_markup=admin_keyboard()
            )
        else:
            await message.answer("❌ Ошибка при рассылке")

# ============================================================
# /give — выдать звёзды пользователю
# ============================================================
@dp.message(Command("give"))
async def cmd_give(message: Message):
    if message.from_user.id not in ADMIN_IDS:
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
            await bot.send_message(target_id, f"🎁 Администратор выдал вам {amount} ⭐ в Justgift!", reply_markup=main_keyboard())
        except Exception:
            pass
    else:
        await message.answer(f"❌ Ошибка: {resp.text}")

# ============================================================
# /promo — создать промокод
# ============================================================
@dp.message(Command("promo"))
async def cmd_promo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    parts = message.text.split()
    # /promo <code> <stars> [max_uses]
    if len(parts) < 3:
        await message.answer(
            "Использование:\n<code>/promo КОД ЗВЁЗД [МАК_ИСПОЛЬЗОВАНИЙ]</code>\n"
            "Пример: <code>/promo SUMMER50 50 100</code>\n"
            "Без кода — сгенерирует автоматически: <code>/promo _ 50 10</code>",
            parse_mode="HTML"
        )
        return
    code = parts[1] if parts[1] != "_" else ""
    stars = int(parts[2])
    max_uses = int(parts[3]) if len(parts) >= 4 else 1
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BACKEND_URL}/api/admin/promo/create",
            json={"code": code, "stars": stars, "max_uses": max_uses},
            headers={"x-init-data": f"dev:{message.from_user.id}"}
        )
    if resp.status_code == 200:
        r = resp.json()
        await message.answer(
            f"✅ <b>Промокод создан!</b>\n\nКод: <code>{r['code']}</code>\nЗвёзд: <b>{r['stars']} ⭐</b>\nИспользований: <b>{r['max_uses']}</b>",
            parse_mode="HTML"
        )
    else:
        err = resp.json().get("detail", "Ошибка")
        await message.answer(f"❌ {err}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
