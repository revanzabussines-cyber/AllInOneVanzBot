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
            InlineKeyboardButton("📺 Vidio x10", callback_data="VIDIO10"),
            InlineKeyboardButton("📺 Vidio x20", callback_data="VIDIO20"),
        ],
        [
            InlineKeyboardButton("📦 Riwayat Akun", callback_data="SAVED"),
            InlineKeyboardButton("⏳ Sisa Sewa", callback_data="SEWA"),
        ],
        [
            InlineKeyboardButton("🆘 Bantuan", callback_data="HELP"),
        ],
    ])
