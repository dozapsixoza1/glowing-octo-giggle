from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sqlite3
import json
import hashlib
import hmac
import time
import os
import random
import string
from datetime import datetime, date

app = FastAPI(title="Justgift API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_TOKEN = os.getenv("BOT_TOKEN", "8667961704:AAGLpbPSMvcqXDD1sgmRTG2_FtwfHxpZJWI")
ADMIN_IDS = [8526401545]
DB_PATH = os.getenv("DB_PATH", "justgift.db")

CHANNEL_ID = "@justgif_t"
CHAT_ID = "@justgiftchat"

# === CASES CONFIG ===
CASES = {
    "bronze": {
        "name": "Бронзовый кейс",
        "price": 50,
        "color": "#CD7F32",
        "items": [
            {"name": "10 звёзд", "stars": 10, "chance": 50, "rarity": "common"},
            {"name": "25 звёзд", "stars": 25, "chance": 30, "rarity": "uncommon"},
            {"name": "50 звёзд", "stars": 50, "chance": 15, "rarity": "rare"},
            {"name": "150 звёзд", "stars": 150, "chance": 4, "rarity": "epic"},
            {"name": "500 звёзд", "stars": 500, "chance": 1, "rarity": "legendary"},
        ]
    },
    "silver": {
        "name": "Серебряный кейс",
        "price": 150,
        "color": "#C0C0C0",
        "items": [
            {"name": "50 звёзд", "stars": 50, "chance": 45, "rarity": "common"},
            {"name": "100 звёзд", "stars": 100, "chance": 30, "rarity": "uncommon"},
            {"name": "250 звёзд", "stars": 250, "chance": 15, "rarity": "rare"},
            {"name": "500 звёзд", "stars": 500, "chance": 8, "rarity": "epic"},
            {"name": "2000 звёзд", "stars": 2000, "chance": 2, "rarity": "legendary"},
        ]
    },
    "gold": {
        "name": "Золотой кейс",
        "price": 500,
        "color": "#FFD700",
        "items": [
            {"name": "200 звёзд", "stars": 200, "chance": 40, "rarity": "common"},
            {"name": "400 звёзд", "stars": 400, "chance": 30, "rarity": "uncommon"},
            {"name": "800 звёзд", "stars": 800, "chance": 18, "rarity": "rare"},
            {"name": "2000 звёзд", "stars": 2000, "chance": 10, "rarity": "epic"},
            {"name": "10000 звёзд", "stars": 10000, "chance": 2, "rarity": "legendary"},
        ]
    },
    "daily": {
        "name": "Ежедневный кейс",
        "price": 0,
        "color": "#C8FF00",
        "items": [
            {"name": "5 звёзд", "stars": 5, "chance": 50, "rarity": "common"},
            {"name": "15 звёзд", "stars": 15, "chance": 30, "rarity": "uncommon"},
            {"name": "30 звёзд", "stars": 30, "chance": 15, "rarity": "rare"},
            {"name": "100 звёзд", "stars": 100, "chance": 4, "rarity": "epic"},
            {"name": "500 звёзд", "stars": 500, "chance": 1, "rarity": "legendary"},
        ]
    }
}

# === DATABASE ===
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        tg_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        photo_url TEXT,
        balance INTEGER DEFAULT 0,
        total_won INTEGER DEFAULT 0,
        cases_opened INTEGER DEFAULT 0,
        last_daily TEXT,
        referred_by INTEGER DEFAULT NULL,
        referral_count INTEGER DEFAULT 0,
        referral_earned INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        type TEXT,
        amount INTEGER,
        status TEXT DEFAULT 'pending',
        payload TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS case_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER,
        case_type TEXT,
        item_name TEXT,
        stars_won INTEGER,
        rarity TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    # НОВОЕ: промокоды
    c.execute('''CREATE TABLE IF NOT EXISTS promo_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        stars INTEGER NOT NULL,
        max_uses INTEGER DEFAULT 1,
        used_count INTEGER DEFAULT 0,
        expires_at TEXT DEFAULT NULL,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )''')
    # НОВОЕ: кто активировал промокод
    c.execute('''CREATE TABLE IF NOT EXISTS promo_uses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT NOT NULL,
        tg_id INTEGER NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(code, tg_id)
    )''')
    conn.commit()

    # Миграция: добавить реферальные колонки если их нет
    try:
        c.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN referral_earned INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass

    conn.close()

init_db()

# === AUTH ===
def verify_telegram_data(init_data: str) -> Optional[dict]:
    """
    Telegram WebApp initData verification.
    initData приходит как URL-encoded строка, например:
      user=%7B%22id%22%3A123%7D&auth_date=1234&hash=abc
    """
    try:
        import urllib.parse

        # 1. Полностью декодируем строку (Telegram шлёт URL-encoded)
        decoded = urllib.parse.unquote(init_data)

        # 2. Парсим в dict — используем parse_qs с keep_blank_values
        parsed_qs = urllib.parse.parse_qs(decoded, keep_blank_values=True)
        # parse_qs возвращает списки, берём первый элемент
        parsed = {k: v[0] for k, v in parsed_qs.items()}

        hash_val = parsed.pop("hash", None)
        if not hash_val:
            # Попробуем ещё раз через split — некоторые клиенты шлют не-encoded
            parsed2 = {}
            for item in init_data.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    parsed2[urllib.parse.unquote(k)] = urllib.parse.unquote(v)
            hash_val = parsed2.pop("hash", None)
            if not hash_val:
                return None
            parsed = parsed2

        # 3. Строим data-check-string (ключи отсортированы, разделитель \n)
        data_check = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))

        # 4. HMAC: secret = HMAC-SHA256("WebAppData", BOT_TOKEN)
        #    computed = HMAC-SHA256(secret, data_check_string)
        secret = hmac.new(
            b"WebAppData",          # key
            BOT_TOKEN.encode(),    # msg
            hashlib.sha256
        ).digest()
        computed = hmac.new(
            secret,                # key
            data_check.encode(),   # msg
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(computed, hash_val):
            user_str = parsed.get("user", "{}")
            # user может быть ещё раз URL-encoded внутри
            try:
                return json.loads(user_str)
            except json.JSONDecodeError:
                return json.loads(urllib.parse.unquote(user_str))
        
        print(f"HMAC mismatch. computed={computed[:16]}... got={hash_val[:16]}...")
        return None
    except Exception as e:
        print("verify_telegram_data error:", e)
        return None

def get_current_user(x_init_data: str = Header(None)):
    if not x_init_data:
        raise HTTPException(status_code=401, detail="No auth")
    
    if x_init_data.startswith("dev:"):
        tg_id = int(x_init_data.split(":")[1])
        return {"id": tg_id, "first_name": "Dev User"}
    
    user = verify_telegram_data(x_init_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth")
    return user

def get_or_create_user(tg_user: dict, ref_id: int = None) -> dict:
    conn = get_db()
    c = conn.cursor()
    tg_id = tg_user["id"]
    
    user = c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    if not user:
        referred_by = ref_id if ref_id and ref_id != tg_id else None
        c.execute(
            "INSERT INTO users (tg_id, username, first_name, last_name, referred_by) VALUES (?,?,?,?,?)",
            (tg_id, tg_user.get("username"), tg_user.get("first_name"), tg_user.get("last_name"), referred_by)
        )
        conn.commit()
        # Если пришёл по реферале — начислить бонус рефереру
        if referred_by:
            REFERRAL_BONUS = 25  # звёзд рефереру
            c.execute("UPDATE users SET balance = balance + ?, referral_count = referral_count + 1, referral_earned = referral_earned + ? WHERE tg_id = ?",
                      (REFERRAL_BONUS, REFERRAL_BONUS, referred_by))
            conn.commit()
        user = c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    
    result = dict(user)
    conn.close()
    return result

# === ROUTES ===

@app.get("/api/me")
def get_me(ref: Optional[str] = None, tg_user=Depends(get_current_user)):
    ref_id = int(ref) if ref and ref.isdigit() else None
    user = get_or_create_user(tg_user, ref_id)
    return user

@app.get("/api/debug/auth")
def debug_auth(x_init_data: str = Header(None)):
    """Отладочный эндпоинт — показывает что пришло в заголовке и результат верификации"""
    if not x_init_data:
        return {"error": "no x-init-data header"}
    result = verify_telegram_data(x_init_data)
    return {
        "raw_length": len(x_init_data),
        "raw_preview": x_init_data[:120],
        "verified": result is not None,
        "user": result,
    }

@app.post("/api/me/photo")
def update_photo(data: dict, tg_user=Depends(get_current_user)):
    conn = get_db()
    conn.execute("UPDATE users SET photo_url = ? WHERE tg_id = ?", 
                 (data.get("photo_url"), tg_user["id"]))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.get("/api/cases")
def get_cases():
    return CASES

@app.post("/api/cases/{case_type}/open")
def open_case(case_type: str, tg_user=Depends(get_current_user)):
    if case_type not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = CASES[case_type]
    user = get_or_create_user(tg_user)
    tg_id = tg_user["id"]
    
    if case_type == "daily":
        today = date.today().isoformat()
        if user.get("last_daily") == today:
            raise HTTPException(status_code=400, detail="Ежедневный кейс уже получен сегодня")
    else:
        price = case["price"]
        if user["balance"] < price:
            raise HTTPException(status_code=400, detail="Недостаточно звёзд")
    
    items = case["items"]
    total = sum(i["chance"] for i in items)
    roll = random.uniform(0, total)
    cumulative = 0
    won_item = items[-1]
    for item in items:
        cumulative += item["chance"]
        if roll <= cumulative:
            won_item = item
            break
    
    conn = get_db()
    c = conn.cursor()
    
    if case_type == "daily":
        c.execute("UPDATE users SET last_daily = ?, balance = balance + ?, total_won = total_won + ?, cases_opened = cases_opened + 1 WHERE tg_id = ?",
                  (date.today().isoformat(), won_item["stars"], won_item["stars"], tg_id))
    else:
        c.execute("UPDATE users SET balance = balance - ? + ?, total_won = total_won + ?, cases_opened = cases_opened + 1 WHERE tg_id = ?",
                  (case["price"], won_item["stars"], won_item["stars"], tg_id))
    
    c.execute("INSERT INTO case_history (tg_id, case_type, item_name, stars_won, rarity) VALUES (?,?,?,?,?)",
              (tg_id, case_type, won_item["name"], won_item["stars"], won_item["rarity"]))
    conn.commit()
    
    user_upd = dict(c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone())
    conn.close()
    
    return {
        "won": won_item,
        "new_balance": user_upd["balance"],
        "spin_items": _generate_spin_sequence(items, won_item)
    }

def _generate_spin_sequence(items, won_item, count=30):
    seq = []
    for _ in range(count - 1):
        seq.append(random.choice(items))
    seq.append(won_item)
    return seq

# === REFERRALS ===

@app.get("/api/referrals")
def get_referrals(tg_user=Depends(get_current_user)):
    tg_id = tg_user["id"]
    conn = get_db()
    user = dict(conn.execute("SELECT referral_count, referral_earned FROM users WHERE tg_id = ?", (tg_id,)).fetchone() or {})
    refs = conn.execute(
        "SELECT first_name, username, created_at FROM users WHERE referred_by = ? ORDER BY created_at DESC LIMIT 50",
        (tg_id,)
    ).fetchall()
    conn.close()
    return {
        "referral_count": user.get("referral_count", 0),
        "referral_earned": user.get("referral_earned", 0),
        "referral_bonus_per_user": 25,
        "referrals": [dict(r) for r in refs]
    }

# === PROMO CODES ===

@app.post("/api/promo/activate")
def activate_promo(data: dict, tg_user=Depends(get_current_user)):
    code = (data.get("code") or "").strip().upper()
    if not code:
        raise HTTPException(status_code=400, detail="Введите промокод")
    
    tg_id = tg_user["id"]
    conn = get_db()
    c = conn.cursor()
    
    promo = c.execute("SELECT * FROM promo_codes WHERE code = ?", (code,)).fetchone()
    if not promo:
        conn.close()
        raise HTTPException(status_code=404, detail="Промокод не найден")
    
    promo = dict(promo)
    
    # Проверить срок
    if promo["expires_at"] and promo["expires_at"] < datetime.now().isoformat():
        conn.close()
        raise HTTPException(status_code=400, detail="Промокод истёк")
    
    # Проверить лимит
    if promo["used_count"] >= promo["max_uses"]:
        conn.close()
        raise HTTPException(status_code=400, detail="Промокод уже исчерпан")
    
    # Проверить повторную активацию
    already = c.execute("SELECT 1 FROM promo_uses WHERE code = ? AND tg_id = ?", (code, tg_id)).fetchone()
    if already:
        conn.close()
        raise HTTPException(status_code=400, detail="Вы уже активировали этот промокод")
    
    stars = promo["stars"]
    c.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (stars, tg_id))
    c.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?", (code,))
    c.execute("INSERT INTO promo_uses (code, tg_id) VALUES (?, ?)", (code, tg_id))
    conn.commit()
    
    user = dict(c.execute("SELECT balance FROM users WHERE tg_id = ?", (tg_id,)).fetchone())
    conn.close()
    
    return {"ok": True, "stars": stars, "new_balance": user["balance"]}

# === ADMIN ===

@app.post("/api/admin/promo/create")
def admin_create_promo(data: dict, tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    
    code = (data.get("code") or "").strip().upper()
    if not code:
        # Генерируем случайный
        code = "GIFT" + "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    stars = int(data.get("stars", 0))
    max_uses = int(data.get("max_uses", 1))
    expires_at = data.get("expires_at")  # ISO строка или null
    
    if stars < 1:
        raise HTTPException(status_code=400, detail="Укажите количество звёзд")
    
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO promo_codes (code, stars, max_uses, expires_at, created_by) VALUES (?,?,?,?,?)",
            (code, stars, max_uses, expires_at, tg_user["id"])
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Такой промокод уже существует")
    conn.close()
    return {"ok": True, "code": code, "stars": stars, "max_uses": max_uses}

@app.get("/api/admin/promos")
def admin_get_promos(tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    conn = get_db()
    promos = conn.execute("SELECT * FROM promo_codes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(p) for p in promos]

@app.delete("/api/admin/promo/{code}")
def admin_delete_promo(code: str, tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    conn = get_db()
    conn.execute("DELETE FROM promo_codes WHERE code = ?", (code.upper(),))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/admin/broadcast")
async def admin_broadcast(data: dict, tg_user=Depends(get_current_user)):
    """Рассылка через бот — вызывает внутренний эндпоинт бота"""
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    
    text = data.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Текст не может быть пустым")
    
    conn = get_db()
    users = conn.execute("SELECT tg_id FROM users").fetchall()
    conn.close()
    
    import httpx
    BOT_TOKEN_VAL = os.getenv("BOT_TOKEN", BOT_TOKEN)
    sent = 0
    failed = 0
    
    async with httpx.AsyncClient(timeout=30) as client:
        for u in users:
            try:
                resp = await client.post(
                    f"https://api.telegram.org/bot{BOT_TOKEN_VAL}/sendMessage",
                    json={
                        "chat_id": u["tg_id"],
                        "text": text,
                        "parse_mode": "HTML"
                    }
                )
                if resp.status_code == 200:
                    sent += 1
                else:
                    failed += 1
            except Exception:
                failed += 1
    
    return {"ok": True, "sent": sent, "failed": failed, "total": len(users)}

@app.post("/api/admin/give-stars")
def admin_give_stars(data: dict, tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403, detail="Нет доступа")
    
    target_id = data["tg_id"]
    amount = int(data["amount"])
    
    conn = get_db()
    conn.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (amount, target_id))
    conn.execute("INSERT INTO transactions (tg_id, type, amount, status) VALUES (?,?,?,?)",
                 (target_id, "admin_gift", amount, "completed"))
    conn.commit()
    conn.close()
    return {"ok": True, "message": f"Выдано {amount} звёзд пользователю {target_id}"}

@app.get("/api/admin/users")
def admin_get_users(tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY balance DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(u) for u in users]

@app.get("/api/admin/transactions")
def admin_get_transactions(tg_user=Depends(get_current_user)):
    if tg_user["id"] not in ADMIN_IDS:
        raise HTTPException(status_code=403)
    conn = get_db()
    txs = conn.execute("SELECT * FROM transactions ORDER BY created_at DESC LIMIT 100").fetchall()
    conn.close()
    return [dict(t) for t in txs]

# === DEPOSIT / WITHDRAW ===

@app.post("/api/deposit/request")
def request_deposit(data: dict, tg_user=Depends(get_current_user)):
    amount = int(data.get("amount", 0))
    if amount < 1:
        raise HTTPException(status_code=400, detail="Минимальное пополнение — 1 звезда")
    
    tg_id = tg_user["id"]
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO transactions (tg_id, type, amount, status) VALUES (?,?,?,?)",
              (tg_id, "deposit", amount, "pending"))
    tx_id = c.lastrowid
    conn.commit()
    conn.close()
    
    bot_username = os.getenv("BOT_USERNAME", "justgift_bot")
    bot_url = f"https://t.me/{bot_username}?start=pay_{tx_id}_{amount}"
    return {"tx_id": tx_id, "bot_url": bot_url, "amount": amount}

@app.post("/api/deposit/confirm")
def confirm_deposit(data: dict):
    secret = data.get("secret")
    if secret != os.getenv("INTERNAL_SECRET", "justgift_internal_secret"):
        raise HTTPException(status_code=403)
    
    tx_id = data["tx_id"]
    tg_id = data["tg_id"]
    amount = data["amount"]
    
    conn = get_db()
    conn.execute("UPDATE transactions SET status = 'completed' WHERE id = ? AND tg_id = ?", (tx_id, tg_id))
    conn.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (amount, tg_id))
    conn.commit()
    conn.close()
    return {"ok": True}

@app.post("/api/withdraw/request")
def request_withdraw(data: dict, tg_user=Depends(get_current_user)):
    amount = int(data.get("amount", 0))
    tg_id = tg_user["id"]
    
    user = get_or_create_user(tg_user)
    if user["balance"] < amount:
        raise HTTPException(status_code=400, detail="Недостаточно звёзд")
    if amount < 50:
        raise HTTPException(status_code=400, detail="Минимальный вывод — 50 звёзд")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance - ? WHERE tg_id = ?", (amount, tg_id))
    c.execute("INSERT INTO transactions (tg_id, type, amount, status) VALUES (?,?,?,?)",
              (tg_id, "withdraw", amount, "pending"))
    tx_id = c.lastrowid
    conn.commit()
    conn.close()
    
    bot_username = os.getenv("BOT_USERNAME", "justgift_bot")
    bot_url = f"https://t.me/{bot_username}?start=withdraw_{tx_id}_{amount}"
    return {"tx_id": tx_id, "bot_url": bot_url, "amount": amount}

@app.get("/api/history")
def get_history(tg_user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM case_history WHERE tg_id = ? ORDER BY created_at DESC LIMIT 20",
        (tg_user["id"],)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
