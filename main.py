import os, time, requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# ─── Config ──────────────────────────────────────────
BOT_TOKEN    = os.environ.get("BOT_TOKEN",    "8611107910:AAFrsF57clxJnoRDMouzi6TztWwD7PqyVxI")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://ads-sovitx.vercel.app")
FB_DB_URL    = os.environ.get("FB_DB_URL",    "https://digit-product-default-rtdb.firebaseio.com")
BOT_USERNAME = "watch_ads_sovitx_bot"
DEVELOPER    = "SovitX"

# ─── Firebase helpers ────────────────────────────────
def fb_get(path):
    try:
        r = requests.get(f"{FB_DB_URL}/{path}.json", timeout=8)
        return r.json()
    except:
        return None

def fb_set(path, data):
    try:
        requests.put(f"{FB_DB_URL}/{path}.json", json=data, timeout=8)
    except:
        pass

def fb_patch(path, data):
    try:
        requests.patch(f"{FB_DB_URL}/{path}.json", json=data, timeout=8)
    except:
        pass

# ─── Main keyboard ───────────────────────────────────
def main_keyboard(tg_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Play", web_app={"url": MINI_APP_URL})],
        [
            InlineKeyboardButton("🔗 My Referral Link", callback_data=f"ref_{tg_id}"),
            InlineKeyboardButton("❓ Help",             callback_data="help")
        ]
    ])

# ─── /start ──────────────────────────────────────────
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user   = update.effective_user
    tg_id  = str(user.id)
    fname  = user.first_name or "User"
    lname  = user.last_name or ""
    name   = (fname + (" " + lname if lname else "")).strip()
    photo  = user.photo_url if hasattr(user, 'photo_url') and user.photo_url else ""
    uid    = f"TG_{tg_id}"
    now_ms = int(time.time() * 1000)

    # Referral code from /start param
    ref_code = context.args[0] if context.args else None

    existing = fb_get(f"users/{uid}")
    is_new   = not (existing and isinstance(existing, dict))

    if is_new:
        fb_set(f"users/{uid}", {
            "uid": uid, "username": name, "photoUrl": photo,
            "balance": 0, "totalWithdrawn": 0, "lastDailyClaim": 0,
            "dailyStreak": 0, "invites": 0, "adProgress": 0,
            "lastBalanceUpdate": now_ms, "role": "user",
            "createdAt": now_ms, "referredBy": None
        })
        # Credit referrer
        if ref_code and len(str(ref_code)) == 8 and str(ref_code).isdigit():
            code_data = fb_get(f"refCodes/{ref_code}")
            if code_data and isinstance(code_data, dict):
                referrer_uid = code_data.get("uid")
                if referrer_uid and referrer_uid != uid:
                    rd = fb_get(f"users/{referrer_uid}")
                    if rd and isinstance(rd, dict):
                        fb_patch(f"users/{referrer_uid}", {
                            "balance": float(rd.get("balance", 0)) + 3,
                            "invites": int(rd.get("invites", 0)) + 1,
                            "lastBalanceUpdate": now_ms
                        })
                    fb_patch(f"users/{uid}", {"referredBy": referrer_uid})
    else:
        updates = {}
        uname = existing.get("username", "")
        if name and (not uname or uname.startswith("TG_") or uname.startswith("Guest_")):
            updates["username"] = name
        if photo and not existing.get("photoUrl"):
            updates["photoUrl"] = photo
        if updates:
            fb_patch(f"users/{uid}", updates)

    intro = f"🎉 *Welcome {fname}\\!*" if is_new else f"👋 *Hey {fname}, welcome back\\!*"

    await update.message.reply_text(
        f"{intro}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 Earn *₹1* per video\n"
        f"🎁 Daily bonus up to *₹15/day*\n"
        f"👥 Invite friends — *₹3* each\n"
        f"💳 Withdraw at *₹100* via UPI\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👇 Tap *Play* to start earning\\!\n\n"
        f"💎 *Developed by {DEVELOPER}*",
        parse_mode="MarkdownV2",
        reply_markup=main_keyboard(tg_id)
    )

# ─── /refer ──────────────────────────────────────────
async def refer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    tg_id   = str(user.id)
    uid     = f"TG_{tg_id}"
    data    = fb_get(f"users/{uid}")
    if not data or not isinstance(data, dict):
        await update.message.reply_text("⚠️ Please open the app first via Play button.")
        return
    ref_code = data.get("refCode")
    invites  = int(data.get("invites", 0))
    if not ref_code:
        await update.message.reply_text("⚠️ Open the app first to generate your referral code.")
        return
    ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
    await update.message.reply_text(
        f"🔗 *Your Referral Link:*\n\n"
        f"`{ref_link}`\n\n"
        f"🎯 Your Code: `{ref_code}`\n"
        f"👥 Total Invites: *{invites}*\n"
        f"💵 Referral Earned: *₹{invites * 3}*\n\n"
        f"Share and earn *₹3* per friend\\!\n\n"
        f"💎 *Developed by {DEVELOPER}*",
        parse_mode="MarkdownV2",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link",
                switch_inline_query=f"🎬 Watch & Earn — earn real money!\n👉 {ref_link}")],
            [InlineKeyboardButton("▶️ Open App", web_app={"url": MINI_APP_URL})]
        ])
    )

# ─── Callback buttons ─────────────────────────────────
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user  = query.from_user
    tg_id = str(user.id)
    fname = user.first_name or "User"
    cbd   = query.data

    if cbd.startswith("ref_"):
        uid      = f"TG_{cbd.replace('ref_', '')}"
        data     = fb_get(f"users/{uid}")
        ref_code = data.get("refCode") if isinstance(data, dict) else None
        invites  = int(data.get("invites", 0)) if isinstance(data, dict) else 0
        if not ref_code:
            await query.message.reply_text("⚠️ Open the app first to generate your code.")
            return
        ref_link = f"https://t.me/{BOT_USERNAME}?start={ref_code}"
        await query.message.reply_text(
            f"🔗 *Your Referral Link:*\n\n"
            f"`{ref_link}`\n\n"
            f"🎯 Code: `{ref_code}`\n"
            f"👥 Invites: *{invites}* \\| Earned: *₹{invites * 3}*\n\n"
            f"💎 *Developed by {DEVELOPER}*",
            parse_mode="MarkdownV2",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 Share",
                    switch_inline_query=f"🎬 Watch & Earn!\n👉 {ref_link}")
            ]])
        )

    elif cbd == "help":
        await query.message.reply_text(
            f"📖 *How Watch & Earn works:*\n\n"
            f"1️⃣ Tap *Play* → watch ad → earn ₹1\n"
            f"2️⃣ Claim daily bonus every 24h\n"
            f"3️⃣ Invite friends — earn ₹3 each\n"
            f"4️⃣ Reach ₹100 → withdraw to UPI\n\n"
            f"/start — Open app\n"
            f"/refer — Your referral link\n\n"
            f"💎 *Developed by {DEVELOPER}*",
            parse_mode="Markdown"
        )

# ─── Default message ──────────────────────────────────
async def default_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tg_id = str(update.effective_user.id)
    await update.message.reply_text(
        "👇 Tap to open Watch & Earn!",
        reply_markup=main_keyboard(tg_id)
    )

# ─── Build app ────────────────────────────────────────
def build_app():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start",  start_command))
    application.add_handler(CommandHandler("refer",  refer_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(~filters.COMMAND, default_message))
    return application

# ─── Local run ────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 Starting @{BOT_USERNAME}")
    build_app().run_polling(drop_pending_updates=True)
