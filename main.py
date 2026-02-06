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
# Transliteration
def is_cyrillic(text):
    return any("а" <= c <= "я" or "А" <= c <= "Я" for c in text)

def to_kiril(text):
    mapping = {
        'a':'а','b':'б','d':'д','e':'е','f':'ф','g':'г','h':'х','i':'и',
        'j':'ж','k':'к','l':'л','m':'м','n':'н','o':'о','p':'п','q':'қ',
        'r':'р','s':'с','t':'т','u':'у','v':'в','x':'х','y':'й','z':'з'
    }
    return ''.join([mapping.get(c.lower(), c) for c in text])

def to_latin(text):
    mapping = {
        'а':'a','б':'b','д':'d','е':'e','ф':'f','г':'g','х':'h','и':'i',
        'ж':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','қ':'q',
        'р':'r','с':'s','т':'t','у':'u','в':'v','й':'y','з':'z'
    }
    return ''.join([mapping.get(c.lower(), c) for c in text])

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
    trigger = message.text.lower()
    # Qoida saqlash: triggerning lotin va kiril shakli
    trigger_kiril = to_kiril(trigger)
    trigger_latin = to_latin(trigger)
    user_state[message.chat.id]["trigger"] = {"latin": trigger_latin, "kiril": trigger_kiril}
    user_state[message.chat.id]["step"] = "reply"
    bot.send_message(message.chat.id, "💬 Javob yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "reply")
def add_reply(message):
    triggers = user_state[message.chat.id]["trigger"]
    reply = message.text
    # Har bir trigger uchun qoida saqlaymiz
    rules[triggers["latin"]] = reply
    rules[triggers["kiril"]] = reply
    save_json(RULES_FILE, rules)
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id, f"✅ Qo‘shildi:\n{triggers['latin']} | {triggers['kiril']}")

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
    deleted = False
    for t in [key, to_kiril(key), to_latin(key)]:
        if t in rules:
            del rules[t]
            deleted = True
    save_json(RULES_FILE, rules)
    if deleted:
        bot.send_message(message.chat.id, f"🗑 O‘chirildi: {key}")
    else:
        bot.send_message(message.chat.id, "❌ Bunday so‘z yo‘q")
    user_state.pop(message.chat.id)

# ===========================
# Broadcast / Rasmli va matnli xabar
@bot.message_handler(func=lambda m: m.text.lower() == "broadcast" and is_owner(m))
def broadcast_start(message):
    user_state[message.chat.id] = {"step": "broadcast"}
    bot.send_message(message.chat.id, "📢 Jo‘natiladigan xabar matnini kiriting yoki rasm yuboring:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "broadcast",
                     content_types=['text', 'photo'])
def broadcast_send(message):
    count = 0
    if message.content_type == 'text':
        text = message.text
        for uid in users:
            try:
                bot.send_message(uid, text)
                count += 1
            except Exception as e:
                log(f"Broadcast xato {uid}: {e}")
    elif message.content_type == 'photo':
        file_id = message.photo[-1].file_id
        caption = message.caption or ""
        for uid in users:
            try:
                bot.send_photo(uid, file_id, caption=caption)
                count += 1
            except Exception as e:
                log(f"Broadcast rasm xato {uid}: {e}")
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
            if is_cyrillic(message.text):
                bot.reply_to(message, to_kiril(reply))
            else:
                bot.reply_to(message, to_latin(reply))
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