import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient

# ================== PATH & FILE STOK ==================
BASE = Path(__file__).parent

STOK_VIU = BASE / "stok_viu.txt"       # dipake juga di all.py
STOK_ALIGHT = BASE / "stok_alight.txt" # dipake juga di all.py
TMP_DIR = BASE / "tmp_ubot"
TMP_DIR.mkdir(exist_ok=True)

# ================== LOAD ENV ==================
# Buat lokal bisa pakai .env, di Railway cukup pakai panel ENV
load_dotenv()

API_ID = int(os.getenv("API_ID", "0"))
API_HASH = os.getenv("API_HASH")
SESSION_NAME = os.getenv("SESSION_NAME", "vanz_farming")

VIU_BOT = os.getenv("VIU_BOT", "@generateviupawbot")
AM_BOT = os.getenv("AM_BOT", "@pawalightmotionbot")

VIU_INTERVAL_MINUTES = int(os.getenv("VIU_INTERVAL_MINUTES", "20"))
AM_INTERVAL_MINUTES = int(os.getenv("AM_INTERVAL_MINUTES", "20"))

# Flow khusus VIU
VIU_PAKET_KEYWORD = os.getenv("VIU_PAKET_KEYWORD", "Lifetime")
VIU_DOMAIN = os.getenv("VIU_DOMAIN", "vanzmail.web.id")
VIU_PASSWORD = os.getenv("VIU_PASSWORD", "masuk123")

# Flow khusus AM (Alight Motion)
AM_DURASI_KEYWORD = os.getenv("AM_DURASI_KEYWORD", "1 Tahun")
AM_JUMLAH = os.getenv("AM_JUMLAH", "50")  # klik tombol angka
AM_MODE_EMAIL = os.getenv("AM_MODE_EMAIL", "Otomatis (Cepat)")

# ================== TELETHON CLIENT ==================
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


# ========== HELPER FILE STOK ==========

def append_accounts(path: Path, accounts: list[str]):
    """Tambah list akun ke file stok (1 akun per baris)."""
    accounts = [a.strip() for a in accounts if a and a.strip()]
    if not accounts:
        return
    with path.open("a", encoding="utf-8") as f:
        for a in accounts:
            f.write(a + "\n")
    print(f"[STOK] +{len(accounts)} akun ke {path.name}")


# ========== HELPER TELEGRAM ==========

async def get_last_message(chat_username):
    msgs = await client.get_messages(chat_username, limit=1)
    return msgs[0] if msgs else None


async def click_button_by_text(chat_username: str, keyword: str, timeout: int = 30):
    """
    Cari message terakhir dari bot yg punya inline keyboard,
    lalu klik button yg teksnya mengandung keyword.
    """
    keyword_low = keyword.lower()
    for _ in range(timeout):
        msg = await get_last_message(chat_username)
        if msg and msg.buttons:
            for row_idx, row in enumerate(msg.buttons):
                for col_idx, btn in enumerate(row):
                    text = (btn.text or "").strip()
                    if keyword_low in text.lower():
                        print(
                            f"[{chat_username}] 👉 Klik button "
                            f"'{text}' (row={row_idx}, col={col_idx})"
                        )
                        await btn.click()
                        return
        await asyncio.sleep(1)

    raise RuntimeError(
        f"[{chat_username}] Gagal nemu button dengan keyword '{keyword}' "
        f"dalam {timeout} detik"
    )


async def wait_text_contains(chat_username: str, keyword: str, timeout: int = 900):
    """
    Tunggu sampe message terakhir dari bot mengandung keyword tertentu.
    Berguna buat nunggu '✅ Generate Berhasil!' atau '✅ Proses Selesai!'
    """
    keyword_low = keyword.lower()
    for _ in range(timeout):
        msg = await get_last_message(chat_username)
        if msg and keyword_low in (msg.text or "").lower():
            print(f"[{chat_username}] ✅ Ketemu text berisi '{keyword}'")
            return msg
        await asyncio.sleep(2)

    raise RuntimeError(
        f"[{chat_username}] Timeout nunggu text mengandung '{keyword}'"
    )


async def wait_document_message(chat_username: str, timeout: int = 300):
    """
    Nunggu message terakhir dari bot yg punya document (file txt hasil AM).
    Dipanggil setelah '✅ Proses Selesai!'.
    """
    for _ in range(timeout):
        msg = await get_last_message(chat_username)
        if msg and msg.document:
            print(f"[{chat_username}] 📄 Ketemu document dari bot.")
            return msg
        await asyncio.sleep(2)

    raise RuntimeError(f"[{chat_username}] Timeout nunggu document dari bot")


# ========== PARSER HASIL ==========
def extract_accounts_from_text(text: str) -> list[str]:
    """
    Ambil baris yg keliatan kayak akun dari text VIU.
    Aturan simple: baris ga kosong, bukan header, dan mengandung '@' / ':' / '|'.
    """
    hasil = []
    if not text:
        return hasil

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("✅") or "proses selesai" in lower:
            continue
        if lower.startswith("berhasil") or lower.startswith("gagal"):
            continue
        # heuristik akun
        if any(c in line for c in ("@", ":", "|")) and len(line) >= 5:
            hasil.append(line)

    return hasil


def extract_accounts_from_file(path: Path) -> list[str]:
    """
    Baca file TXT hasil AM.
    Asumsi: tiap baris = 1 akun (email|pass / dsb).
    """
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l for l in lines if l]


# ========== FLOW VIU (generate akun) ==========

async def run_viu_once():
    bot = VIU_BOT
    print(f"[VIU] 🚀 Mulai flow VIU ke {bot}")

    # 1. /start
    print("[VIU] Kirim /start")
    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    # 2. Klik 'Buat Akun'
    await click_button_by_text(bot, "Buat Akun")

    # 3. Pilih tipe paket (Lifetime / yg lain)
    await asyncio.sleep(3)
    print(f"[VIU] Pilih paket dengan keyword '{VIU_PAKET_KEYWORD}'")
    await click_button_by_text(bot, VIU_PAKET_KEYWORD)

    # 4. Bot minta domain → kirim text
    await asyncio.sleep(3)
    print(f"[VIU] Kirim domain: {VIU_DOMAIN}")
    await client.send_message(bot, VIU_DOMAIN)

    # 5. Bot minta password → kirim text
    await asyncio.sleep(3)
    print(f"[VIU] Kirim password")
    await client.send_message(bot, VIU_PASSWORD)

    # 6. Nunggu sampai "✅ Generate Berhasil!"
    print("[VIU] ⏳ Nunggu '✅ Generate Berhasil!' ...")
    msg_done = await wait_text_contains(bot, "Generate Berhasil", timeout=900)

    # 7. Parse akun dari text & simpan ke stok_viu.txt
    akun_list = extract_accounts_from_text(msg_done.text or "")
    append_accounts(STOK_VIU, akun_list)
    print(f"[VIU] 💾 Hasil disimpan ke {STOK_VIU.name}")


async def farm_viu_loop():
    """
    Loop farming VIU tiap X menit (dari env VIU_INTERVAL_MINUTES)
    """
    if not VIU_BOT:
        print("[VIU] ⚠️ VIU_BOT kosong, skip farming VIU.")
        return

    interval = VIU_INTERVAL_MINUTES
    print(f"[VIU] 🔁 Farming VIU aktif, interval {interval} menit.")

    while True:
        try:
            await run_viu_once()
        except Exception as e:
            print(f"[VIU] ❌ Error di run_viu_once: {e}")

        print(f"[VIU] ⏳ Tidur {interval} menit sebelum next run...\n")
        await asyncio.sleep(interval * 60)


# ========== FLOW AM (Alight Motion) ==========

async def run_am_once():
    bot = AM_BOT
    print(f"[AM] 🚀 Mulai flow AM ke {bot}")

    # 1. /start
    print("[AM] Kirim /start")
    await client.send_message(bot, "/start")
    await asyncio.sleep(3)

    # 2. Klik "🚀 Buat Akun AM"
    await click_button_by_text(bot, "Buat Akun AM")

    # 3. Pilih durasi (6 Bulan / 1 Tahun / dll)
    await asyncio.sleep(3)
    print(f"[AM] Pilih durasi dengan keyword '{AM_DURASI_KEYWORD}'")
    await click_button_by_text(bot, AM_DURASI_KEYWORD)

    # 4. Pilih jumlah akun (1–50)
    await asyncio.sleep(3)
    print(f"[AM] Pilih jumlah akun '{AM_JUMLAH}'")
    await click_button_by_text(bot, AM_JUMLAH)

    # 5. Pilih metode input email (Otomatis / Manual)
    await asyncio.sleep(3)
    print(f"[AM] Pilih mode email '{AM_MODE_EMAIL}'")
    await click_button_by_text(bot, AM_MODE_EMAIL)

    # 6. Nunggu "✅ Proses Selesai!"
    print("[AM] ⏳ Nunggu '✅ Proses Selesai!' ...")
    _ = await wait_text_contains(bot, "Proses Selesai", timeout=3600)

    # 7. Nunggu file TXT akun
    print("[AM] ⏳ Nunggu file TXT akun ...")
    doc_msg = await wait_document_message(bot, timeout=300)

    tmp_path = TMP_DIR / "am_last.txt"
    await client.download_media(doc_msg, file=tmp_path)
    print(f"[AM] 📄 File akun ke-download di {tmp_path.name}")

    akun_list = extract_accounts_from_file(tmp_path)
    append_accounts(STOK_ALIGHT, akun_list)
    print(f"[AM] 💾 Hasil disimpan ke {STOK_ALIGHT.name}")


async def farm_am_loop():
    """
    Loop farming AM tiap X menit (dari env AM_INTERVAL_MINUTES)
    """
    if not AM_BOT:
        print("[AM] ⚠️ AM_BOT kosong, skip farming AM.")
        return

    interval = AM_INTERVAL_MINUTES
    print(f"[AM] 🔁 Farming AM aktif, interval {interval} menit.")

    while True:
        try:
            await run_am_once()
        except Exception as e:
            print(f"[AM] ❌ Error di run_am_once: {e}")

        print(f"[AM] ⏳ Tidur {interval} menit sebelum next run...\n")
        await asyncio.sleep(interval * 60)


# ========== MAIN ==========

async def main():
    print("🔐 Login userbot...")
    await client.start()
    me = await client.get_me()
    print(f"✅ Login sebagai: {me.first_name} (@{me.username}) [id={me.id}]")

    # Jalanin 2 farming bareng (VIU + AM)
    asyncio.create_task(farm_viu_loop())
    asyncio.create_task(farm_am_loop())

    print("🔥 Farming jalan. CTRL+C kalau run di lokal.")
    # Biar script nggak langsung selesai
    await asyncio.Future()


if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
