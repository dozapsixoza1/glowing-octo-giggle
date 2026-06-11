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
DB_PATH = "justgift.db"

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
    conn.commit()
    conn.close()

init_db()

# === AUTH ===
def verify_telegram_data(init_data: str) -> Optional[dict]:
    """Verify Telegram WebApp init data"""
    try:
        parsed = {}
        for item in init_data.split("&"):
            if "=" in item:
                k, v = item.split("=", 1)
                parsed[k] = v
        
        hash_val = parsed.pop("hash", None)
        if not hash_val:
            return None
        
        data_check = "\n".join(sorted([f"{k}={v}" for k, v in parsed.items()]))
        secret = hmac.new("WebAppData".encode(), BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret, data_check.encode(), hashlib.sha256).hexdigest()
        
        if computed == hash_val:
            user_str = parsed.get("user", "{}")
            return json.loads(user_str)
        return None
    except Exception:
        return None

def get_current_user(x_init_data: str = Header(None)):
    if not x_init_data:
        raise HTTPException(status_code=401, detail="No auth")
    
    # Dev mode — accept plain user_id for testing
    if x_init_data.startswith("dev:"):
        tg_id = int(x_init_data.split(":")[1])
        return {"id": tg_id, "first_name": "Dev User"}
    
    user = verify_telegram_data(x_init_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth")
    return user

def get_or_create_user(tg_user: dict) -> dict:
    conn = get_db()
    c = conn.cursor()
    tg_id = tg_user["id"]
    
    user = c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    if not user:
        c.execute(
            "INSERT INTO users (tg_id, username, first_name, last_name) VALUES (?,?,?,?)",
            (tg_id, tg_user.get("username"), tg_user.get("first_name"), tg_user.get("last_name"))
        )
        conn.commit()
        user = c.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)).fetchone()
    
    result = dict(user)
    conn.close()
    return result

# === ROUTES ===

@app.get("/api/me")
def get_me(tg_user=Depends(get_current_user)):
    user = get_or_create_user(tg_user)
    return user

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
    import random
    
    if case_type not in CASES:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = CASES[case_type]
    user = get_or_create_user(tg_user)
    tg_id = tg_user["id"]
    
    # Daily case check
    if case_type == "daily":
        today = date.today().isoformat()
        if user.get("last_daily") == today:
            raise HTTPException(status_code=400, detail="Ежедневный кейс уже получен сегодня")
    else:
        # Check balance
        price = case["price"]
        if user["balance"] < price:
            raise HTTPException(status_code=400, detail="Недостаточно звёзд")
    
    # Spin the wheel
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
    
    # Update DB
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
    import random
    seq = []
    for _ in range(count - 1):
        seq.append(random.choice(items))
    seq.append(won_item)
    return seq

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
    """Called by bot after payment received"""
    secret = data.get("secret")
    if secret != os.getenv("INTERNAL_SECRET", "justgift_internal_secret"):
        raise HTTPException(status_code=403)
    
    tx_id = data["tx_id"]
    tg_id = data["tg_id"]
    amount = data["amount"]
    
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE transactions SET status = 'completed' WHERE id = ? AND tg_id = ?", (tx_id, tg_id))
    c.execute("UPDATE users SET balance = balance + ? WHERE tg_id = ?", (amount, tg_id))
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

# === ADMIN ===
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
