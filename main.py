import telebot
from telebot import types
import json
import os

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215
MIN_SUMMA = 20000  # minimal summa

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

PRODUCTS_FILE = "products.json"
USERS_FILE = "users.json"

# User state va carts
user_state = {}
carts = {}

# JSON load/save
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

# ================= START =================
@bot.message_handler(commands=["start"])
def start(m):
    save_user(m.from_user.id)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🛒 Buyurtma berish")
    bot.send_message(m.chat.id, "Assalomu alaykum! Buyurtma berish uchun tugmani bosing 👇", reply_markup=kb)

# ================= ADMIN ADD PRODUCT =================
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
    carts[m.chat.id] = {name:0 for name in products.keys()}
    # Bitta rasm tagida barcha mahsulot
    first_prod = list(products.keys())[0]
    show_cart(m.chat.id, products[first_prod]["photo"])

def show_cart(chat_id, photo_id):
    cart = carts[chat_id]
    caption = "🛒 Buyurtma\n\n"
    total = 0
    for name, count in cart.items():
        price = products[name]["price"]
        subtotal = price * count
        total += subtotal
        caption += f"{name} — {count} dona\n"
    caption += f"\nJami: {total} so‘m"

    kb = types.InlineKeyboardMarkup()
    # Har bir mahsulot uchun +/-
    row = []
    for name in cart.keys():
        kb.row(
            types.InlineKeyboardButton(f"➕ {name}", callback_data=f"plus|{name}"),
            types.InlineKeyboardButton(f"➖ {name}", callback_data=f"minus|{name}")
        )
    kb.add(types.InlineKeyboardButton("🧹 Tozalash", callback_data="clear"))
    kb.add(types.InlineKeyboardButton("✅ Buyurtma berish", callback_data="done"))

    # Agar xabar oldin bor bo'lsa edit qiling, yo'q bo'lsa send
    if "msg_id" in carts[chat_id]:
        try:
            bot.edit_message_caption(caption, chat_id, carts[chat_id]["msg_id"], reply_markup=kb)
        except:
            m = bot.send_photo(chat_id, photo_id, caption=caption, reply_markup=kb)
            carts[chat_id]["msg_id"] = m.message_id
    else:
        m = bot.send_photo(chat_id, photo_id, caption=caption, reply_markup=kb)
        carts[chat_id]["msg_id"] = m.message_id

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda c: True)
def callbacks(c):
    chat_id = c.message.chat.id
    if chat_id not in carts:
        return
    cart = carts[chat_id]
    if c.data.startswith("plus|"):
        name = c.data.split("|")[1]
        cart[name] += 1
    elif c.data.startswith("minus|"):
        name = c.data.split("|")[1]
        cart[name] = max(0, cart[name]-1)
    elif c.data == "clear":
        for k in cart.keys():
            cart[k]=0
    elif c.data == "done":
        total = sum(products[name]["price"]*count for name,count in cart.items())
        if total < MIN_SUMMA:
            bot.answer_callback_query(c.id, "❌ Buyurtma miqdori kam", show_alert=True)
            return
        user_state[chat_id] = {"step":"phone"}
        bot.send_message(chat_id, "📞 Telefon raqamingizni yozing (to‘liq 998901234567)")
        return
    first_prod = list(products.keys())[0]
    show_cart(chat_id, products[first_prod]["photo"])
    bot.answer_callback_query(c.id)

# ================= PHONE / REGION / ADDRESS =================
@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="phone")
def get_phone(m):
    if not m.text.isdigit() or len(m.text)!=12 or not m.text.startswith("998"):
        bot.send_message(m.chat.id, "❌ Telefon raqam noto‘g‘ri. Misol: 998901234567")
        return
    user_state[m.chat.id]["phone"]=m.text
    user_state[m.chat.id]["step"]="region"
    bot.send_message(m.chat.id, "📍 Viloyatni yozing")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="region")
def get_region(m):
    user_state[m.chat.id]["region"]=m.text
    user_state[m.chat.id]["step"]="address"
    bot.send_message(m.chat.id, "🏠 Manzilni yozing")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="address")
def get_address(m):
    chat_id = m.chat.id
    st = user_state.pop(chat_id)
    cart = carts.pop(chat_id)
    total = sum(products[name]["price"]*count for name,count in cart.items())
    msg = "🆕 <b>Yangi buyurtma</b>\n\n"
    for name,count in cart.items():
        if count>0:
            subtotal = products[name]["price"]*count
            msg += f"{name} — {count} dona → {subtotal} so‘m\n"
    msg += f"\n📞 Telefon: {st['phone']}\n📍 Manzil: {st['region']} – {m.text}\n"
    msg += f"\nJami: {total} so‘m"
    bot.send_message(OWNER_ID, msg)
    bot.send_message(chat_id, "✅ Buyurtmangiz qabul qilindi. Rahmat!")

bot.infinity_polling()