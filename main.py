import telebot
import json
import os
from datetime import datetime

# ===========================
# CONFIG
TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215
RULES_FILE = "rules.json"
USERS_FILE = "users.json"
LOG_FILE = "bot.log"
# ===========================

bot = telebot.TeleBot(TOKEN)

# ===========================
# JSON load/save
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

rules = load_json(RULES_FILE, {})
users = load_json(USERS_FILE, {})

# ===========================
# Log
def log(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {text}\n")

# ===========================
# Admin tekshirish
def is_owner(message):
    return message.from_user.id == OWNER_ID

# ===========================
# Foydalanuvchi saqlash
def save_user(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or "",
            "messages": 0
        }
    users[user_id]["messages"] += 1
    save_json(USERS_FILE, users)

# ===========================
# ADD (Admin)
user_state = {}

@bot.message_handler(func=lambda m: m.text and m.text.lower() == "add" and is_owner(m))
def add_start(message):
    user_state[message.chat.id] = {"step": "trigger"}
    bot.send_message(message.chat.id, "📝 So‘z yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "trigger")
def add_trigger(message):
    trigger = message.text.lower()
    user_state[message.chat.id]["trigger"] = trigger
    user_state[message.chat.id]["step"] = "reply"
    bot.send_message(message.chat.id, "💬 Javob yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "reply")
def add_reply(message):
    trigger = user_state[message.chat.id]["trigger"]
    reply = message.text
    rules[trigger] = reply
    save_json(RULES_FILE, rules)
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi:\n{trigger}")

# ===========================
# LIST
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "list" and is_owner(m))
def list_rules(message):
    if not rules:
        bot.send_message(message.chat.id, "📭 Hozircha qoida yo‘q")
        return
    msg = "📋 So‘zlar:\n"
    for k in rules:
        msg += f"- {k}\n"
    bot.send_message(message.chat.id, msg)

# ===========================
# DELETE
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "del" and is_owner(m))
def del_start(message):
    user_state[message.chat.id] = {"step": "delete"}
    bot.send_message(message.chat.id, "❌ Qaysi so‘zni o‘chiramiz?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "delete")
def delete_rule(message):
    key = message.text.lower()
    if key in rules:
        del rules[key]
        save_json(RULES_FILE, rules)
        bot.send_message(message.chat.id, "🗑 O‘chirildi")
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi")
    user_state.pop(message.chat.id)

# ===========================
# JAVOB BERISH (Guruh + Private)
@bot.message_handler(content_types=['text'])
def reply_to_users(message):
    save_user(message)
    text = message.text.lower()

    for trigger, reply in rules.items():
        if trigger in text:
            bot.reply_to(message, reply)
            break

# ===========================
# STATS
@bot.message_handler(func=lambda m: m.text and m.text.lower() == "stats" and is_owner(m))
def show_stats(message):
    total_users = len(users)
    total_messages = sum(u["messages"] for u in users.values())
    bot.send_message(
        message.chat.id,
        f"📊 Statistika:\n"
        f"Foydalanuvchilar: {total_users}\n"
        f"Xabarlar: {total_messages}\n"
        f"So‘zlar: {len(rules)}"
    )

# ===========================
print("Bot ishlayapti...")
bot.infinity_polling()