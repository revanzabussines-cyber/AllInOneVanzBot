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
    raise RuntimeError("BOT_TOKEN wajib diisi!")

ADMIN_IDS = {7321522905}  # GANTI ke ID lu

MAX_PER_DAY = 100

BASE = Path(__file__).parent
PREMIUM_FILE = BASE / "premium.json"
HISTORY_FILE = BASE / "history.json"
STOK_FILE = BASE / "stok_akun.txt"


# ======================================
# JSON HELPERS
# ======================================

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def save_json(path: Path, data):
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ======================================
# PREMIUM SYSTEM
# ======================================

def is_admin(uid: int):
    return uid in ADMIN_IDS


def get_premium_db():
    return load_json(PREMIUM_FILE, {})


def save_premium_db(db):
    save_json(PREMIUM_FILE, db)


def is_premium(uid: int):
    db = get_premium_db()
    rec = db.get(str(uid))
    if not rec:
        return False
    exp = rec.get("expire_at")
    if not exp:
        return False
    exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
    return date.today() <= exp_date


def get_sisa_sewa(uid: int):
    db = get_premium_db()
    rec = db.get(str(uid), {})
    exp = rec.get("expire_at")
    if not exp:
        return 0
    exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
    return max((exp_date - date.today()).days, 0)


def update_quota(uid: int):
    today = date.today().strftime("%Y-%m-%d")
    db = get_premium_db()
    rec = db.get(str(uid), {
        "expire_at": None,
        "today_date": today,
        "today_count": 0,
        "total_generated": 0
    })

    if rec["today_date"] != today:
        rec["today_date"] = today
        rec["today_count"] = 0

    db[str(uid)] = rec
    save_premium_db(db)
    return rec


def increment_quota(uid: int):
    db = get_premium_db()
    rec = db.get(str(uid))
    if not rec:
        return
    rec["today_count"] += 1
    rec["total_generated"] += 1
    db[str(uid)] = rec
    save_premium_db(db)


# ======================================
# HISTORY SYSTEM
# ======================================

def get_history(uid: int):
    db = load_json(HISTORY_FILE, {})
    return db.get(str(uid), [])


def add_history(uid: int, akun: str):
    db = load_json(HISTORY_FILE, {})
    lst = db.get(str(uid), [])
    lst.append({"akun": akun})
    db[str(uid)] = lst
    save_json(HISTORY_FILE, db)


# ======================================
# STOK BOT
# ======================================

def ambil_akun():
    if not STOK_FILE.exists():
        return None

    lines = [l.strip() for l in STOK_FILE.read_text().splitlines() if l.strip()]
    if not lines:
        return None

    akun = lines[0]
    sisa = lines[1:]

    with STOK_FILE.open("w", encoding="utf-8") as f:
        for s in sisa:
            f.write(s + "\n")

    return akun


# ======================================
# UI
# ======================================

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧪 Generate 10 Akun", callback_data="GEN10")],
        [InlineKeyboardButton("🚀 Generate 20 Akun", callback_data="GEN20")],
        [InlineKeyboardButton("📦 Riwayat Akun", callback_data="SAVED")],
        [InlineKeyboardButton("⏳ Sisa Sewa", callback_data="SEWA")],
        [InlineKeyboardButton("🆘 Bantuan", callback_data="HELP")],
    ])


# ======================================
# BOT HANDLERS
# ======================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>VANZSTORE.ID — CapCut Generator Bot</b> 🚀\n\n"
        "⚙️ <b>Fitur:</b>\n"
        f"• Generate hingga <b>{MAX_PER_DAY} akun/hari</b>\n"
        "• Sistem akses premium by ID\n"
        "• Proses cepat & otomatis\n\n"
        "Gunakan tombol di bawah."
    )

    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="HTML")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    if data == "GEN10":
        await generate_multiple(q, uid, 10)
    elif data == "GEN20":
        await generate_multiple(q, uid, 20)
    elif data == "SAVED":
        await show_saved(q, uid)
    elif data == "SEWA":
        await show_sewa(q, uid)
    elif data == "HELP":
        await show_help(q)


async def generate_multiple(q, uid, jumlah):
    if not (is_admin(uid) or is_premium(uid)):
        await q.message.reply_text("🚫 Kamu belum memiliki akses premium.")
        return

    rec = update_quota(uid)

    if not is_admin(uid):
        sisa = MAX_PER_DAY - rec["today_count"]
        if sisa <= 0:
            await q.message.reply_text("❌ Limit harian sudah habis. Coba lagi besok.")
            return
        if jumlah > sisa:
            jumlah = sisa

    hasil = []

    for _ in range(jumlah):
        akun = ambil_akun()
        if not akun:
            break
        hasil.append(akun)
        increment_quota(uid)
        add_history(uid, akun)

        # Anti spam delay
        await asyncio.sleep(0.6)

    if not hasil:
        await q.message.reply_text("😿 Stok akun habis.")
        return

    daftar = "\n".join(f"<code>{a}</code>" for a in hasil)

    await q.message.reply_text(
        f"✅ <b>Berhasil mengambil {len(hasil)} akun:</b>\n\n{daftar}",
        parse_mode="HTML"
    )


async def show_saved(q, uid):
    hist = get_history(uid)
    if not hist:
        await q.message.reply_text("📦 Kamu belum mengambil akun.")
        return

    last = hist[-10:]
    lines = [f"{i+1}. <code>{h['akun']}</code>" for i, h in enumerate(last)]

    await q.message.reply_text(
        "📦 <b>Riwayat akun kamu:</b>\n\n" + "\n".join(lines),
        parse_mode="HTML",
    )


async def show_sewa(q, uid):
    if is_admin(uid):
        await q.message.reply_text("👑 Kamu admin — akses tanpa batas.")
        return

    if not is_premium(uid):
        await q.message.reply_text("⏳ Kamu belum memiliki akses premium.")
        return

    sisa = get_sisa_sewa(uid)
    await q.message.reply_text(f"⏳ Sisa masa aktif: <b>{sisa} hari</b>.", parse_mode="HTML")


async def show_help(q):
    await q.message.reply_text(
        "🆘 Bantuan:\n"
        "• Generate 10/20 akun\n"
        "• Limit 100 akun/hari\n"
        "• Premium access\n\n"
        "Untuk pembelian premium, hubungi admin.",
        parse_mode="HTML"
    )


# ======================================
# ADMIN COMMANDS
# ======================================

async def addpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text("Format: /addpremium <user_id> <hari>")
        return

    uid = int(context.args[0])
    hari = int(context.args[1])

    db = get_premium_db()
    today = date.today()

    old = db.get(str(uid), {})
    if old.get("expire_at"):
        old_exp = datetime.strptime(old["expire_at"], "%Y-%m-%d").date()
    else:
        old_exp = today

    new_expire = max(old_exp, today) + timedelta(days=hari)

    db[str(uid)] = {
        "expire_at": new_expire.strftime("%Y-%m-%d"),
        "today_date": today.strftime("%Y-%m-%d"),
        "today_count": 0,
        "total_generated": old.get("total_generated", 0)
    }

    save_premium_db(db)

    await update.message.reply_text(
        f"✅ Premium user {uid} aktif sampai {new_expire}"
    )


async def delpremium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    uid = context.args[0]

    db = get_premium_db()
    if uid in db:
        db.pop(uid)
        save_premium_db(db)
        await update.message.reply_text("Dihapus dari premium.")
    else:
        await update.message.reply_text("User tidak ditemukan.")


# ======================================
# MAIN
# ======================================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpremium", addpremium))
    app.add_handler(CommandHandler("delpremium", delpremium))

    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                   lambda u, c: u.message.reply_text("Gunakan menu /start")))

    app.run_polling()


if __name__ == "__main__":
    main()
