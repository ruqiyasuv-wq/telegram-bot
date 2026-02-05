import telebot
from telebot import types
import json
import os
from datetime import datetime
import re
from rapidfuzz import process

# ===========================
# CONFIG
TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215
RULES_FILE = "rules.json"
USERS_FILE = "users.json"
PRODUCTS_FILE = "products.json"
LOG_FILE = "bot.log"
MIN_ORDER_SUM = 4000  # minimal summa belgilash
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

rules = load_json(RULES_FILE, {})
users = load_json(USERS_FILE, {})
products = load_json(PRODUCTS_FILE, {
    "Suv 5L": {"price": 4000, "image": ""},
    "Suv 10L": {"price": 7000, "image": ""}
})

user_state = {}

# Logging
def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {msg}\n")

# ===========================
def is_owner(message):
    return message.from_user.id == OWNER_ID

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
# Admin Qoida boshqaruvi
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

@bot.message_handler(func=lambda m: m.text.lower() == "list" and is_owner(m))
def list_rules(message):
    if not rules:
        bot.send_message(message.chat.id, "📭 Hozircha qoida yo‘q")
        return
    msg = "📋 So‘zlar ro‘yxati:\n"
    for k in rules:
        msg += f"- {k}\n"
    bot.send_message(message.chat.id, msg)

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
# Broadcast
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
# Statistika
@bot.message_handler(func=lambda m: m.text.lower() == "stats" and is_owner(m))
def show_stats(message):
    total_users = len(users)
    total_messages = sum(u["messages"] for u in users.values())
    msg = f"📊 Statistika:\n- Foydalanuvchilar: {total_users}\n- Umumiy xabarlar: {total_messages}\n- Triggers: {len(rules)}"
    bot.send_message(message.chat.id, msg)

# ===========================
# Zakaz / Mahsulotlar (inline button)
@bot.message_handler(func=lambda m: m.text.lower() == "buyurtma berish")
def start_order(message):
    save_user(message)
    markup = types.InlineKeyboardMarkup()
    for product, info in products.items():
        button_text = f"{product} - {info['price']} so'm"
        markup.add(types.InlineKeyboardButton(button_text, callback_data=f"buy_{product}"))
    bot.send_message(message.chat.id, "🛒 Mahsulotni tanlang:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_order(call):
    product = call.data[4:]
    user_state[call.message.chat.id] = {"step": "quantity", "product": product}
    bot.send_message(call.message.chat.id, f"📦 {product} tanlandi.\nNechta buyurtma qilmoqchisiz?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "quantity")
def ask_quantity(message):
    try:
        quantity = int(message.text)
        product = user_state[message.chat.id]["product"]
        total = quantity * products[product]["price"]
        if total < MIN_ORDER_SUM:
            bot.send_message(message.chat.id, f"❌ Sizning buyurtmangiz miqdori kam! Minimal summa {MIN_ORDER_SUM} so‘m")
            return
        user_state[message.chat.id]["quantity"] = quantity
        user_state[message.chat.id]["step"] = "phone"
        bot.send_message(message.chat.id, "📞 Telefon raqamingizni kiriting:")
    except:
        bot.send_message(message.chat.id, "❌ Iltimos, son kiriting.")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "phone")
def ask_location(message):
    user_state[message.chat.id]["phone"] = message.text
    user_state[message.chat.id]["step"] = "location"
    bot.send_message(message.chat.id, "📍 Qaysi viloyat va qaysi manzilga yetkazilsin?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "location")
def finish_order(message):
    data = user_state[message.chat.id]
    product = data["product"]
    quantity = data["quantity"]
    phone = data["phone"]
    location = message.text
    # Adminga xabar
    order_msg = (
        f"✅ Yangi zakaz!\n"
        f"Foydalanuvchi: @{message.from_user.username}\n"
        f"Mahsulot: {product}\n"
        f"Soni: {quantity}\n"
        f"Telefon: {phone}\n"
        f"Manzil: {location}"
    )
    bot.send_message(OWNER_ID, order_msg)
    bot.send_message(message.chat.id, "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz.")
    user_state.pop(message.chat.id)

# ===========================
# Guruh va shaxsiy chat javob
@bot.message_handler(content_types=['text'])
def handle_text(message):
    save_user(message)
    text = message.text.lower()
    for trigger, reply in rules.items():
        if re.search(trigger, text, re.IGNORECASE):
            bot.reply_to(message, reply)
            break
        else:
            match, score = process.extractOne(text, [trigger])
            if score > 80:
                bot.reply_to(message, reply)
                break

# ===========================
bot.infinity_polling()