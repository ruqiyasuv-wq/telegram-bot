import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
ADMIN_ID = 6736873215

DATA_FILE = "data.json"
IMAGE_FILE_ID = None  # bitta rasm file_id sini keyin admin yuboradi

bot = telebot.TeleBot(TOKEN)

# -------------------- SAQLASH --------------------
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {
        "products": {},
        "users": [],
        "min_sum": 50000
    }

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# -------------------- YORDAMCHI --------------------
def is_admin(uid):
    return uid == ADMIN_ID

def add_user(uid):
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data()

# -------------------- START --------------------
@bot.message_handler(commands=["start"])
def start(msg):
    if msg.chat.type != "private":
        return
    add_user(msg.from_user.id)

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🛒 Buyurtma berish", callback_data="order"))

    bot.send_message(
        msg.chat.id,
        "Assalomu alaykum!\nBuyurtma berish uchun tugmani bosing 👇",
        reply_markup=kb
    )

# -------------------- ADMIN: MIN SUMMA --------------------
@bot.message_handler(commands=["minsum"])
def set_min_sum(msg):
    if not is_admin(msg.from_user.id):
        return
    try:
        data["min_sum"] = int(msg.text.split()[1])
        save_data()
        bot.reply_to(msg, f"✅ Minimal summa: {data['min_sum']} so‘m")
    except:
        bot.reply_to(msg, "❌ Misol: /minsum 50000")

# -------------------- ADMIN: RASM --------------------
@bot.message_handler(content_types=["photo"])
def set_image(msg):
    global IMAGE_FILE_ID
    if not is_admin(msg.from_user.id):
        return
    IMAGE_FILE_ID = msg.photo[-1].file_id
    bot.reply_to(msg, "✅ Buyurtma uchun rasm saqlandi")

# -------------------- ADMIN: ADD PRODUCT --------------------
@bot.message_handler(commands=["add"])
def add_product(msg):
    if not is_admin(msg.from_user.id):
        return
    bot.reply_to(msg, "📝 Mahsulot nomini yozing:")
    bot.register_next_step_handler(msg, add_product_name)

def add_product_name(msg):
    name = msg.text
    bot.send_message(msg.chat.id, "💰 Narxini yozing:")
    bot.register_next_step_handler(msg, add_product_price, name)

def add_product_price(msg, name):
    try:
        price = int(msg.text)
        data["products"][name] = price
        save_data()
        bot.send_message(msg.chat.id, f"✅ Qo‘shildi:\n{name} — {price} so‘m")
    except:
        bot.send_message(msg.chat.id, "❌ Narx faqat son bo‘lsin")

# -------------------- ADMIN: DELETE PRODUCT --------------------
@bot.message_handler(commands=["del"])
def delete_product(msg):
    if not is_admin(msg.from_user.id):
        return

    kb = InlineKeyboardMarkup()
    for name in data["products"]:
        kb.add(InlineKeyboardButton(name, callback_data=f"del:{name}"))

    bot.send_message(msg.chat.id, "🗑 O‘chirish uchun tanlang:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("del:"))
def del_prod(c):
    name = c.data.split(":")[1]
    if name in data["products"]:
        del data["products"][name]
        save_data()
        bot.answer_callback_query(c.id, "❌ O‘chirildi")
        bot.edit_message_text("✅ Mahsulot o‘chirildi", c.message.chat.id, c.message.message_id)

# -------------------- BUYURTMA --------------------
user_cart = {}

@bot.callback_query_handler(func=lambda c: c.data == "order")
def order_menu(c):
    uid = c.from_user.id
    user_cart[uid] = {}

    kb = InlineKeyboardMarkup(row_width=1)
    for name in data["products"]:
        kb.add(InlineKeyboardButton(name, callback_data=f"add:{name}"))

    kb.add(
        InlineKeyboardButton("🧹 Tozalash", callback_data="clear"),
        InlineKeyboardButton("✅ Buyurtma berish", callback_data="confirm")
    )

    caption = "🛒 Mahsulotni tanlang (bosgan sari ko‘payadi):"
    if IMAGE_FILE_ID:
        bot.send_photo(c.message.chat.id, IMAGE_FILE_ID, caption=caption, reply_markup=kb)
    else:
        bot.send_message(c.message.chat.id, caption, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("add:"))
def add_to_cart(c):
    uid = c.from_user.id
    name = c.data.split(":")[1]
    user_cart.setdefault(uid, {})
    user_cart[uid][name] = user_cart[uid].get(name, 0) + 1
    bot.answer_callback_query(c.id, f"{name}: {user_cart[uid][name]} ta")

@bot.callback_query_handler(func=lambda c: c.data == "clear")
def clear_cart(c):
    user_cart[c.from_user.id] = {}
    bot.answer_callback_query(c.id, "🧹 Tozalandi")

@bot.callback_query_handler(func=lambda c: c.data == "confirm")
def confirm_order(c):
    uid = c.from_user.id
    cart = user_cart.get(uid, {})

    total = sum(data["products"][n] * q for n, q in cart.items())
    if total < data["min_sum"]:
        bot.answer_callback_query(
            c.id,
            f"❌ Buyurtma kam\nMinimal: {data['min_sum']} so‘m",
            show_alert=True
        )
        return

    text = "📦 YANGI BUYURTMA:\n\n"
    for n, q in cart.items():
        text += f"{n} x {q} = {data['products'][n]*q} so‘m\n"
    text += f"\n💰 Jami: {total} so‘m\n👤 ID: {uid}"

    bot.send_message(ADMIN_ID, text)
    bot.edit_message_text("✅ Buyurtma yuborildi. Rahmat!", c.message.chat.id, c.message.message_id)

# -------------------- RUN --------------------
bot.infinity_polling()