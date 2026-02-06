import os
import json
from telegram import Update, InputFile
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

DATA_FILE = "rules.json"

# ====== MA'LUMOTLARNI YUKLASH ======
def load_rules():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_rules(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

rules = load_rules()

# ====== ADMIN TEKSHIRISH ======
def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Salom! Bot ishlayapti ✅\n"
        "Admin buyruqlari:\n"
        "add so‘z | javob\n"
        "del so‘z\n"
        "list"
    )

# ====== ADD ======
async def add_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    try:
        text = update.message.text.replace("add", "", 1).strip()
        key, value = text.split("|", 1)
        rules[key.strip().lower()] = value.strip()
        save_rules(rules)
        await update.message.reply_text("✅ Qo‘shildi")
    except:
        await update.message.reply_text("❌ Format: add so‘z | javob")

# ====== DELETE ======
async def del_rule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    key = update.message.text.replace("del", "", 1).strip().lower()
    if key in rules:
        del rules[key]
        save_rules(rules)
        await update.message.reply_text("🗑 O‘chirildi")
    else:
        await update.message.reply_text("Topilmadi")

# ====== LIST ======
async def list_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if not rules:
        await update.message.reply_text("Bo‘sh")
        return

    msg = "\n".join([f"• {k}" for k in rules.keys()])
    await update.message.reply_text(msg)

# ====== FOYDALANUVCHI XABARI ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()

    for key, answer in rules.items():
        if key in text:
            await update.message.reply_text(answer)
            break

# ====== MAIN ======
def main():
    if not TOKEN or not ADMIN_ID:
        print("❌ BOT_TOKEN yoki ADMIN_ID yo‘q")
        return

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^add "), add_rule))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^del "), del_rule))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^list$"), list_rules))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot ishga tushdi")
    app.run_polling()

if __name__ == "__main__":
    main() 