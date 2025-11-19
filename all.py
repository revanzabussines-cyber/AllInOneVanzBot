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

# GANTI KE ID TELEGRAM LU
ADMIN_IDS = {7321522905}  # contoh: {123456789}

MAX_PER_DAY = 100  # TOTAL limit per user per hari (gabungan semua generator)

BASE = Path(__file__).parent
PREMIUM_FILE = BASE / "premium.json"
HISTORY_FILE = BASE / "history.json"

STOK_CANVA = BASE / "stok_canva.txt"
STOK_CAPCUT = BASE / "stok_capcut.txt"
STOK_VIDIO = BASE / "stok_vidio.txt"


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


def add_history(uid: int, akun: str, produk: str):
    db = load_json(HISTORY_FILE, {})
    lst = db.get(str(uid), [])
    lst.append({"akun": akun, "produk": produk})
    db[str(uid)] = lst
    save_json(HISTORY_FILE, db)


# ======================================
# STOK BOT
# ======================================

def get_stok_file(produk_key: str) -> Path:
    if produk_key == "CANVA":
        return STOK_CANVA
    if produk_key == "CAPCUT":
        return STOK_CAPCUT
    if produk_key == "VIDIO":
        return STOK_VIDIO
    return STOK_CAPCUT  # fallback aja


def ambil_akun(produk_key: str):
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


# ======================================
# UI
# ======================================

def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🧪 Canva x10", callback_data="CANVA10"),
            InlineKeyboardButton("🧪 Canva x20", callback_data="CANVA20"),
        ],
        [
            InlineKeyboardButton("🎬 CapCut x10", callback_data="CAPCUT10"),
            InlineKeyboardButton("🎬 CapCut x20", callback_data="CAPCUT20"),
        ],
        [
            InlineKeyboardButton("📺 Vidio 1 TV x10", callback_data="VIDIO10"),
            InlineKeyboardButton("📺 Vidio 1 TV x20", callback_data="VIDIO20"),
        ],
        [
            InlineKeyboardButton("📦 Riwayat Akun", callback_data="SAVED"),
            InlineKeyboardButton("⏳ Sisa Sewa", callback_data="SEWA"),
        ],
        [
            InlineKeyboardButton("🆘 Bantuan", callback_data="HELP"),
        ],
    ])


# ======================================
# BOT HANDLERS
# ======================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🌌 <b>VANZSTORE.ID — Multi Generator Bot</b> 🚀\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "Satu bot untuk generate beberapa jenis akun secara otomatis:\n"
        "• Canva\n"
        "• CapCut Kosongan\n"
        "• Vidio 1 TV\n\n"
        "Cocok buat kebutuhan testing, jualan jasa, atau multi-akun tanpa daftar manual.\n\n"
        "⚙️ <b>Highlight Fitur</b>\n"
        f"• ⚡ Total hingga <b>{MAX_PER_DAY} akun / hari / user</b>\n"
        "• 🔐 Sistem akses premium by ID\n"
        "• 🤖 Proses cepat & otomatis (dengan indikator proses generate)\n\n"
        "📲 <b>Cara pakai:</b>\n"
        "1. Pilih jenis akun & jumlah (10 / 20)\n"
        "2. Tunggu proses generator selesai\n"
        "3. Akun siap dipakai & bisa dicek ulang di menu <b>Riwayat Akun</b>\n\n"
        "Gunakan tombol di bawah untuk mulai."
    )

    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="HTML")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = q.data

    mapping = {
        "CANVA10": ("CANVA", "Canva", 10),
        "CANVA20": ("CANVA", "Canva", 20),
        "CAPCUT10": ("CAPCUT", "CapCut Kosongan", 10),
        "CAPCUT20": ("CAPCUT", "CapCut Kosongan", 20),
        "VIDIO10": ("VIDIO", "Vidio 1 TV", 10),
        "VIDIO20": ("VIDIO", "Vidio 1 TV", 20),
    }

    if data in mapping:
        produk_key, produk_nama, jumlah = mapping[data]
        await generate_multiple(q, uid, produk_key, produk_nama, jumlah)
    elif data == "SAVED":
        await show_saved(q, uid)
    elif data == "SEWA":
        await show_sewa(q, uid)
    elif data == "HELP":
        await show_help(q)


async def generate_multiple(q, uid, produk_key: str, produk_nama: str, jumlah_awal: int):
    # cek akses
    if not (is_admin(uid) or is_premium(uid)):
        await q.message.reply_text(
            "🚫 Akses premium belum aktif untuk akun kamu.\n"
            "Silakan hubungi admin untuk aktivasi."
        )
        return

    rec = update_quota(uid)
    jumlah = jumlah_awal

    # cek limit harian global
    if not is_admin(uid):
        sisa = MAX_PER_DAY - rec["today_count"]
        if sisa <= 0:
            await q.message.reply_text(
                "❌ Limit harian kamu sudah tercapai.\n"
                "Kamu bisa generate lagi besok."
            )
            return
        if jumlah > sisa:
            jumlah = sisa

    # notif proses
    proses_msg = await q.message.reply_text(
        f"🔄 <b>Generator {produk_nama}</b>\n"
        f"⏳ Menyiapkan <b>{jumlah}</b> akun untuk kamu...\n\n"
        "Mohon tunggu, sistem sedang memproses data.",
        parse_mode="HTML"
    )

    hasil = []

    for _ in range(jumlah):
        akun = ambil_akun(produk_key)
        if not akun:
            break
        hasil.append(akun)
        increment_quota(uid)
        add_history(uid, akun, produk_nama)
        await asyncio.sleep(0.6)  # anti spam

    if not hasil:
        await proses_msg.edit_text(
            f"😿 Stok akun <b>{produk_nama}</b> sedang habis.\n"
            "Silakan hubungi admin untuk isi ulang stok.",
            parse_mode="HTML"
        )
        return

    daftar = "\n".join(f"<code>{a}</code>" for a in hasil)
    total_batch = len(hasil)

    await proses_msg.edit_text(
        f"✅ <b>Generate {produk_nama} selesai!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Jumlah akun di batch ini: <b>{total_batch}</b>\n\n"
        f"{daftar}\n\n"
        "🔁 Semua akun ini juga tersimpan di menu <b>Riwayat Akun</b>.",
        parse_mode="HTML"
    )


async def show_saved(q, uid):
    hist = get_history(uid)
    if not hist:
        await q.message.reply_text(
            "📦 Riwayat kosong.\n"
            "Kamu belum pernah generate akun dari bot ini."
        )
        return

    lines = [
        f"{i+1}. [{h['produk']}] <code>{h['akun']}</code>"
        for i, h in enumerate(hist)
    ]

    text = (
        "📦 <b>Riwayat Akun Kamu</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Total akun yang pernah kamu ambil: <b>{len(hist)}</b>\n\n"
        + "\n".join(lines)
    )

    await q.message.reply_text(text, parse_mode="HTML")


async def show_sewa(q, uid):
    if is_admin(uid):
        await q.message.reply_text(
            "👑 Kamu adalah admin.\n"
            "Akses generator tidak dibatasi masa sewa."
        )
        return

    if not is_premium(uid):
        await q.message.reply_text(
            "⏳ Akses premium kamu belum aktif.\n"
            "Silakan hubungi admin untuk beli / perpanjang paket."
        )
        return

    sisa = get_sisa_sewa(uid)

    db = get_premium_db()
    rec = db.get(str(uid), {})
    today_cnt = rec.get("today_count", 0)

    await q.message.reply_text(
        "⏳ <b>Status Sewa Premium</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"• Sisa masa aktif: <b>{sisa} hari</b>\n"
        f"• Limit harian: <b>{MAX_PER_DAY} akun / hari</b>\n"
        f"• Pemakaian hari ini: <b>{today_cnt}/{MAX_PER_DAY}</b>",
        parse_mode="HTML"
    )


async def show_help(q):
    await q.message.reply_text(
        "🆘 <b>Panduan Singkat</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "• Pilih jenis akun: Canva / CapCut Kosongan / Vidio 1 TV\n"
        "• Pilih jumlah generate: 10 atau 20 akun sekaligus\n"
        "• Tunggu indikator proses selesai, akun akan muncul\n"
        "• Semua akun yang pernah kamu ambil bisa dicek di menu <b>Riwayat Akun</b>\n\n"
        f"Limit generate per user: <b>{MAX_PER_DAY} akun / hari</b> (gabungan semua jenis).\n"
        "Untuk pembelian / perpanjang akses premium, silakan hubungi admin.",
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

    if not context.args:
        await update.message.reply_text("Format: /delpremium <user_id>")
        return

    uid = context.args[0]

    db = get_premium_db()
    if uid in db:
        db.pop(uid)
        save_premium_db(db)
        await update.message.reply_text("✅ User tersebut dihapus dari premium.")
    else:
        await update.message.reply_text("User tidak ditemukan di list premium.")


# ======================================
# MAIN & FALLBACK
# ======================================

async def fallback_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Halo 👋\n"
        "Gunakan /start untuk membuka menu utama bot ya."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addpremium", addpremium))
    app.add_handler(CommandHandler("delpremium", delpremium))

    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_msg))

    app.run_polling()


if __name__ == "__main__":
    main()
