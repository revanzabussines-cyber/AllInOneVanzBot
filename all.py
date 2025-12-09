import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta, date

from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ======================================
# CONFIG
# ======================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN wajib diisi di environment variable!")

# GANTI KE ID TELEGRAM LU SENDIRI
ADMIN_IDS = {7321522905}  # ganti kalau ID lu beda

BASE = Path(__file__).parent
PREMIUM_FILE = BASE / "premium.json"
HISTORY_FILE = BASE / "history.json"
LANG_FILE = BASE / "language.json"  # simpan bahasa user

# ---------- FILE STOK ----------
# stok_canva.txt, stok_capcut.txt, dst tetap
STOK_CANVA = BASE / "stok_canva.txt"
STOK_CAPCUT = BASE / "stok_capcut.txt"
STOK_SCRIBD = BASE / "stok_scribd.txt"
STOK_APPLE = BASE / "stok_apple.txt"

# INI YANG DISAMBUNG KE UBOT:
STOK_VIU = BASE / "stok_viu.txt"   # hasil farmer VIU
STOK_VIDIO = BASE / "stok_vidio.txt"

# AM / Alight Motion → ubot biasanya pakai "stok_am.txt"
STOK_ALIGHT = BASE / "stok_am.txt"  # <--- penting: sesuaikan dengan file ubot

# Nama produk untuk tampilan
PRODUCTS = {
    "CANVA": "Canva Kosongan",
    "CAPCUT": "CapCut Kosongan",
    "SCRIBD": "Scribd Premium",
    "APPLE": "Apple Music Kosongan",
    "VIU": "Viu Premium 1 Tahun",
    "VIDIO": "Vidio Platinum 1 TV",
    "ALIGHT": "Alight Motion 1 Tahun",
}

# Limit per produk per hari (per user)
PRODUCT_LIMIT = {
    "CANVA": 50,
    "CAPCUT": 100,
    "SCRIBD": 10,
    "APPLE": 30,
    "VIU": 15,
    "VIDIO": 10,
    "ALIGHT": 15,
}

# ======================================
# TEKS PLAN (ID & EN)
# ======================================

PLAN_TEXTS_ID = {
    "CAPCUT": (
        "🎬 <b>Plan CapCut Kosongan</b>\n"
        "Limit: <b>100 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>5K</b>\n"
        "• Medium — 7 Hari  • <b>10K</b>\n"
        "• High — 14 Hari  • <b>15K</b>\n\n"
        "Cocok untuk jasa edit & reseller akun CapCut."
    ),
    "CANVA": (
        "🎨 <b>Plan Canva Kosongan</b>\n"
        "Limit: <b>50 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>10K</b>\n"
        "• Medium — 7 Hari  • <b>18K</b>\n"
        "• High — 14 Hari  • <b>30K</b>\n\n"
        "Cocok untuk desain, jual jasa template, dsb."
    ),
    "SCRIBD": (
        "📚 <b>Plan Scribd Premium</b>\n"
        "Limit: <b>10 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>15K</b>\n"
        "• Medium — 7 Hari  • <b>30K</b>\n"
        "• High — 14 Hari  • <b>55K</b>\n\n"
        "Cocok buat akses dokumen & e-book premium."
    ),
    "APPLE": (
        "🎵 <b>Plan Apple Music Kosongan</b>\n"
        "Limit: <b>30 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>7K</b>\n"
        "• Medium — 7 Hari  • <b>12K</b>\n"
        "• High — 14 Hari  • <b>20K</b>\n\n"
        "Cocok buat kebutuhan musik & trial loop."
    ),
    "VIU": (
        "🎬 <b>Plan Viu Premium 1 Tahun</b>\n"
        "Limit: <b>15 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>15K</b>\n"
        "• Medium — 7 Hari  • <b>25K</b>\n"
        "• High — 14 Hari  • <b>35K</b>\n\n"
        "Cocok untuk pecinta drama & film."
    ),
    "VIDIO": (
        "📺 <b>Plan Vidio Platinum 1 TV</b>\n"
        "Limit: <b>10 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>20K</b>\n"
        "• Medium — 7 Hari  • <b>30K</b>\n"
        "• High — 14 Hari  • <b>40K</b>\n\n"
        "Cocok buat nonton bola, F1, dan sport lain."
    ),
    "ALIGHT": (
        "🎥 <b>Plan Alight Motion 1 Tahun</b>\n"
        "Limit: <b>15 akun/hari</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>15K</b>\n"
        "• Medium — 7 Hari  • <b>25K</b>\n"
        "• High — 14 Hari  • <b>35K</b>\n\n"
        "Cocok buat editor video mobile & jasa preset."
    ),
    "ALL": (
        "💎 <b>Plan ALL ACCESS (Semua Produk)</b>\n"
        "Termasuk: CapCut, Canva, Scribd, Apple Music, Viu, Vidio, Alight Motion.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Hari  • <b>25K</b>\n"
        "• Medium — 7 Hari  • <b>45K</b>\n"
        "• High — 14 Hari  • <b>75K</b>\n\n"
        "Paket paling hemat untuk reseller & jasa besar."
    ),
}

PLAN_TEXTS_EN = {
    "CAPCUT": (
        "🎬 <b>CapCut Blank Plan</b>\n"
        "Limit: <b>100 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>5K</b>\n"
        "• Medium — 7 Days  • <b>10K</b>\n"
        "• High — 14 Days  • <b>15K</b>\n\n"
        "Great for editors & CapCut resellers."
    ),
    "CANVA": (
        "🎨 <b>Canva Blank Plan</b>\n"
        "Limit: <b>50 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>10K</b>\n"
        "• Medium — 7 Days  • <b>18K</b>\n"
        "• High — 14 Days  • <b>30K</b>\n\n"
        "Perfect for designers and template sellers."
    ),
    "SCRIBD": (
        "📚 <b>Scribd Premium Plan</b>\n"
        "Limit: <b>10 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>15K</b>\n"
        "• Medium — 7 Days  • <b>30K</b>\n"
        "• High — 14 Days  • <b>55K</b>\n\n"
        "Great for ebook & document access."
    ),
    "APPLE": (
        "🎵 <b>Apple Music Blank Plan</b>\n"
        "Limit: <b>30 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>7K</b>\n"
        "• Medium — 7 Days  • <b>12K</b>\n"
        "• High — 14 Days  • <b>20K</b>\n\n"
        "Good for music needs & trial loops."
    ),
    "VIU": (
        "🎬 <b>Viu Premium 1 Year Plan</b>\n"
        "Limit: <b>15 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>15K</b>\n"
        "• Medium — 7 Days  • <b>25K</b>\n"
        "• High — 14 Days  • <b>35K</b>\n\n"
        "Great for drama and movie lovers."
    ),
    "VIDIO": (
        "📺 <b>Vidio Platinum 1 TV Plan</b>\n"
        "Limit: <b>10 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>20K</b>\n"
        "• Medium — 7 Days  • <b>30K</b>\n"
        "• High — 14 Days  • <b>40K</b>\n\n"
        "Perfect for sports and live matches."
    ),
    "ALIGHT": (
        "🎥 <b>Alight Motion 1 Year Plan</b>\n"
        "Limit: <b>15 accounts/day</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>15K</b>\n"
        "• Medium — 7 Days  • <b>25K</b>\n"
        "• High — 14 Days  • <b>35K</b>\n\n"
        "Ideal for mobile video editors."
    ),
    "ALL": (
        "💎 <b>ALL ACCESS Plan (All Products)</b>\n"
        "Includes: CapCut, Canva, Scribd, Apple Music, Viu, Vidio, Alight Motion.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Lite — 3 Days  • <b>25K</b>\n"
        "• Medium — 7 Days  • <b>45K</b>\n"
        "• High — 14 Days  • <b>75K</b>\n\n"
        "Best value for resellers and services."
    ),
}

# ======================================
# JSON HELPERS
# ======================================

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ======================================
# LANGUAGE SYSTEM
# ======================================

def get_lang(uid: int) -> str:
    db = load_json(LANG_FILE, {})
    return db.get(str(uid), "id")  # default Indonesia


def set_lang(uid: int, lang: str):
    if lang not in ("id", "en"):
        lang = "id"
    db = load_json(LANG_FILE, {})
    db[str(uid)] = lang
    save_json(LANG_FILE, db)

# ======================================
# PREMIUM SYSTEM
# ======================================

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS


def get_premium_db():
    return load_json(PREMIUM_FILE, {})


def save_premium_db(db):
    save_json(PREMIUM_FILE, db)


def is_premium(uid: int) -> bool:
    db = get_premium_db()
    rec = db.get(str(uid))
    if not rec:
        return False
    exp = rec.get("expire_at")
    if not exp:
        return False
    try:
        exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
    except ValueError:
        return False
    return date.today() <= exp_date


def get_sisa_sewa(uid: int) -> int:
    db = get_premium_db()
    rec = db.get(str(uid), {})
    exp = rec.get("expire_at")
    if not exp:
        return 0
    try:
        exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
    except ValueError:
        return 0
    return max((exp_date - date.today()).days, 0)


def update_quota(uid: int):
    """
    Simpan quota per produk di premium.json:
    {
      "uid": {
        "expire_at": "...",
        "quota": {
          "CANVA": {"date": "2025-01-10", "count": 0},
          ...
        },
        "total_generated": 0
      }
    }
    """
    today = date.today().strftime("%Y-%m-%d")
    db = get_premium_db()
    rec = db.get(str(uid), {
        "expire_at": None,
        "quota": {},
        "total_generated": 0,
    })

    quota = rec.get("quota", {})
    # reset harian jika beda tanggal
    for p_key in PRODUCT_LIMIT.keys():
        entry = quota.get(p_key, {"date": today, "count": 0})
        if entry.get("date") != today:
            entry["date"] = today
            entry["count"] = 0
        quota[p_key] = entry

    rec["quota"] = quota
    db[str(uid)] = rec
    save_premium_db(db)
    return rec


def increment_quota(uid: int, produk_key: str):
    db = get_premium_db()
    rec = db.get(str(uid))
    if not rec:
        return
    quota = rec.get("quota", {})
    today = date.today().strftime("%Y-%m-%d")
    entry = quota.get(produk_key, {"date": today, "count": 0})
    if entry.get("date") != today:
        entry["date"] = today
        entry["count"] = 0
    entry["count"] = entry.get("count", 0) + 1
    quota[produk_key] = entry
    rec["quota"] = quota
    rec["total_generated"] = rec.get("total_generated", 0) + 1
    db[str(uid)] = rec
    save_premium_db(db)


def get_quota_info(uid: int, produk_key: str):
    db = get_premium_db()
    rec = db.get(str(uid))
    if not rec:
        return 0, PRODUCT_LIMIT.get(produk_key, 0)
    quota = rec.get("quota", {})
    entry = quota.get(produk_key)
    if not entry:
        return 0, PRODUCT_LIMIT.get(produk_key, 0)
    today = date.today().strftime("%Y-%m-%d")
    if entry.get("date") != today:
        return 0, PRODUCT_LIMIT.get(produk_key, 0)
    used = entry.get("count", 0)
    limit = PRODUCT_LIMIT.get(produk_key, 0)
    return used, limit


def grant_premium_days(uid: int, days: int) -> date:
    db = get_premium_db()
    today = date.today()
    rec = db.get(str(uid), {})
    if rec.get("expire_at"):
        try:
            old_exp = datetime.strptime(rec["expire_at"], "%Y-%m-%d").date()
        except ValueError:
            old_exp = today
    else:
        old_exp = today
    new_expire = max(old_exp, today) + timedelta(days=days)

    rec["expire_at"] = new_expire.strftime("%Y-%m-%d")
    # reset quota hari ini
    rec["quota"] = {}
    rec["total_generated"] = rec.get("total_generated", 0)
    db[str(uid)] = rec
    save_premium_db(db)
    return new_expire

# ======================================
# HISTORY SYSTEM
# ======================================

def get_history(uid: int):
    db = load_json(HISTORY_FILE, {})
    return db.get(str(uid), [])


def add_history(uid: int, akun: str, produk: str):
    db = load_json(HISTORY_FILE, {})
    lst = db.get(str(uid), [])
    lst.append({"akun": akun, "produk": produk})
    db[str(uid)] = lst
    save_json(HISTORY_FILE, db)

# ======================================
# STOK HANDLER (internal)
# ======================================

def get_stok_file(produk_key: str) -> Path:
    if produk_key == "CANVA":
        return STOK_CANVA
    if produk_key == "CAPCUT":
        return STOK_CAPCUT
    if produk_key == "SCRIBD":
        return STOK_SCRIBD
    if produk_key == "APPLE":
        return STOK_APPLE
    if_produk = produk_key  # just to keep local
    if produk_key == "VIU":
        return STOK_VIU
    if produk_key == "VIDIO":
        return STOK_VIDIO
    if produk_key == "ALIGHT":
        return STOK_ALIGHT
    # fallback
    return STOK_CAPCUT


def ambil_satu_akun(produk_key: str):
    stok_file = get_stok_file(produk_key)
    if not stok_file.exists():
        return None

    lines = [l.strip() for l in stok_file.read_text().splitlines() if l.strip()]
    if not lines:
        return None

    akun = lines[0]
    sisa = lines[1:]

    with stok_file.open("w", encoding="utf-8") as f:
        for s in sisa:
            f.write(s + "\n")

    return akun


def count_stok(produk_key: str) -> int:
    """Hitung sisa stok akun di file stok."""
    stok_file = get_stok_file(produk_key)
    if not stok_file.exists():
        return 0
    lines = [l.strip() for l in stok_file.read_text().splitlines() if l.strip()]
    return len(lines)

# ======================================
# KEYBOARD LAYOUTS
# ======================================

def main_keyboard():
    """Menu utama: pilih jenis generator / info."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("◆ Generate Kosongan", callback_data="GEN_BLANK")],
        [InlineKeyboardButton("💎 Generate Premium", callback_data="GEN_PREMIUM")],
        [
            InlineKeyboardButton("📦 Riwayat Akun", callback_data="SAVED"),
            InlineKeyboardButton("💸 Harga Sewa", callback_data="PLANS"),
        ],
        [
            InlineKeyboardButton("🆘 Bantuan", callback_data="HELP"),
            InlineKeyboardButton("👑 Admin @VanzzSkyyID", url="https://t.me/VanzzSkyyID"),
        ],
    ])


def blank_keyboard():
    """Submenu generator kosongan."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎨 Canva Kosongan", callback_data="P_CANVA"),
            InlineKeyboardButton("🎬 CapCut Kosongan", callback_data="P_CAPCUT"),
        ],
        [
            InlineKeyboardButton("🎵 Apple Music Kosongan", callback_data="P_APPLE"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali ke menu utama", callback_data="BACK_HOME"),
        ],
    ])


def premium_keyboard():
    """Submenu generator premium."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📚 Scribd Premium", callback_data="P_SCRIBD"),
            InlineKeyboardButton("🎬 Viu Premium 1 Tahun", callback_data="P_VIU"),
        ],
        [
            InlineKeyboardButton("📺 Vidio Platinum 1 TV", callback_data="P_VIDIO"),
            InlineKeyboardButton("🎥 Alight Motion 1 Tahun", callback_data="P_ALIGHT"),
        ],
        [
            InlineKeyboardButton("⬅️ Kembali ke menu utama", callback_data="BACK_HOME"),
        ],
    ])

# ======================================
# /START
# ======================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    uid = user.id
    lang = get_lang(uid)
    nama = user.first_name or (user.username or "User")

    # Role info
    if is_admin(uid):
        role_id = "Admin"
        role_en = "Admin"
    elif is_premium(uid):
        role_id = "Premium"
        role_en = "Premium"
    else:
        role_id = "Free User"
        role_en = "Free User"

    if lang == "en":
        text = (
            "🌌 <b>VANZSTORE.ID — Multi Generator Bot</b> 🚀\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Welcome, <b>{nama}</b>!\n"
            f"🎯 Status: <b>{role_en}</b>\n\n"
            "This bot helps you generate ready-to-use accounts automatically.\n"
            "Each account is prepared via an internal generator engine.\n\n"
            "Use the menu below to start:\n"
            "• ⚙️ Blank Generator (Canva, CapCut, Apple Music)\n"
            "• 💎 Premium Generator (Scribd, Viu, Vidio, Alight Motion)\n\n"
            "Choose what you want to generate:"
        )
    else:
        text = (
            "🌌 <b>VANZSTORE.ID — Multi Generator Bot</b> 🚀\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Welcome, <b>{nama}</b>!\n"
            f"🎯 Status: <b>{role_id}</b>\n\n"
            "Bot ini membantu kamu membuat akun-akun siap pakai secara otomatis.\n"
            "Setiap akun diproses lewat sistem generator internal, bukan manual.\n\n"
            "Gunakan menu di bawah untuk mulai:\n"
            "• ⚙️ Generator Kosongan (Canva, CapCut, Apple Music)\n"
            "• 💎 Generator Premium (Scribd, Viu, Vidio, Alight Motion)\n\n"
            "Pilih aksi yang kamu mau:"
        )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard(),
        parse_mode="HTML",
    )

# ======================================
# CALLBACK BUTTONS
# ======================================

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    lang = get_lang(uid)
    data = q.data

    # menu kategori
    if data == "GEN_BLANK":
        if lang == "en":
            msg = (
                "⚙️ <b>Blank Generator</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Choose which blank service you want to generate:"
            )
        else:
            msg = (
                "⚙️ <b>Generator Kosongan</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Pilih layanan kosongan yang mau kamu generate:"
            )
        await q.message.edit_text(msg, reply_markup=blank_keyboard(), parse_mode="HTML")
        return

    if data == "GEN_PREMIUM":
        if lang == "en":
            msg = (
                "💎 <b>Premium Generator</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Choose which premium service you want to generate:"
            )
        else:
            msg = (
                "💎 <b>Generator Premium</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "Pilih layanan premium yang mau kamu generate:"
            )
        await q.message.edit_text(msg, reply_markup=premium_keyboard(), parse_mode="HTML")
        return

    if data == "PLANS":
        await show_plans_menu(q, lang)
        return

    # STEP 1: pilih produk
    if data.startswith("P_"):
        produk_key = data.split("_", 1)[1]  # P_CANVA -> CANVA
        produk_nama = PRODUCTS.get(produk_key, produk_key)
        await show_quantity_menu(q, produk_key, produk_nama, lang)
        return

    # STEP 2: pilih jumlah setelah produk
    if data.startswith("Q_"):
        # format: Q_CANVA_10
        try:
            _, produk_key, qty_str = data.split("_", 2)
            jumlah = int(qty_str)
        except Exception:
            if lang == "en":
                await q.message.reply_text("Unknown button format. Please /start again.")
            else:
                await q.message.reply_text("Format tombol tidak dikenal. Coba /start lagi.")
            return

        produk_nama = PRODUCTS.get(produk_key, produk_key)
        await generate_multiple(q, uid, produk_key, produk_nama, jumlah, lang)
        return

    # tombol lihat harga plan detail
    if data.startswith("PLAN_"):
        key = data.split("_", 1)[1]
        if lang == "en":
            plan_text = PLAN_TEXTS_EN.get(key)
        else:
            plan_text = PLAN_TEXTS_ID.get(key)

        if not plan_text:
            msg = "Paket sewa tidak ditemukan." if lang == "id" else "Plan not found."
            await q.message.reply_text(msg)
            return

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Pilih layanan lain" if lang == "id" else "⬅️ Choose other service",
                    callback_data="BACK_PLANS",
                ),
                InlineKeyboardButton(
                    "⬅️ Kembali ke menu utama" if lang == "id" else "⬅️ Back to main",
                    callback_data="BACK_HOME",
                ),
            ],
        ])

        await q.message.edit_text(
            plan_text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    if data == "BACK_PLANS":
        await show_plans_menu(q, lang)
        return

    # menu lain
    if data == "SAVED":
        await show_saved(q, uid, lang)
    elif data == "SEWA":
        await show_sewa(q, uid, lang)
    elif data == "HELP":
        await show_help(q, lang)
    elif data == "BACK_HOME":
        if lang == "en":
            text = (
                "⬅️ Back to main menu.\n\n"
                "Choose what you want to do:"
            )
        else:
            text = (
                "⬅️ Kembali ke menu utama.\n\n"
                "Silakan pilih aksi yang kamu mau:"
            )
        await q.message.edit_text(
            text,
            reply_markup=main_keyboard(),
            parse_mode="HTML",
        )

# ======================================
# MENU PILIH JUMLAH
# ======================================

async def show_quantity_menu(q, produk_key: str, produk_nama: str, lang: str):
    if lang == "en":
        msg = (
            f"✨ You chose: <b>{produk_nama}</b>\n\n"
            "Select how many accounts you want to generate:"
        )
        btn10 = "🔟 Generate 10 accounts"
        btn20 = "2️⃣0️⃣ Generate 20 accounts"
        back = "⬅️ Back to main menu"
    else:
        msg = (
            f"✨ Kamu memilih: <b>{produk_nama}</b>\n\n"
            "Pilih berapa banyak akun yang mau kamu generate:"
        )
        btn10 = "🔟 Generate 10 akun"
        btn20 = "2️⃣0️⃣ Generate 20 akun"
        back = "⬅️ Kembali ke menu utama"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(btn10, callback_data=f"Q_{produk_key}_10"),
            InlineKeyboardButton(btn20, callback_data=f"Q_{produk_key}_20"),
        ],
        [
            InlineKeyboardButton(back, callback_data="BACK_HOME"),
        ],
    ])

    await q.message.edit_text(
        msg,
        reply_markup=keyboard,
        parse_mode="HTML",
    )

# ======================================
# GENERATE MULTI AKUN
# ======================================

async def generate_multiple(q, uid: int, produk_key: str, produk_nama: str, jumlah_awal: int, lang: str):
    # cek akses premium / admin
    if not (is_admin(uid) or is_premium(uid)):
        if lang == "en":
            text = (
                "🚫 Your premium access is not active yet.\n"
                "Please contact admin to activate your plan."
            )
        else:
            text = (
                "🚫 Akses premium kamu belum aktif.\n"
                "Silakan hubungi admin untuk aktivasi."
            )
        await q.message.reply_text(text)
        return

    update_quota(uid)
    jumlah = jumlah_awal

    # cek limit per produk (kecuali admin)
    if not is_admin(uid):
        used, limit = get_quota_info(uid, produk_key)
        sisa = limit - used
        if sisa <= 0:
            if lang == "en":
                text = (
                    f"❌ Your daily limit for {produk_nama} is already reached.\n"
                    "Please try again tomorrow."
                )
            else:
                text = (
                    f"❌ Limit harian kamu untuk {produk_nama} sudah tercapai.\n"
                    "Kamu bisa generate lagi besok."
                )
            await q.message.reply_text(text)
            return
        if jumlah > sisa:
            jumlah = sisa

    # notif proses
    if lang == "en":
        proses_msg = await q.message.reply_text(
            f"🔄 <b>{produk_nama} Generator</b>\n"
            f"⏳ Preparing <b>{jumlah}</b> accounts for you...\n\n"
            "Please wait, the system is configuring your credentials.",
            parse_mode="HTML",
        )
    else:
        proses_msg = await q.message.reply_text(
            f"🔄 <b>Generator {produk_nama}</b>\n"
            f"⏳ Menyiapkan <b>{jumlah}</b> akun untuk kamu...\n\n"
            "Mohon tunggu, sistem sedang mengonfigurasi kredensial akun kamu.",
            parse_mode="HTML",
        )

    hasil = []

    for _ in range(jumlah):
        akun = ambil_satu_akun(produk_key)
        if not akun:
            break
        hasil.append(akun)
        increment_quota(uid, produk_key)
        add_history(uid, akun, produk_nama)
        # anti-spam delay
        await asyncio.sleep(0.6)

    if not hasil:
        if lang == "en":
            text = (
                f"😿 Account quota for <b>{produk_nama}</b> is currently unavailable.\n"
                "Please contact admin if you need more accounts."
            )
        else:
            text = (
                f"😿 Kuota akun untuk <b>{produk_nama}</b> sedang tidak tersedia.\n"
                "Silakan hubungi admin jika kamu membutuhkan tambahan akun."
            )
        await proses_msg.edit_text(text, parse_mode="HTML")
        return

    lines = []
    for i, a in enumerate(hasil, start=1):
        lines.append(f"{i}. <code>{a}</code>")
    daftar = "\n".join(lines)

    if lang == "en":
        text = (
            f"✅ <b>{produk_nama} generation complete!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Accounts in this batch: <b>{len(hasil)}</b>\n\n"
            f"{daftar}\n\n"
            "🔁 All these accounts are also stored in your <b>History</b> menu."
        )
    else:
        text = (
            f"✅ <b>Generate {produk_nama} selesai!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Jumlah akun di batch ini: <b>{len(hasil)}</b>\n\n"
            f"{daftar}\n\n"
            "🔁 Semua akun ini juga tersimpan di menu <b>Riwayat Akun</b> kamu."
        )

    await proses_msg.edit_text(text, parse_mode="HTML")

# ======================================
# RIWAYAT, SEWA, HELP
# ======================================

async def show_saved(q, uid: int, lang: str):
    hist = get_history(uid)
    if not hist:
        if lang == "en":
            text = (
                "📦 History is empty.\n"
                "You haven't generated any account yet."
            )
        else:
            text = (
                "📦 Riwayat kosong.\n"
                "Kamu belum pernah generate akun dari bot ini."
            )
        await q.message.reply_text(text)
        return

    lines = [
        f"{i+1}. [{h['produk']}] <code>{h['akun']}</code>"
        for i, h in enumerate(hist)
    ]

    if lang == "en":
        text = (
            "📦 <b>Your Account History</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total accounts you have generated: <b>{len(hist)}</b>\n\n"
            + "\n".join(lines)
        )
    else:
        text = (
            "📦 <b>Riwayat Akun Kamu</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Total akun yang pernah kamu ambil: <b>{len(hist)}</b>\n\n"
            + "\n".join(lines)
        )

    await q.message.reply_text(text, parse_mode="HTML")


async def show_sewa(q, uid: int, lang: str):
    if is_admin(uid):
        if lang == "en":
            text = (
                "👑 You are admin.\n"
                "Your generator access is not limited by subscription."
            )
        else:
            text = (
                "👑 Kamu adalah admin.\n"
                "Akses generator kamu tidak dibatasi masa sewa."
            )
        await q.message.reply_text(text)
        return

    if not is_premium(uid):
        if lang == "en":
            text = (
                "⏳ Your premium access is not active.\n"
                "Please contact admin to buy or renew a plan."
            )
        else:
            text = (
                "⏳ Akses premium kamu belum aktif.\n"
                "Silakan hubungi admin untuk beli / perpanjang paket."
            )
        await q.message.reply_text(text)
        return

    sisa = get_sisa_sewa(uid)
    db = get_premium_db()
    rec = db.get(str(uid), {})
    quota = rec.get("quota", {})

    if lang == "en":
        text = (
            "⏳ <b>Your Premium Status</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Remaining active days: <b>{sisa} day(s)</b>\n\n"
            "Daily usage by product (today):\n"
        )
    else:
        text = (
            "⏳ <b>Status Sewa Premium</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"• Sisa masa aktif: <b>{sisa} hari</b>\n\n"
            "Pemakaian harian per produk (hari ini):\n"
        )

    today = date.today().strftime("%Y-%m-%d")
    lines = []
    for p_key, p_name in PRODUCTS.items():
        limit = PRODUCT_LIMIT.get(p_key, 0)
        entry = quota.get(p_key, {})
        cnt = entry.get("count", 0) if entry.get("date") == today else 0
        lines.append(f"• {p_name}: <b>{cnt}/{limit}</b>")

    text += "\n".join(lines)

    await q.message.reply_text(text, parse_mode="HTML")


async def show_help(q, lang: str):
    if lang == "en":
        text = (
            "🆘 <b>Quick Guide</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Use /start → choose Blank or Premium generator.\n"
            "2️⃣ Pick the service (Canva, CapCut, Scribd, etc.).\n"
            "3️⃣ Choose how many accounts you want (10 or 20).\n"
            "4️⃣ Wait for the generator to finish, accounts will appear.\n"
            "5️⃣ All generated accounts are stored in 📦 History.\n\n"
            "For price & rental plans, use /plans or the 💸 Harga Sewa button.\n"
            "For support, tap the Admin button on the main menu."
        )
    else:
        text = (
            "🆘 <b>Panduan Singkat</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "1️⃣ Gunakan /start → pilih Generator Kosongan atau Premium.\n"
            "2️⃣ Pilih layanan (Canva, CapCut, Scribd, dll).\n"
            "3️⃣ Pilih jumlah akun yang mau digenerate (10 atau 20).\n"
            "4️⃣ Tunggu proses generator selesai, akun akan muncul.\n"
            "5️⃣ Semua akun yang pernah kamu ambil tersimpan di 📦 Riwayat Akun.\n\n"
            "Untuk harga & paket sewa gunakan /plans atau tombol 💸 Harga Sewa.\n"
            "Untuk bantuan, gunakan tombol Admin di menu utama."
        )

    await q.message.reply_text(text, parse_mode="HTML")

# ======================================
# /PLANS
# ======================================

async def show_plans_menu_from_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    await show_plans_menu(update, lang)


async def show_plans_menu(target, lang: str):
    if lang == "en":
        text = (
            "💸 <b>Rental Plans — VANZSTORE.ID</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Choose which service you want to see the rental plans for.\n\n"
            "Tap a button below to see Lite / Medium / High details.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 <b>Premium Highlight:</b>\n\n"
            "🔥 Alight Motion 1 Year — premium editor for mobile video\n"
            "🔥 Vidio Platinum 1 Year — full sports & entertainment\n"
            "🔥 Scribd Premium — global ebooks & documents access\n\n"
            "These services are part of <b>ALL PREMIUM</b> and included in 💎 All Access.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
        back_main = "⬅️ Back to main menu"
    else:
        text = (
            "💸 <b>Paket Sewa — VANZSTORE.ID</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "Pilih layanan yang ingin kamu lihat paket sewanya.\n\n"
            "Klik salah satu tombol di bawah untuk melihat detail plan Lite / Medium / High.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 <b>Premium Highlight:</b>\n\n"
            "🔥 Alight Motion 1 Tahun — editor premium untuk video mobile\n"
            "🔥 Vidio Platinum 1 Tahun — paket lengkap sport & hiburan\n"
            "🔥 Scribd Premium — akses dokumen & e-book global\n\n"
            "Layanan di atas masuk kategori <b>ALL PREMIUM</b>\n"
            "dan tersedia juga di paket 💎 All Access.\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
        back_main = "⬅️ Kembali ke menu utama"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🎬 CapCut", callback_data="PLAN_CAPCUT"),
            InlineKeyboardButton("🎨 Canva", callback_data="PLAN_CANVA"),
        ],
        [
            InlineKeyboardButton("📚 Scribd", callback_data="PLAN_SCRIBD"),
            InlineKeyboardButton("🎵 Apple Music", callback_data="PLAN_APPLE"),
        ],
        [
            InlineKeyboardButton("🎬 Viu 1 Tahun", callback_data="PLAN_VIU"),
            InlineKeyboardButton("📺 Vidio Platinum", callback_data="PLAN_VIDIO"),
        ],
        [
            InlineKeyboardButton("🎥 Alight Motion", callback_data="PLAN_ALIGHT"),
            InlineKeyboardButton("💎 All Access", callback_data="PLAN_ALL"),
        ],
        [
            InlineKeyboardButton(back_main, callback_data="BACK_HOME"),
        ],
    ])

    # target bisa Update (dari /plans) atau CallbackQuery (dari tombol PLANS)
    if isinstance(target, Update):
        msg = target.message
        await msg.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        msg = target.message
        await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")

# ======================================
# ADMIN COMMANDS (PREMIUM & STOK)
# ======================================

async def addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Format: /addpremium <user_id> <hari>")
        return

    try:
        uid = int(context.args[0])
        hari = int(context.args[1])
    except ValueError:
        await update.message.reply_text("User ID dan hari harus berupa angka.")
        return

    new_expire = grant_premium_days(uid, hari)
    await update.message.reply_text(
        f"✅ Premium user {uid} aktif sampai {new_expire}"
    )


async def delpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("Format: /delpremium <user_id>")
        return

    uid_str = context.args[0]
    db = get_premium_db()
    if uid_str in db:
        db.pop(uid_str)
        save_premium_db(db)
        await update.message.reply_text("✅ User tersebut dihapus dari premium.")
    else:
        await update.message.reply_text("User tidak ditemukan di list premium.")


async def listpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    db = get_premium_db()
    if not db:
        await update.message.reply_text("Belum ada user premium.")
        return

    lines = []
    for uid, rec in db.items():
        exp = rec.get("expire_at", "-")
        total = rec.get("total_generated", 0)
        lines.append(f"• {uid} | exp: {exp} | total: {total}")

    text = (
        "👑 <b>Daftar User Premium</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n" + "\n".join(lines)
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def stok_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hanya admin yang bisa pakai /stok, user lain di-silent."""
    uid = update.effective_user.id
    if not is_admin(uid):
        return

    lines = []
    for key, name in PRODUCTS.items():
        sisa = count_stok(key)
        lines.append(f"• {name}: <b>{sisa}</b> akun tersisa")

    text = (
        "📊 <b>Status Stok Akun</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n" +
        "\n".join(lines)
    )
    await update.message.reply_text(text, parse_mode="HTML")

# ======================================
# /LANGUAGE (HIDDEN)
# ======================================

async def language_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not context.args:
        msg = (
            "Gunakan: /language id atau /language en\n"
            "Contoh: /language id"
        )
        await update.message.reply_text(msg)
        return

    lang = context.args[0].lower()
    if lang not in ("id", "en"):
        await update.message.reply_text("Bahasa hanya mendukung: id / en")
        return

    set_lang(uid, lang)
    if lang == "en":
        await update.message.reply_text("✅ Bot language set to English.")
    else:
        await update.message.reply_text("✅ Bahasa bot di-set ke Indonesia.")

# ======================================
# FALLBACK & MAIN
# ======================================

async def fallback_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    lang = get_lang(uid)
    if lang == "en":
        text = "Hi 👋\nUse /start to open the main menu."
    else:
        text = "Halo 👋\nGunakan /start untuk membuka menu utama bot ya."
    await update.message.reply_text(text)


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plans", show_plans_menu_from_cmd))
    app.add_handler(CommandHandler("language", language_cmd))

    app.add_handler(CommandHandler("addpremium", addpremium))
    app.add_handler(CommandHandler("delpremium", delpremium))
    app.add_handler(CommandHandler("listpremium", listpremium))
    app.add_handler(CommandHandler("stok", stok_cmd))  # admin only, hidden

    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_msg))

    app.run_polling()


if __name__ == "__main__":
    main()
