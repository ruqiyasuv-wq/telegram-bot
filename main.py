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
# Load / Save JSON
def load_json(file, default):
    if os.path.exists(file):
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
# ===========================

# Rules va foydalanuvchilar
rules = load_json(RULES_FILE, {})
users = load_json(USERS_FILE, {})

# Logging
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {msg}\n")

# ===========================
# Admin tekshirish
def is_owner(message):
    return message.from_user.id == OWNER_ID

# ===========================
# Foydalanuvchi ID saqlash
def save_user(message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {
            "username": message.from_user.username or "",
            "first_name": message.from_user.first_name or "",
            "last_name": message.from_user.last_name or "",
            "messages": 0
        }
    users[user_id]["messages"] += 1
    save_json(USERS_FILE, users)

# ===========================
# Qoida qo‘shish
user_state = {}

@bot.message_handler(func=lambda m: m.text.lower() == "add" and is_owner(m))
def add_start(message):
    user_state[message.chat.id] = {"step": "trigger"}
    bot.send_message(message.chat.id, "📝 So‘z yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "trigger")
def add_trigger(message):
    user_state[message.chat.id]["trigger"] = message.text.lower()
    user_state[message.chat.id]["step"] = "reply"
    bot.send_message(message.chat.id, "💬 Javob yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "reply")
def add_reply(message):
    trigger = user_state[message.chat.id]["trigger"]
    rules[trigger] = message.text
    save_json(RULES_FILE, rules)
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi:\n{trigger}")

# ===========================
# Qoida ro‘yxati
@bot.message_handler(func=lambda m: m.text.lower() == "list" and is_owner(m))
def list_rules(message):
    if not rules:
        bot.send_message(message.chat.id, "📭 Hozircha qoida yo‘q")
        return
    msg = "📋 So‘zlar ro‘yxati:\n"
    for k in rules:
        msg += f"- {k}\n"
    bot.send_message(message.chat.id, msg)

# ===========================
# Qoida o‘chirish
@bot.message_handler(func=lambda m: m.text.lower() == "del" and is_owner(m))
def del_start(message):
    user_state[message.chat.id] = {"step": "delete"}
    bot.send_message(message.chat.id, "❌ Qaysi so‘zni o‘chiramiz?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "delete")
def delete_rule(message):
    key = message.text.lower()
    if key in rules:
        del rules[key]
        save_json(RULES_FILE, rules)
        bot.send_message(message.chat.id, f"🗑 O‘chirildi: {key}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday so‘z yo‘q")
    user_state.pop(message.chat.id)

# ===========================
# Broadcast / Habar jo‘natish
@bot.message_handler(func=lambda m: m.text.lower() == "broadcast" and is_owner(m))
def broadcast_start(message):
    user_state[message.chat.id] = {"step": "broadcast"}
    bot.send_message(message.chat.id, "📢 Jo‘natiladigan xabar matnini kiriting:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "broadcast")
def broadcast_send(message):
    text = message.text
    count = 0
    for uid in users:
        try:
            bot.send_message(uid, text)
            count += 1
        except Exception as e:
            log(f"Broadcast xato {uid}: {e}")
    bot.send_message(message.chat.id, f"✅ Xabar {count} foydalanuvchiga yuborildi")
    user_state.pop(message.chat.id)

# ===========================
# Guruh va shaxsiy chatda javob
@bot.message_handler(content_types=['text'])
def group_reply(message):
    save_user(message)
    text = message.text.lower()
    for trigger, reply in rules.items():
        if trigger in text:
            bot.reply_to(message, reply)
            break

# ===========================
# Statistikalar
@bot.message_handler(func=lambda m: m.text.lower() == "stats" and is_owner(m))
def show_stats(message):
    total_users = len(users)
    total_messages = sum(u["messages"] for u in users.values())
    msg = f"📊 Statistika:\n- Foydalanuvchilar: {total_users}\n- Umumiy xabarlar: {total_messages}\n- Triggers: {len(rules)}"
    bot.send_message(message.chat.id, msg)

# ===========================
# Ishga tushurish
bot.infinity_polling()