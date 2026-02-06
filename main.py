import telebot
import json
import os
from datetime import datetime

TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215
RULES_FILE = "rules.json"
USERS_FILE = "users.json"
PRODUCTS_FILE = "products.json"

bot = telebot.TeleBot(TOKEN)

# ===========================
# Load / Save
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
products = load_json(PRODUCTS_FILE, {})

user_state = {}  # Admin va foydalanuvchi holatlari

# ===========================
# Transliteration
def is_cyrillic(text):
    return any("а" <= c <= "я" or "А" <= c <= "Я" for c in text)

def to_kiril(text):
    mapping = {'a':'а','b':'б','d':'д','e':'е','f':'ф','g':'г','h':'х','i':'и',
               'j':'ж','k':'к','l':'л','m':'м','n':'н','o':'о','p':'п','q':'қ',
               'r':'р','s':'с','t':'т','u':'у','v':'в','x':'х','y':'й','z':'з'}
    return ''.join([mapping.get(c.lower(), c) for c in text])

def to_latin(text):
    mapping = {'а':'a','б':'b','д':'d','е':'e','ф':'f','г':'g','х':'h','и':'i',
               'ж':'j','к':'k','л':'l','м':'m','н':'n','о':'o','п':'p','қ':'q',
               'р':'r','с':'s','т':'t','у':'u','в':'v','й':'y','з':'z'}
    return ''.join([mapping.get(c.lower(), c) for c in text])

# ===========================
# Admin tekshirish
def is_owner(message):
    return message.from_user.id == OWNER_ID

# ===========================
# Foydalanuvchi ID saqlash
def save_user(message):
    uid = str(message.from_user.id)
    if uid not in users:
        users[uid] = {"username": message.from_user.username or "", "messages":0}
    users[uid]["messages"] += 1
    save_json(USERS_FILE, users)

# ===========================
# Admin Qoida: add / del / list
# (shu yerga oldingi rules qo‘shish kodi transliteration bilan)

# ===========================
# Admin mahsulot qo‘shish / o‘chirish
# products = { "suv": {"narx":10000} }
# Foydalanuvchi buyurtma beradi, soni kiritadi, natija adminga keladi

# ===========================
# Foydalanuvchi xabar handler
# 1️⃣ Foydalanuvchi rules ga mos so‘z yozsa javob beradi
# 2️⃣ Agar buyurtma berish bosilsa → step by step: soni, nomer, viloyat, manzil
# 3️⃣ Minimal summa tekshiriladi
# 4️⃣ Buyurtma adminga jo‘natiladi

# ===========================
# Ishga tushurish
bot.infinity_polling()