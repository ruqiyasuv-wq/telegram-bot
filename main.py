import telebot
import json
import os

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215
MIN_SUMMA = 4000

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

PRODUCTS_FILE = "products.json"
USERS_FILE = "users.json"

user_state = {}
carts = {}

def load_json(file, default):
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump(default, f)
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

products = load_json(PRODUCTS_FILE, {})
users = load_json(USERS_FILE, {})

def is_owner(m):
    return m.from_user.id == OWNER_ID

def save_user(uid):
    users[str(uid)] = True
    save_json(USERS_FILE, users)

@bot.message_handler(commands=["start"])
def start(m):
    save_user(m.from_user.id)
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Buyurtma berish")
    bot.send_message(m.chat.id, "Assalomu alaykum! Buyurtma berish uchun tugmani bosing 👇", reply_markup=kb)

# ================= ADMIN: ADD PRODUCT =================
@bot.message_handler(func=lambda m: m.text == "addproduct" and is_owner(m))
def add_product_start(m):
    user_state[m.chat.id] = {"step": "photo"}
    bot.send_message(m.chat.id, "📸 Mahsulot rasmini yuboring")

@bot.message_handler(content_types=["photo"])
def get_photo(m):
    st = user_state.get(m.chat.id)
    if not st or st.get("step") != "photo":
        return
    st["photo"] = m.photo[-1].file_id
    st["step"] = "name"
    bot.send_message(m.chat.id, "📝 Mahsulot nomini yozing")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "name")
def get_name(m):
    user_state[m.chat.id]["name"] = m.text
    user_state[m.chat.id]["step"] = "price"
    bot.send_message(m.chat.id, "💰 Narxini yozing (faqat son)")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "price")
def get_price(m):
    try:
        price = int(m.text)
    except:
        bot.send_message(m.chat.id, "❌ Narx son bo‘lishi kerak")
        return
    st = user_state.pop(m.chat.id)
    products[st["name"]] = {
        "price": price,
        "photo": st["photo"]
    }
    save_json(PRODUCTS_FILE, products)
    bot.send_message(m.chat.id, f"✅ Mahsulot qo‘shildi:\n<b>{st['name']}</b>")

# ================= BUY ORDER =================
@bot.message_handler(func=lambda m: m.text == "🛒 Buyurtma berish")
def order(m):
    if m.chat.type != "private":
        return
    if not products:
        bot.send_message(m.chat.id, "❌ Mahsulotlar yo‘q")
        return
    carts[m.chat.id] = {"product": None, "count": 0}
    show_product(m.chat.id, list(products.keys())[0])

def show_product(chat_id, name):
    prod = products[name]
    cart = carts[chat_id]
    total = cart["count"] * prod["price"]
    cap = (
        f"<b>{name}</b>\n"
        f"Narxi: {prod['price']} so‘m\n"
        f"Tanlangan: {cart['count']} dona\n"
        f"Jami: {total} so‘m"
    )
    kb = telebot.types.InlineKeyboardMarkup()
    kb.row(
        telebot.types.InlineKeyboardButton("➕", callback_data="plus"),
        telebot.types.InlineKeyboardButton("➖", callback_data="minus")
    )
    kb.add(telebot.types.InlineKeyboardButton("🧹 Tozalash", callback_data="clear"))
    kb.add(telebot.types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="done"))
    cart["product"] = name
    bot.send_photo(chat_id, prod["photo"], caption=cap, reply_markup=kb)

@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    cart = carts.get(c.message.chat.id)
    if not cart:
        return
    prod = products[cart["product"]]
    if c.data == "plus":
        cart["count"] += 1
    elif c.data == "minus":
        cart["count"] = max(0, cart["count"] - 1)
    elif c.data == "clear":
        cart["count"] = 0
    elif c.data == "done":
        total = cart["count"] * prod["price"]
        if total < MIN_SUMMA:
            bot.answer_callback_query(c.id, "❌ Buyurtma miqdori kam", show_alert=True)
            return
        user_state[c.message.chat.id] = {"step": "phone"}
        bot.send_message(c.message.chat.id, "📞 Telefon raqamingizni yozing")
        return
    show_product(c.message.chat.id, cart["product"])

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "phone")
def phone(m):
    user_state[m.chat.id]["phone"] = m.text
    user_state[m.chat.id]["step"] = "region"
    bot.send_message(m.chat.id, "📍 Viloyatni yozing")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "region")
def region(m):
    user_state[m.chat.id]["region"] = m.text
    user_state[m.chat.id]["step"] = "address"
    bot.send_message(m.chat.id, "🏠 Manzilni yozing")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step") == "address")
def finish(m):
    st = user_state.pop(m.chat.id)
    cart = carts.pop(m.chat.id)
    prod = products[cart["product"]]
    total = cart["count"] * prod["price"]

    msg = (
        "🆕 <b>Yangi buyurtma</b>\n\n"
        f"📦 Mahsulot: {cart['product']}\n"
        f"🔢 Soni: {cart['count']}\n"
        f"💰 Jami: {total} so‘m\n\n"
        f"📞 Telefon: {st['phone']}\n"
        f"📍 Manzil: {st['region']} – {m.text}"
    )
    bot.send_message(OWNER_ID, msg)
    bot.send_message(m.chat.id, "✅ Buyurtmangiz qabul qilindi. Rahmat!")

bot.infinity_polling()