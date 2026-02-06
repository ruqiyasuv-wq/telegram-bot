import telebot
import json
import os

# ================== TOKEN & ADMIN ==================
TOKEN = "8459082198:AAFtvTHSbToKvyx-6Q1ZcCW0D943TH_Dw4Q"
OWNER_ID = 6736873215

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "data.json"
user_state = {}  # admin buyruqlari uchun holat

# ================== TRANSLITERATION ==================
latin_to_cyr = {
    "a":"а","b":"б","d":"д","e":"е","f":"ф","g":"г","h":"ҳ","i":"и",
    "j":"ж","k":"к","l":"л","m":"м","n":"н","o":"о","p":"п","q":"қ",
    "r":"р","s":"с","t":"т","u":"у","v":"в","x":"х","y":"й","z":"з",
    "sh":"ш","ch":"ч","o'":"ў","g'":"ғ"
}
cyr_to_latin = {v:k for k,v in latin_to_cyr.items()}

def to_cyrillic(text):
    text = text.lower()
    for k,v in latin_to_cyr.items():
        text = text.replace(k,v)
    return text

def to_latin(text):
    text = text.lower()
    for k,v in cyr_to_latin.items():
        text = text.replace(k,v)
    return text

# ================== DATA ==================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE,"r") as f:
            return json.load(f)
    return {"rules": {}, "users": [], "groups": []}

def save_data():
    with open(DATA_FILE,"w") as f:
        json.dump(data,f,indent=4)

data = load_data()

# ================== ADMIN CHECK ==================
def is_owner(message):
    return message.from_user.id == OWNER_ID

# ================== ADD ==================
@bot.message_handler(commands=["add"])
def add_start(message):
    if not is_owner(message):
        return
    user_state[message.chat.id] = {"step":"trigger"}
    bot.send_message(message.chat.id,"📝 So‘z yozing (lotin harflarida):")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="trigger")
def add_trigger(message):
    user_state[message.chat.id]["trigger"] = message.text.lower()
    user_state[message.chat.id]["step"] = "reply"
    bot.send_message(message.chat.id,"💬 Javob yozing:")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="reply")
def add_reply(message):
    trigger = user_state[message.chat.id]["trigger"]
    reply = message.text
    data["rules"][trigger] = reply
    save_data()
    user_state.pop(message.chat.id)
    bot.send_message(message.chat.id,f"✅ Qo‘shildi:\n{trigger}")

# ================== LIST ==================
@bot.message_handler(commands=["list"])
def list_rules(message):
    if not is_owner(message):
        return
    if not data["rules"]:
        bot.send_message(message.chat.id,"📭 Hozircha qoida yo‘q")
        return
    msg = "📋 So‘zlar ro‘yxati:\n"
    for k,v in data["rules"].items():
        msg += f"{k} → Latin: {v} | Kirill: {to_cyrillic(v)}\n"
    bot.send_message(message.chat.id,msg)

# ================== DELETE ==================
@bot.message_handler(commands=["del"])
def del_start(message):
    if not is_owner(message):
        return
    user_state[message.chat.id] = {"step":"delete"}
    bot.send_message(message.chat.id,"❌ Qaysi so‘zni o‘chiramiz?")

@bot.message_handler(func=lambda m: user_state.get(m.chat.id, {}).get("step")=="delete")
def delete_rule(message):
    key = message.text.lower()
    if key in data["rules"]:
        del data["rules"][key]
        save_data()
        bot.send_message(message.chat.id,f"🗑 O‘chirildi: {key}")
    else:
        bot.send_message(message.chat.id,"❌ Bunday so‘z yo‘q")
    user_state.pop(message.chat.id)

# ================== USER REPLY ==================
@bot.message_handler(content_types=['text'])
def user_reply(message):
    uid = message.from_user.id
    chat_id = message.chat.id

    # ID saqlash
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data()
    if message.chat.type in ["group","supergroup"]:
        if chat_id not in data["groups"]:
            data["groups"].append(chat_id)
            save_data()

    text = message.text.lower()
    for trigger, reply in data["rules"].items():
        if trigger in text or to_cyrillic(trigger) in text:
            if any(c in message.text for c in "абвгдежзийклмнопрстуфхцчшщъыьэюя"):
                bot.reply_to(message,to_cyrillic(reply))
            else:
                bot.reply_to(message,reply)
            break

# ================== START ==================
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    if uid not in data["users"]:
        data["users"].append(uid)
        save_data()
        bot.send_message(uid,"Assalomu alaykum! Siz ro‘yxatdan o‘tdingiz ✅")
    else:
        bot.send_message(uid,"Xush kelibsiz! Oldingi sozlamalar saqlangan 🔒")

# ================== BROADCAST TEXT ==================
def broadcast(message_text):
    for uid in data["users"]:
        try:
            bot.send_message(uid,message_text)
        except:
            pass
    for gid in data["groups"]:
        try:
            bot.send_message(gid,message_text)
        except:
            pass

@bot.message_handler(func=lambda m: m.text.startswith("/broadcast "))
def admin_broadcast(msg):
    if not is_owner(msg):
        return
    text = msg.text.replace("/broadcast ","",1)
    broadcast(text)
    bot.send_message(msg.chat.id,"✅ Hamma foydalanuvchilarga va guruhlarga xabar jo‘natildi")

# ================== BROADCAST PHOTO ==================
def broadcast_photo(photo_file, caption_text=""):
    for uid in data["users"]:
        try:
            bot.send_photo(uid,photo_file,caption=caption_text)
        except:
            pass
    for gid in data["groups"]:
        try:
            bot.send_photo(gid,photo_file,caption=caption_text)
        except:
            pass

@bot.message_handler(content_types=['photo'])
def admin_send_photo(msg):
    if not is_owner(msg):
        return
    if msg.caption and msg.caption.startswith("/broadcast "):
        caption_text = msg.caption.replace("/broadcast ","",1)
        file_id = msg.photo[-1].file_id
        broadcast_photo(file_id,caption_text)
        bot.send_message(msg.chat.id,"✅ Hamma foydalanuvchilarga va guruhlarga rasm + xabar jo‘natildi")

# ================== RUN ==================
bot.infinity_polling()@dp.message_handler(commands=['test'])
async def test_cmd(message: types.Message):
    await message.answer("Bot ishlayapti ✅")