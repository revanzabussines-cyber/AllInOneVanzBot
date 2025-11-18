import os
import json
from pathlib import Path
from datetime import datetime, timedelta, date
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# =========================
# LOGGING
# =========================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# =========================
# KONFIGURASI
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN")  # set di Railway/Render
if not BOT_TOKEN:
    raise RuntimeError("ENV BOT_TOKEN belum di-set!")

# GANTI ID ADMIN DENGAN ID TELEGRAM LU
ADMIN_IDS = {123456789, 987654321}  # contoh, ganti angka ini

# Limit per user per hari
MAX_PER_DAY = 100

BASE_DIR = Path(__file__).parent
PREMIUM_FILE = BASE_DIR / "premium.json"
HISTORY_FILE = BASE_DIR / "history.json"
STOK_FILE = BASE_DIR / "stok_akun.txt"


# =========================
# HELPER JSON
# =========================

def load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Gagal baca {path}: {e}")
        return default


def save_json(path: Path, data):
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Gagal simpan {path}: {e}")


# =========================
# PREMIUM SYSTEM
# =========================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def get_premium_db():
    return load_json(PREMIUM_FILE, {})


def save_premium_db(db):
    save_json(PREMIUM_FILE, db)


def is_premium(user_id: int) -> bool:
    db = get_premium_db()
    user = db.get(str(user_id))
    if not user:
        return False
    expire_str = user.get("expire_at")
    if not expire_str:
        return False
    try:
        expire_date = datetime.strptime(expire_str, "%Y-%m-%d").date()
    except ValueError:
        return False
    today = date.today()
    return today <= expire_date


def get_sisa_sewa(user_id: int) -> int:
    db = get_premium_db()
    user = db.get(str(user_id))
    if not user or not user.get("expire_at"):
        return 0
    try:
        expire_date = datetime.strptime(user["expire_at"], "%Y-%m-%d").date()
    except ValueError:
        return 0
    today = date.today()
    delta = (expire_date - today).days
    return max(delta, 0)


def update_quota(user_id: int) -> dict:
    """
    Return user premium record setelah update tanggal dan quota harian.
    Kalau hari berganti, reset today_count ke 0.
    """
    db = get_premium_db()
    today_str = date.today().strftime("%Y-%m-%d")
    rec = db.get(str(user_id))
    if not rec:
        rec = {
            "expire_at": None,
            "today_date": today_str,
            "today_count": 0,
            "total_generated": 0,
        }
    # reset jika hari berganti
    if rec.get("today_date") != today_str:
        rec["today_date"] = today_str
        rec["today_count"] = 0
    db[str(user_id)] = rec
    save_premium_db(db)
    return rec


def increment_quota(user_id: int):
    db = get_premium_db()
    rec = db.get(str(user_id))
    if not rec:
        return
    rec["today_count"] = rec.get("today_count", 0) + 1
    rec["total_generated"] = rec.get("total_generated", 0) + 1
    db[str(user_id)] = rec
    save_premium_db(db)


# =========================
# HISTORY AKUN
# =========================

def get_history_db():
    return load_json(HISTORY_FILE, {})


def save_history_db(db):
    save_json(HISTORY_FILE, db)


def add_history(user_id: int, akun: str):
    db = get_history_db()
    lst = db.get(str(user_id), [])
    lst.append({
        "akun": akun,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    db[str(user_id)] = lst
    save_history_db(db)


def get_user_history(user_id: int):
    db = get_history_db()
    return db.get(str(user_id), [])


# =========================
# STOK AKUN
# =========================

def ambil_satu_akun() -> str | None:
    if not STOK_FILE.exists():
        return None
    with STOK_FILE.open("r", encoding="utf-8") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

    if not lines:
        return None

    akun = lines[0]
    sisa = lines[1:]

    with STOK_FILE.open("w", encoding="utf-8") as f:
        for line in sisa:
            f.write(line + "\n")

    return akun


def count_stok() -> int:
    if not STOK_FILE.exists():
        return 0
    with STOK_FILE.open("r", encoding="utf-8") as f:
        return len([l for l in f.readlines() if l.strip()])


# =========================
# KEYBOARD
# =========================

def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🧪 Generator Akun", callback_data="GEN"),
        ],
        [
            InlineKeyboardButton("📦 Akun yang disimpan", callback_data="SAVED"),
        ],
        [
            InlineKeyboardButton("⏳ Sisa sewa", callback_data="SEWA"),
        ],
        [
            InlineKeyboardButton("🆘 Help / Bantuan", callback_data="HELP"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# =========================
# HANDLERS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.full_name

    text = (
        f"Hai {username} 👋\n"
        f"ID Telegram kamu: <code>{user_id}</code>\n\n"
        "Selamat datang di <b>Bot Generator Akun CapCut Kosongan</b> 🧪\n\n"
        "⚙️ Fitur bot:\n"
        f"• Limit generate: <b>{MAX_PER_DAY} akun / hari</b>\n"
        "• Sistem sewa / premium by ID\n"
        "• Akun sebenernya sudah disiapin sama admin (bukan generate random)\n\n"
        "Klik tombol di bawah buat mulai pake bot ini. ⬇️"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🆘 <b>Bantuan Bot Generator CapCut</b>\n\n"
        "• /start - buka menu utama\n"
        "• /help - lihat bantuan ini\n\n"
        "Khusus admin:\n"
        "• /addpremium &lt;user_id&gt; &lt;hari&gt; - tambah / perpanjang sewa\n"
        "• /delpremium &lt;user_id&gt; - hapus akses premium\n"
        "• /listpremium - lihat daftar premium singkat\n"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    user_id = user.id

    data = query.data

    if data == "GEN":
        await handle_generate(query, user_id)
    elif data == "SAVED":
        await handle_saved(query, user_id)
    elif data == "SEWA":
        await handle_sewa(query, user_id)
    elif data == "HELP":
        await handle_help_button(query)
    else:
        await query.message.reply_text("Perintah tidak dikenal, coba /start ulang aja bro.")


async def handle_generate(query, user_id: int):
    # Admin selalu boleh akses
    if not (is_premium(user_id) or is_admin(user_id)):
        await query.message.reply_text(
            "🚫 Kamu belum punya akses premium untuk pakai generator ini.\n"
            "Silakan hubungi admin buat sewa akses ya."
        )
        return

    # Cek / update quota harian
    rec = update_quota(user_id)
    if not is_admin(user_id):  # admin bebas
        today_count = rec.get("today_count", 0)
        if today_count >= MAX_PER_DAY:
            await query.message.reply_text(
                f"❌ Limit harian tercapai.\n"
                f"Kamu sudah generate {MAX_PER_DAY} akun hari ini.\n"
                "Coba lagi besok ya."
            )
            return

    # Cek stok
    akun = ambil_satu_akun()
    if not akun:
        await query.message.reply_text(
            "😿 Stok akun CapCut lagi habis.\n"
            "Tolong kabarin admin supaya diisi lagi."
        )
        return

    # Simpan ke history
    add_history(user_id, akun)
    increment_quota(user_id)

    sisa_stok = count_stok()

    text = (
        "✅ Berhasil ngasih 1 akun CapCut buat kamu:\n\n"
        f"<code>{akun}</code>\n\n"
        f"⚠️ Jaga baik-baik datanya ya.\n"
        f"📦 Sisa stok di bot: <b>{sisa_stok}</b> akun."
    )
    await query.message.reply_text(text, parse_mode="HTML")


async def handle_saved(query, user_id: int):
    history = get_user_history(user_id)
    if not history:
        await query.message.reply_text(
            "📦 Kamu belum pernah ngambil akun dari bot ini.\n"
            "Coba klik tombol <b>🧪 Generator Akun</b> dulu.",
            parse_mode="HTML",
        )
        return

    # Tampilkan max 10 terakhir biar ga kepanjangan
    last_items = history[-10:]
    lines = []
    for idx, item in enumerate(last_items, start=1):
        lines.append(
            f"{idx}. <code>{item['akun']}</code>\n   ⏱ {item['time']}"
        )

    text = "📦 <b>Riwayat akun yang pernah kamu ambil:</b>\n\n" + "\n\n".join(lines)
    await query.message.reply_text(text, parse_mode="HTML")


async def handle_sewa(query, user_id: int):
    if is_admin(user_id):
        await query.message.reply_text(
            "👑 Kamu adalah admin, akses ga dibatasi sewa."
        )
        return

    if not is_premium(user_id):
        await query.message.reply_text(
            "⏳ Kamu belum punya paket sewa aktif.\n"
            "Hubungi admin buat beli akses premium."
        )
        return

    sisa_hari = get_sisa_sewa(user_id)
    await query.message.reply_text(
        f"⏳ Paket sewamu masih aktif.\n"
        f"Sisa masa aktif: <b>{sisa_hari} hari</b>.",
        parse_mode="HTML",
    )


async def handle_help_button(query):
    text = (
        "🆘 <b>Bantuan Singkat</b>\n\n"
        "• 🧪 <b>Generator Akun</b> → ambil 1 akun CapCut kosongan (butuh premium).\n"
        "• 📦 <b>Akun yang disimpan</b> → lihat riwayat akun yang pernah kamu ambil.\n"
        "• ⏳ <b>Sisa sewa</b> → cek masa aktif premium kamu.\n"
        "• /help → detail bantuan + command admin.\n"
    )
    await query.message.reply_text(text, parse_mode="HTML")


# =========================
# ADMIN COMMANDS
# =========================

async def add_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Format:\n/addpremium <user_id> <hari>\n\nContoh:\n/addpremium 123456789 30"
        )
        return

    try:
        target_id = int(context.args[0])
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("User ID dan hari harus angka.")
        return

    db = get_premium_db()
    rec = db.get(str(target_id), {})
    today = date.today()
    # kalau sudah ada expire, lanjut dari situ
    if rec.get("expire_at"):
        try:
            old_expire = datetime.strptime(rec["expire_at"], "%Y-%m-%d").date()
        except ValueError:
            old_expire = today
    else:
        old_expire = today

    new_expire = max(old_expire, today) + timedelta(days=days)
    rec["expire_at"] = new_expire.strftime("%Y-%m-%d")
    rec.setdefault("today_date", today.strftime("%Y-%m-%d"))
    rec.setdefault("today_count", 0)
    rec.setdefault("total_generated", 0)

    db[str(target_id)] = rec
    save_premium_db(db)

    await update.message.reply_text(
        f"✅ User {target_id} ditandai premium.\n"
        f"Berlaku sampai: {rec['expire_at']} (tambah {days} hari)."
    )


async def del_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
        return

    if not context.args:
        await update.message.reply_text("Format:\n/delpremium <user_id>")
        return

    try:
        target_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("User ID harus angka.")
        return

    db = get_premium_db()
    if str(target_id) in db:
        db.pop(str(target_id))
        save_premium_db(db)
        await update.message.reply_text(f"✅ User {target_id} dihapus dari premium.")
    else:
        await update.message.reply_text("User tersebut tidak ada di list premium.")


async def list_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not is_admin(user.id):
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

    text = "👑 <b>Daftar user premium:</b>\n\n" + "\n".join(lines)
    await update.message.reply_text(text, parse_mode="HTML")


# =========================
# FALLBACK UNTUK CHAT BIASA
# =========================

async def echo_non_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Biar kalo orang chat biasa, diarahkan ke /start
    await update.message.reply_text(
        "Halo! Gunakan /start untuk buka menu bot ya. 😺"
    )


# =========================
# MAIN
# =========================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # admin
    app.add_handler(CommandHandler("addpremium", add_premium))
    app.add_handler(CommandHandler("delpremium", del_premium))
    app.add_handler(CommandHandler("listpremium", list_premium))

    # buttons
    app.add_handler(CallbackQueryHandler(handle_buttons))

    # non-command messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_non_command))

    logger.info("Bot generator CapCut siap jalan...")
    app.run_polling()


if __name__ == "__main__":
    main()
